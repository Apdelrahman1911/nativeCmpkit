//! AppKit objects never cross threads. JNI transfers owned Rust values and a numeric request ID;
//! this table owns every picker/delegate/service until main-thread cleanup acknowledges completion.
use super::operation::{Completion, DISMISSED, FAILED, SUCCESS, UNAVAILABLE};
use super::{registry, ShareData};
use objc2::rc::{autoreleasepool, Retained};
use objc2::runtime::{AnyClass, AnyObject, AnyProtocol, ClassBuilder, Sel};
use objc2::{msg_send, sel, AllocAnyThread, ClassType, MainThreadMarker};
use objc2_app_kit::{NSApplication, NSSharingService, NSSharingServicePicker, NSView, NSWindow};
use objc2_foundation::{
    NSArray, NSObject, NSObjectProtocol, NSPoint, NSRect, NSRectEdge, NSSize, NSString, NSURL,
};
use std::cell::RefCell;
use std::collections::HashMap;
use std::ffi::c_void;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, OnceLock};

struct UiOperation {
    picker: Retained<NSSharingServicePicker>,
    delegate: Retained<AnyObject>,
    service: Option<Retained<NSSharingService>>,
    subject: Option<Retained<NSString>>,
    // Retain the anchor and the items even if the originating JVM window goes away.
    _window: Retained<NSWindow>,
    _view: Retained<NSView>,
    _items: Retained<NSArray<NSObject>>,
    _completion: Arc<Completion>,
}

thread_local! {
    static UI_OPERATIONS: RefCell<HashMap<i64, UiOperation>> = RefCell::new(HashMap::new());
}
static LIVE_OPERATIONS: AtomicUsize = AtomicUsize::new(0);

pub(super) fn live_count() -> usize {
    LIVE_OPERATIONS.load(Ordering::Acquire)
}

pub(super) fn is_supported() -> bool {
    // Cancellation requires close. Do not offer a supposedly cancellable operation on an older
    // runtime that cannot close its picker. Class/selector lookup does not create AppKit objects.
    let Some(class) = AnyClass::get(c"NSSharingServicePicker") else {
        return false;
    };
    unsafe { msg_send![class, instancesRespondToSelector: sel!(close)] }
}

pub(super) fn present(id: i64, completion: Arc<Completion>, data: ShareData) {
    dispatch_main(id, move || present_on_main(id, completion, data));
}

pub(super) fn cancel(id: i64) {
    // Always queue, including when called on Main. In particular, never release an Objective-C
    // delegate while one of its callbacks is executing.
    dispatch_main(id, move || finish_on_main(id, DISMISSED));
}

fn present_on_main(id: i64, completion: Arc<Completion>, data: ShareData) {
    let Some(main) = MainThreadMarker::new() else {
        registry().finish(id, FAILED);
        return;
    };
    if completion.cancelled() {
        registry().finish(id, DISMISSED);
        return;
    }
    if !is_supported() {
        registry().finish(id, UNAVAILABLE);
        return;
    }
    let Some(delegate_class) = delegate_class() else {
        registry().finish(id, FAILED);
        return;
    };
    let Some(id_ivar) = delegate_class.instance_variable(c"_nativeCmpkitRequestId") else {
        registry().finish(id, FAILED);
        return;
    };
    let app = NSApplication::sharedApplication(main);
    let Some(window) = app.keyWindow() else {
        registry().finish(id, UNAVAILABLE);
        return;
    };
    let Some(view) = window.contentView() else {
        registry().finish(id, UNAVAILABLE);
        return;
    };

    let mut items: Vec<Retained<NSObject>> = Vec::new();
    if let Some(text) = data.text {
        items.push(Retained::into_super(NSString::from_str(&text)));
    }
    if let Some(url) = data.url {
        let Some(url) = NSURL::URLWithString(&NSString::from_str(&url)) else {
            registry().finish(id, FAILED);
            return;
        };
        items.push(Retained::into_super(url));
    }
    for path in data.paths {
        items.push(Retained::into_super(NSURL::fileURLWithPath(
            &NSString::from_str(&path),
        )));
    }
    if items.is_empty() {
        registry().finish(id, FAILED);
        return;
    }
    let items = NSArray::from_retained_slice(&items);
    // The array contains only NSString/NSURL, both conforming to NSPasteboardWriting.
    let picker: Retained<NSSharingServicePicker> =
        unsafe { msg_send![NSSharingServicePicker::alloc(), initWithItems: &*items] };
    if !picker.respondsToSelector(sel!(close)) {
        registry().finish(id, UNAVAILABLE);
        return;
    }
    let delegate: Retained<AnyObject> = unsafe { msg_send![delegate_class, new] };
    // This is the same i64 ivar registered below, initialized before the delegate is exposed.
    unsafe { id_ivar.load_ptr::<i64>(&delegate).write(id) };
    let subject = data.subject.map(|s| NSString::from_str(&s));
    let bounds = view.bounds();
    let anchor = NSRect::new(
        NSPoint::new(
            bounds.origin.x + bounds.size.width / 2.0,
            bounds.origin.y + bounds.size.height / 2.0,
        ),
        NSSize::new(1.0, 1.0),
    );
    // Store native owners before any call that can invoke a delegate. Do not hold a RefCell borrow
    // over an Objective-C call: AppKit is allowed to call back synchronously.
    UI_OPERATIONS.with(|operations| {
        operations.borrow_mut().insert(
            id,
            UiOperation {
                picker: picker.clone(),
                delegate: delegate.clone(),
                service: None,
                subject,
                _window: window,
                _view: view.clone(),
                _items: items,
                _completion: completion.clone(),
            },
        );
    });
    LIVE_OPERATIONS.fetch_add(1, Ordering::Release);
    if completion.cancelled() {
        finish_on_main(id, DISMISSED);
        return;
    }
    // The runtime class explicitly implements the selector contracts of both delegate protocols.
    let _: () = unsafe { msg_send![&*picker, setDelegate: &*delegate] };
    picker.showRelativeToRect_ofView_preferredEdge(anchor, &view, NSRectEdge::MinY);
}

fn finish_on_main(id: i64, result: i32) {
    if MainThreadMarker::new().is_none() {
        // No AppKit object may be destroyed here; our dispatcher must reach the true Main thread.
        return;
    }
    let operation = UI_OPERATIONS.with(|operations| operations.borrow_mut().remove(&id));
    if let Some(operation) = operation {
        // close() calls didChoose(nil) if a delegate is still installed, so detach first.
        operation.picker.setDelegate(None);
        if let Some(service) = &operation.service {
            service.setDelegate(None);
        }
        operation.picker.close();
        drop(operation);
        LIVE_OPERATIONS.fetch_sub(1, Ordering::Release);
    }
    // Ownership cleanup precedes result visibility / admission of the next request.
    registry().finish(id, result);
}

fn finish_later(id: i64, result: i32) {
    dispatch_main(id, move || finish_on_main(id, result));
}

unsafe fn request_id(this: *const AnyObject) -> Option<i64> {
    let this = unsafe { this.as_ref() }?;
    let ivar = this.class().instance_variable(c"_nativeCmpkitRequestId")?;
    // Only the registered, strongly owned delegate receives these methods; the immutable ivar is
    // an i64, never a raw Arc or borrowed JVM pointer.
    Some(unsafe { *ivar.load::<i64>(this) })
}

unsafe extern "C" fn did_choose(
    this: *const AnyObject,
    _cmd: Sel,
    _picker: *const AnyObject,
    service: *const AnyObject,
) {
    if service.is_null() {
        if let Some(id) = unsafe { request_id(this) } {
            finish_later(id, DISMISSED);
        }
    }
    // Selection is not delivery. Only didShareItems reports SUCCESS.
}

unsafe extern "C" fn delegate_for_service(
    this: *const AnyObject,
    _cmd: Sel,
    _picker: *const AnyObject,
    service: *mut NSSharingService,
) -> *const AnyObject {
    let Some(id) = (unsafe { request_id(this) }) else {
        return std::ptr::null();
    };
    if MainThreadMarker::new().is_none() {
        finish_later(id, FAILED);
        return std::ptr::null();
    }
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let Some(service) = (unsafe { Retained::retain(service) }) else {
            return std::ptr::null();
        };
        let owners = UI_OPERATIONS.with(|operations| {
            let mut operations = operations.borrow_mut();
            let operation = operations.get_mut(&id)?;
            operation.service = Some(service.clone());
            Some((operation.delegate.clone(), operation.subject.clone()))
        });
        let Some((delegate, subject)) = owners else {
            return std::ptr::null();
        };
        service.setSubject(subject.as_deref());
        // The map retains the delegate until a later Main turn detaches service/picker delegates.
        Retained::as_ptr(&delegate)
    }));
    result.unwrap_or_else(|_| {
        finish_later(id, FAILED);
        std::ptr::null()
    })
}

unsafe extern "C" fn did_share(
    this: *const AnyObject,
    _cmd: Sel,
    _service: *const AnyObject,
    _items: *const AnyObject,
) {
    if let Some(id) = unsafe { request_id(this) } {
        finish_later(id, SUCCESS);
    }
}

unsafe extern "C" fn did_fail(
    this: *const AnyObject,
    _cmd: Sel,
    _service: *const AnyObject,
    _items: *const AnyObject,
    _error: *const AnyObject,
) {
    if let Some(id) = unsafe { request_id(this) } {
        finish_later(id, FAILED);
    }
}

fn delegate_class() -> Option<&'static AnyClass> {
    static CLASS: OnceLock<Option<&'static AnyClass>> = OnceLock::new();
    *CLASS.get_or_init(|| {
        // A name collision fails closed instead of assuming somebody else's layout/implementation.
        let mut builder = ClassBuilder::new(c"NativeCmpkitShareDelegateV1", NSObject::class())?;
        builder.add_ivar::<i64>(c"_nativeCmpkitRequestId");
        for name in [
            c"NSSharingServicePickerDelegate",
            c"NSSharingServiceDelegate",
        ] {
            if let Some(protocol) = AnyProtocol::get(name) {
                builder.add_protocol(protocol);
            }
        }
        unsafe {
            builder.add_method(
                sel!(sharingServicePicker:didChooseSharingService:),
                did_choose as unsafe extern "C" fn(_, _, _, _),
            );
            builder.add_method(
                sel!(sharingServicePicker:delegateForSharingService:),
                delegate_for_service as unsafe extern "C" fn(_, _, _, _) -> _,
            );
            builder.add_method(
                sel!(sharingService:didShareItems:),
                did_share as unsafe extern "C" fn(_, _, _, _),
            );
            builder.add_method(
                sel!(sharingService:didFailToShareItems:error:),
                did_fail as unsafe extern "C" fn(_, _, _, _, _),
            );
        }
        Some(builder.register())
    })
}

struct MainTask {
    id: i64,
    action: Box<dyn FnOnce() + Send>,
}

fn dispatch_main(id: i64, action: impl FnOnce() + Send + 'static) {
    extern "C" {
        static _dispatch_main_q: c_void;
        fn dispatch_async_f(
            queue: *const c_void,
            context: *mut c_void,
            work: extern "C" fn(*mut c_void),
        );
    }
    extern "C" fn run(context: *mut c_void) {
        let task = unsafe { Box::from_raw(context.cast::<MainTask>()) };
        let id = task.id;
        // Recover Rust panics without unwinding through libdispatch; Objective-C exceptions are
        // not swallowed or claimed to be caught by this boundary.
        autoreleasepool(|_| {
            let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(task.action));
            if result.is_err() {
                finish_on_main(id, FAILED);
            }
        });
    }
    let task = Box::new(MainTask {
        id,
        action: Box::new(action),
    });
    // Only Send Rust values enter this closure. No unsafe Send implementation for AppKit owners.
    unsafe { dispatch_async_f(&_dispatch_main_q, Box::into_raw(task).cast(), run) };
}
