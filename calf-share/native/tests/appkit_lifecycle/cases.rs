//! Real AppKit owners and production registry/dispatch/cleanup. Terminal service inputs are
//! deliberately controlled Objective-C messages, NOT user delivery or an external recipient.
use super::*;
use crate::{begin_share, cancel_share};
use objc2::rc::Weak;
use objc2::MainThreadOnly;
use objc2_app_kit::{NSApplicationActivationPolicy, NSBackingStoreType, NSWindowStyleMask};
use objc2_foundation::{NSDate, NSDefaultRunLoopMode, NSRunLoop};
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::sync::atomic::{AtomicBool, Ordering as AtomicOrdering};
use std::time::{Duration, Instant};

const SUBJECT: &str = "NativeCmpKit controlled AppKit lifecycle subject; no recipient is opened";
static CONTROL_FAILED: AtomicBool = AtomicBool::new(false);
const FINITE: &[(&str, fn())] = &[
    ("cancel_before_dispatch", cancel_before_dispatch),
    ("no_key_window", no_key_window),
    ("missing_content_view", missing_content_view),
    ("real_picker_cancel", real_picker_cancel),
    ("controlled_picker_dismissal", controlled_picker_dismissal),
    (
        "controlled_success_duplicate_late",
        controlled_success_duplicate_late,
    ),
    ("controlled_service_failure", controlled_service_failure),
    ("bounded_concurrent_requests", bounded_concurrent_requests),
];

struct Witness {
    delegate: Weak<AnyObject>,
    completion: std::sync::Weak<Completion>,
}
thread_local! {
    static OWNED_IDS: RefCell<Vec<i64>> = const { RefCell::new(Vec::new()) };
    static WITNESSES: RefCell<Vec<Witness>> = const { RefCell::new(Vec::new()) };
    // Only the controlled late-message case adds this intentional extra reference.
    static LATE_DELEGATE: RefCell<Option<Retained<AnyObject>>> = const { RefCell::new(None) };
    static HELD_SERVICE: RefCell<Option<Retained<NSSharingService>>> = const { RefCell::new(None) };
    static TEST_WINDOW: RefCell<Option<Retained<NSWindow>>> = const { RefCell::new(None) };
}

fn data() -> ShareData {
    ShareData {
        text: Some("NativeCmpKit lifecycle verification; disposable process only".into()),
        url: None,
        paths: Vec::new(),
        subject: Some(SUBJECT.into()),
    }
}

fn begin() -> i64 {
    let id = begin_share(data(), 0);
    assert!(id > 0, "The actual native operation must be admitted");
    OWNED_IDS.with(|ids| ids.borrow_mut().push(id));
    id
}

fn pump_until(reason: &str, mut condition: impl FnMut() -> bool) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while !condition() {
        assert!(Instant::now() < deadline, "{reason}");
        autoreleasepool(|_| {
            NSRunLoop::mainRunLoop().runMode_beforeDate(
                unsafe { NSDefaultRunLoopMode },
                &NSDate::dateWithTimeIntervalSinceNow(0.005),
            );
        });
    }
}

fn drain_main() {
    let reached = Arc::new(AtomicBool::new(false));
    let marker = reached.clone();
    dispatch_main(0, move || marker.store(true, AtomicOrdering::Release));
    pump_until("Queued Main cleanup did not complete", || {
        reached.load(AtomicOrdering::Acquire)
    });
}

fn dispatch_control(id: i64, action: impl FnOnce() + Send + 'static) {
    dispatch_main(id, move || {
        if let Err(error) = catch_unwind(AssertUnwindSafe(action)) {
            // Production catches dispatched Rust panics. Keep an independent failed-control
            // witness so cleanup/result consumption cannot turn a native assertion into green.
            CONTROL_FAILED.store(true, AtomicOrdering::Release);
            std::panic::resume_unwind(error);
        }
    });
}

fn assert_released() {
    drain_main();
    pump_until(
        "An actual Objective-C delegate or Rust completion still has a strong owner",
        || {
            WITNESSES.with(|witnesses| {
                witnesses
                    .borrow()
                    .iter()
                    .all(|w| w.delegate.load().is_none() && w.completion.upgrade().is_none())
            })
        },
    );
    assert_eq!(0, live_count(), "Main-owned picker table is not empty");
    assert_eq!(0, registry().len(), "Native registry references remain");
}

fn capture_witness(id: i64) {
    assert!(MainThreadMarker::new().is_some());
    UI_OPERATIONS.with(|operations| {
        let operations = operations.borrow();
        let operation = operations.get(&id).expect("The real picker must exist");
        assert!(
            operation.picker.delegate().is_some(),
            "Production delegate was not installed"
        );
        WITNESSES.with(|witnesses| {
            witnesses.borrow_mut().push(Witness {
                delegate: Weak::from_retained(&operation.delegate),
                completion: Arc::downgrade(&operation._completion),
            })
        });
    });
}

/// Observe only the atomic live count off Main. The returned task dereferences AppKit owners
/// on Main exclusively. An outer process timeout remains required if a native call stalls.
fn when_live(id: i64, action: fn(i64)) -> std::thread::JoinHandle<()> {
    std::thread::spawn(move || {
        let deadline = Instant::now() + Duration::from_secs(10);
        while live_count() != 1 {
            assert!(
                Instant::now() < deadline,
                "Actual native picker never became live"
            );
            std::thread::sleep(Duration::from_millis(2));
        }
        dispatch_control(id, move || {
            capture_witness(id);
            action(id);
        });
    })
}

fn wait_result(id: i64, expected: i32) {
    let mut actual = super::super::operation::PENDING;
    pump_until("Native operation never became terminal", || {
        actual = registry().take(id);
        actual != super::super::operation::PENDING
    });
    assert_eq!(expected, actual);
    assert_eq!(
        UNAVAILABLE,
        registry().take(id),
        "A consumed result cannot be delivered twice"
    );
}

fn with_window(body: impl FnOnce(&NSWindow)) {
    let main = MainThreadMarker::new().expect("Actual process Main is required");
    let window = unsafe {
        NSWindow::initWithContentRect_styleMask_backing_defer(
            NSWindow::alloc(main),
            NSRect::new(NSPoint::new(120.0, 120.0), NSSize::new(360.0, 160.0)),
            NSWindowStyleMask::Titled | NSWindowStyleMask::Closable,
            NSBackingStoreType::Buffered,
            false,
        )
    };
    unsafe { window.setReleasedWhenClosed(false) };
    window.setTitle(&NSString::from_str(
        "NativeCmpKit disposable share lifecycle test",
    ));
    window.makeKeyAndOrderFront(None);
    TEST_WINDOW.with(|owned| *owned.borrow_mut() = Some(window.clone()));
    pump_until("Owned AppKit window did not become key", || {
        window.isKeyWindow()
    });
    body(&window);
    window.orderOut(None);
    window.close();
    TEST_WINDOW.with(|owned| owned.borrow_mut().take());
    drain_main();
}

fn cancel_before_dispatch() {
    let id = begin();
    assert_eq!(1, registry().len());
    assert_eq!(0, live_count()); // No Main run-loop service occurred between begin/cancel.
    cancel_share(id);
    assert_eq!(0, registry().len());
    assert_eq!(
        -1,
        begin_share(data(), 0),
        "Cancellation must retain admission until Main acknowledges cleanup"
    );
    drain_main();
    assert_released();
}

fn no_key_window() {
    let main = MainThreadMarker::new().unwrap();
    assert!(NSApplication::sharedApplication(main).keyWindow().is_none());
    let id = begin();
    wait_result(id, UNAVAILABLE);
    assert_released();
}

fn missing_content_view() {
    with_window(|window| {
        let original = window
            .contentView()
            .expect("Owned window needs its original content view");
        window.setContentView(None);
        assert!(
            window.contentView().is_none(),
            "The real nil-content-view precondition did not hold"
        );
        let id = begin();
        wait_result(id, UNAVAILABLE);
        window.setContentView(Some(&original));
        assert_released();
    });
}

fn real_picker_cancel() {
    with_window(|_| {
        for _ in 0..4 {
            let id = begin();
            let observer = when_live(id, |id| {
                assert_eq!(
                    -1,
                    begin_share(data(), 0),
                    "Live native UI must remain single-flight"
                );
                cancel_share(id);
            });
            pump_until(
                "Actual picker cancellation did not release Main ownership",
                || live_count() == 0 && registry().len() == 0,
            );
            observer.join().expect("Native observer failed");
            assert_released();
            cancel_share(id); // Duplicate cleanup schedules no second owner release.
            drain_main();
            assert_released();
        }
    });
}

fn controlled_success_duplicate_late() {
    with_window(|_| {
        let old = begin();
        let observer = when_live(old, |id| {
            let delegate =
                UI_OPERATIONS.with(|operations| operations.borrow()[&id].delegate.clone());
            LATE_DELEGATE.with(|held| *held.borrow_mut() = Some(delegate.clone()));
            let _: () = unsafe {
                msg_send![&*delegate, sharingService: std::ptr::null::<AnyObject>(), didShareItems: std::ptr::null::<AnyObject>()]
            };
            let _: () = unsafe {
                msg_send![&*delegate, sharingService: std::ptr::null::<AnyObject>(), didFailToShareItems: std::ptr::null::<AnyObject>(), error: std::ptr::null::<AnyObject>()]
            };
        });
        wait_result(old, SUCCESS);
        observer.join().expect("Native observer failed");
        drain_main();
        assert_eq!(0, live_count());

        let new = begin();
        let observer = when_live(new, |id| {
            LATE_DELEGATE.with(|held| {
                let held = held.borrow();
                let delegate = held.as_ref().expect("Controlled late receiver must be safely retained");
                let _: () = unsafe { msg_send![&**delegate, sharingServicePicker: std::ptr::null::<AnyObject>(), didChooseSharingService: std::ptr::null::<AnyObject>()] };
                let _: () = unsafe { msg_send![&**delegate, sharingService: std::ptr::null::<AnyObject>(), didShareItems: std::ptr::null::<AnyObject>()] };
            });
            // FIFO: verify old cleanup tasks have run before cancelling the new operation.
            dispatch_control(id, move || {
                assert_eq!(
                    1,
                    live_count(),
                    "Late old callback removed the new actual picker"
                );
                assert_eq!(
                    -1,
                    begin_share(data(), 0),
                    "Late old callback reopened native admission"
                );
                LATE_DELEGATE.with(|held| held.borrow_mut().take());
                cancel_share(id);
            });
        });
        pump_until("Late-callback case did not clean its replacement", || {
            live_count() == 0 && registry().len() == 0
        });
        observer.join().expect("Native observer failed");
        assert_released();
    });
}

fn controlled_picker_dismissal() {
    with_window(|_| {
        let id = begin();
        let observer = when_live(id, |id| {
            let delegate =
                UI_OPERATIONS.with(|operations| operations.borrow()[&id].delegate.clone());
            let _: () = unsafe {
                msg_send![&*delegate, sharingServicePicker: std::ptr::null::<AnyObject>(), didChooseSharingService: std::ptr::null::<AnyObject>()]
            };
        });
        wait_result(id, DISMISSED);
        observer.join().expect("Native observer failed");
        assert_released();
    });
}

fn controlled_service_failure() {
    with_window(|_| {
        let id = begin();
        let observer = when_live(id, |id| {
            // A real OS service object is retained, but never performWithItems/opened. This
            // verifies the real delegate/subject contract, not Mail installation or delivery.
            let service = unsafe {
                NSSharingService::sharingServiceNamed(
                    objc2_app_kit::NSSharingServiceNameComposeEmail,
                )
            }
            .expect("The real native Mail service object is unavailable");
            let (delegate, picker) = UI_OPERATIONS.with(|operations| {
                let operations = operations.borrow();
                (
                    operations[&id].delegate.clone(),
                    operations[&id].picker.clone(),
                )
            });
            let returned: *const AnyObject = unsafe {
                msg_send![&*delegate, sharingServicePicker: &*picker, delegateForSharingService: &*service]
            };
            assert_eq!(Retained::as_ptr(&delegate), returned);
            assert_eq!(
                SUBJECT,
                service
                    .subject()
                    .expect("Subject was discarded")
                    .to_string()
            );
            let _: () = unsafe { msg_send![&*service, setDelegate: &*delegate] };
            HELD_SERVICE.with(|held| *held.borrow_mut() = Some(service.clone()));
            let _: () = unsafe {
                msg_send![&*delegate, sharingService: &*service, didFailToShareItems: std::ptr::null::<AnyObject>(), error: std::ptr::null::<AnyObject>()]
            };
            // Deliberate controlled native receiver kept alive for post-cleanup weak-property
            // readback, not an assertion that the service itself is globally deallocated.
            dispatch_control(id, move || {
                HELD_SERVICE.with(|held| {
                    let service = held
                        .borrow_mut()
                        .take()
                        .expect("Controlled service readback owner is missing");
                    assert!(
                        service
                            .delegate(
                                MainThreadMarker::new()
                                    .expect("Native service readback needs Main")
                            )
                            .is_none(),
                        "Selected service still holds its native delegate"
                    );
                });
            });
        });
        wait_result(id, FAILED);
        observer.join().expect("Native observer failed");
        assert_released();
    });
}

fn bounded_concurrent_requests() {
    with_window(|_| {
        let workers: Vec<_> = (0..8)
            .map(|_| std::thread::spawn(|| begin_share(data(), 0)))
            .collect();
        let outcomes: Vec<_> = workers
            .into_iter()
            .map(|worker| worker.join().unwrap())
            .collect();
        assert_eq!(1, outcomes.iter().filter(|id| **id > 0).count());
        assert_eq!(7, outcomes.iter().filter(|id| **id == -1).count());
        let id = *outcomes.iter().find(|id| **id > 0).unwrap();
        OWNED_IDS.with(|ids| ids.borrow_mut().push(id));
        let observer = when_live(id, cancel_share);
        pump_until("Concurrent native owner did not clean up", || {
            live_count() == 0 && registry().len() == 0
        });
        observer.join().expect("Native observer failed");
        assert_released();
    });
}

fn stress_2048() {
    with_window(|_| {
        for _ in 0..2048 {
            let id = begin();
            let observer = when_live(id, cancel_share);
            pump_until("Real stress cancellation did not finish", || {
                live_count() == 0 && registry().len() == 0
            });
            observer.join().expect("Native observer failed");
            assert_released();
            // Already checked weak witnesses are not accumulated as test-owned allocation growth.
            WITNESSES.with(|witnesses| witnesses.borrow_mut().clear());
            OWNED_IDS.with(|ids| ids.borrow_mut().clear());
        }
    });
}

fn cleanup_owned() {
    LATE_DELEGATE.with(|held| held.borrow_mut().take());
    OWNED_IDS.with(|ids| {
        for id in ids.borrow().iter() {
            cancel_share(*id);
        }
    });
    drain_main();
    HELD_SERVICE.with(|held| held.borrow_mut().take());
    TEST_WINDOW.with(|owned| {
        if let Some(window) = owned.borrow_mut().take() {
            window.orderOut(None);
            window.close();
        }
    });
    assert_released();
    OWNED_IDS.with(|ids| ids.borrow_mut().clear());
    WITNESSES.with(|witnesses| witnesses.borrow_mut().clear());
}

pub(crate) fn run() {
    assert_eq!(
        Ok("true".into()),
        std::env::var("NATIVECMPKIT_NATIVE_UI_TESTS"),
        "Native GUI opt-in is required; no skip/pass fallback"
    );
    let main =
        MainThreadMarker::new().expect("This native harness must run on actual process Main");
    assert!(
        is_supported(),
        "This AppKit does not expose cancellable native sharing"
    );
    let app = NSApplication::sharedApplication(main);
    assert!(
        app.windows().is_empty(),
        "The disposable harness must not own an existing application window"
    );
    assert!(app.setActivationPolicy(NSApplicationActivationPolicy::Regular));
    app.finishLaunching();
    #[allow(deprecated)]
    app.activateIgnoringOtherApps(true);
    let args: Vec<_> = std::env::args().skip(1).collect();
    let selected = match args.as_slice() {
        [] => FINITE.to_vec(),
        [selector] if selector == "--case=stress_2048" => {
            vec![("stress_2048", stress_2048 as fn())]
        }
        [selector] => FINITE
            .iter()
            .copied()
            .filter(|(name, _)| selector == &format!("--case={name}"))
            .collect(),
        _ => panic!("Select zero or one exact --case=NAME; no unrelated test replay"),
    };
    assert!(!selected.is_empty(), "Unknown native case selection");
    // Fresh per-process reports are assertions from THIS real native executable. They do not
    // restore Cargo/JVM XML, convert compiler success to tests or report unreached methods.
    let output = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../build/ci-verification/share-appkit-native")
        .join(format!("process-{}", std::process::id()));
    std::fs::create_dir_all(output.parent().unwrap()).expect("Cannot create native report parent");
    std::fs::create_dir(&output)
        .expect("Native report output exists or cannot be exclusively created");
    let mut failed = false;
    for (name, case) in selected {
        let started = Instant::now();
        let result = catch_unwind(AssertUnwindSafe(|| autoreleasepool(|_| case())));
        let cleanup = catch_unwind(AssertUnwindSafe(cleanup_owned));
        let passed =
            result.is_ok() && cleanup.is_ok() && !CONTROL_FAILED.load(AtomicOrdering::Acquire);
        println!("NATIVECMPKIT_APPKIT_CASE name={name} passed={passed} seconds={:.6} live={} registry={} cleanup={}",
            started.elapsed().as_secs_f64(), live_count(), registry().len(), cleanup.is_ok());
        let failure = if passed {
            ""
        } else {
            "<failure message=\"Native assertion, control or owned cleanup failed; see original process log\"/>"
        };
        let xml = format!(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?><testsuite name=\"NativeCmpKitAppKitLifecycle\" tests=\"1\" failures=\"{}\" errors=\"0\" skipped=\"0\"><testcase classname=\"com.mohamedrejeb.calf.share.native.AppKitLifecycle\" name=\"{name}\" time=\"{:.6}\">{failure}<system-out>actual-native=true live={} registry={} cleanup={} controlled-callbacks-not-recipient=true</system-out></testcase></testsuite>\n",
            usize::from(!passed), started.elapsed().as_secs_f64(), live_count(), registry().len(), cleanup.is_ok());
        std::fs::write(output.join(format!("TEST-{name}.xml")), xml)
            .expect("Cannot preserve the actual native result");
        failed |= !passed;
        // Never execute other cases against a failed/unknown native owner population.
        if failed {
            break;
        }
    }
    if failed {
        std::process::exit(1);
    }
}
