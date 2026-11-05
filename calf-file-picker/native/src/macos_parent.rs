// Added for NativeCmpKit: owned AppKit parenting via a real JDK resource borrow.
// This is an OpenJDK-17-specific implementation, not a Java SE peer API.
use crate::macos_release_slots::{OwnedRecord, ReleaseSlots};
use crate::parent_retain_slot::{BorrowError, RequestIds, RetainSlot};
use jni::objects::{
    GlobalRef, JClass, JFieldID, JMethodID, JObject, JStaticMethodID, JThrowable, JValue,
};
use jni::signature::{Primitive, ReturnType};
use jni::sys::{jlong, jvalue, JNI_TRUE};
use jni::{JNIEnv, JavaVM};
use objc2::rc::Retained;
use objc2::MainThreadMarker;
use objc2_app_kit::{NSView, NSWindow};
use raw_window_handle::{
    AppKitDisplayHandle, AppKitWindowHandle, HandleError, HasDisplayHandle, HasWindowHandle,
    RawDisplayHandle, RawWindowHandle,
};
use std::cell::RefCell;
use std::ffi::c_void;
use std::io::Write;
use std::marker::PhantomData;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::ptr::NonNull;
use std::sync::{Arc, OnceLock};

const RESOURCE: &str = "sun/lwawt/macosx/CFRetainedResource";
const ACTION: &str = "sun/lwawt/macosx/CFRetainedResource$CFNativeAction";
const EXECUTE_SIGNATURE: &str = "(Lsun/lwawt/macosx/CFRetainedResource$CFNativeAction;)V";
static REQUEST_IDS: RequestIds = RequestIds::new();
// This finite capacity is reserved BEFORE arm/CFRetain. Unknown release outcomes
// keep their entries forever; they are not evicted or retried as completed work.
const RELEASE_CAPACITY: usize = 64;
static RELEASE_SLOTS: OnceLock<ReleaseSlots<ReleaseJob, RELEASE_CAPACITY>> = OnceLock::new();
thread_local! {
    // No cross-thread lock: execute calls CFNativeAction.run on its caller.
    static RETAIN_SLOT: RefCell<RetainSlot> = RefCell::new(RetainSlot::default());
}

#[link(name = "CoreFoundation", kind = "framework")]
unsafe extern "C" {
    fn CFRetain(resource: *const c_void) -> *const c_void;
}

#[derive(Debug)]
pub(super) enum ParentError {
    Unavailable(&'static str),
    Borrow(BorrowError),
    Jni(jni::errors::Error),
    Java(GlobalRef),
    Panic,
}

impl From<jni::errors::Error> for ParentError {
    fn from(error: jni::errors::Error) -> Self {
        Self::Jni(error)
    }
}

impl ParentError {
    /// True means a throwable is pending (including a preserved prior primary),
    /// not that an unavailable/failed Throw delivered this particular error.
    pub(super) fn throw(&self, env: &mut JNIEnv) -> bool {
        match env.exception_check() {
            Ok(true) => return true,
            Ok(false) => {}
            Err(_) => {
                diagnostic("native-parent primary exception state is unavailable");
                return false;
            }
        }
        let delivered = if let Self::Java(global) = self {
            if global.as_obj().is_null() {
                diagnostic("native-parent null exception transport refused before Throw");
                return false;
            }
            // Borrow the checked, still-held global directly. NewLocalRef is
            // unnecessary and jni0.21.1 does not check its null/OOM outcome.
            let throwable: &JThrowable = global.as_obj().into();
            env.throw(throwable)
        } else {
            let message = match self {
                Self::Unavailable(message) => (*message).to_owned(),
                Self::Borrow(error) => format!("Native parent borrow refused: {error:?}"),
                Self::Jni(error) => format!("Native parent JNI operation failed: {error}"),
                Self::Java(_) => unreachable!("handled before formatting"),
                Self::Panic => "Native parent operation panicked".to_owned(),
            };
            env.throw_new("java/lang/IllegalStateException", message)
        };
        if delivered.is_err() {
            diagnostic("native-parent primary Throw failed; no replacement attempted");
            return false;
        }
        match env.exception_check() {
            Ok(true) => true,
            _ => {
                diagnostic("native-parent primary Throw did not establish a pending throwable");
                false
            }
        }
    }
}

/// jni0.21.1 NewGlobalRef returns Ok even for null/OOM. The immediate pending
/// and null checks are required before any further JNI work or native retain.
fn checked_global_ref(
    env: &mut JNIEnv,
    object: &JObject,
    unavailable: &'static str,
) -> Result<GlobalRef, ParentError> {
    crate::ensure_clean(env)?;
    if object.is_null() {
        return Err(ParentError::Unavailable(unavailable));
    }
    let global = env.new_global_ref(object)?;
    crate::ensure_clean(env)?;
    if global.as_obj().is_null() {
        return Err(ParentError::Unavailable(unavailable));
    }
    Ok(global)
}

struct ReleasePolicy {
    vm: JavaVM,
    release_class: GlobalRef,
    release_method: JStaticMethodID,
}

// This record holds the actual additional retain and its precomputed policy.
// A numeric slot/key alone is never native resource ownership.
struct ReleaseJob {
    pointer: usize,
    policy: Arc<ReleasePolicy>,
}

/// Owns one additional CFRetain plus its already-reserved recovery storage.
/// Field Drop is memory-only; it cannot attach, schedule or replace a primary.
/// No unconditional unsafe Send/Sync is needed for this owned binding.
struct OwnedWindow {
    record: OwnedRecord<'static, ReleaseJob>,
}

impl OwnedWindow {
    fn pointer(&self) -> usize {
        self.record.value().pointer
    }
}

fn diagnostic(message: &'static str) {
    // Fallible reporting is outside every recovery-ownership mutex.
    // Ignore stderr errors rather than panicking across the exported JNI ABI.
    let _ = writeln!(std::io::stderr(), "NativeCmpKit: {message}");
}

/// Only called after a CLEAN drain or post-clear exception-transport allocation
/// began. A throwable now present belongs to that new operation, not to a prior
/// primary. This helper never suspends an interrupted picker/main throwable.
fn clear_new_cleanup_exception(env: &mut JNIEnv) -> Result<(), jni::errors::Error> {
    if env.exception_check()? {
        env.exception_clear()?;
    }
    crate::ensure_clean(env)
}

/// Opportunistic bounded recovery at live JNI entry/successful-exit boundaries.
/// NEVER call from retain_under_borrow, the common panic wrapper, or Drop.
pub(super) fn drain_pending_releases(env: &mut JNIEnv) {
    let Some(slots) = RELEASE_SLOTS.get() else {
        return;
    };
    if crate::ensure_clean(env).is_err() {
        // Never suspend/clear an existing primary just to perform cleanup.
        return;
    }
    let outcome = catch_unwind(AssertUnwindSafe(|| drain_clean_matching(env, slots)));
    if !matches!(outcome, Ok(Ok(()))) {
        // An attempt guard already restored Known or quarantined Unknown during
        // unwind. No release retry, raw VM probe, or fallback CFRelease occurs.
        diagnostic("native-parent cleanup interrupted; ownership remains recorded");
        if clear_new_cleanup_exception(env).is_err() {
            diagnostic("new cleanup exception could not be cleared; further work refused");
        }
    }
}

fn drain_clean_matching(
    env: &mut JNIEnv,
    slots: &ReleaseSlots<ReleaseJob, RELEASE_CAPACITY>,
) -> Result<(), jni::errors::Error> {
    crate::ensure_clean(env)?;
    // The current authenticated native entry proves this VM is live. Do not
    // attach/probe through an old saved VM pointer to discover that condition.
    let vm = env.get_java_vm()?;
    crate::ensure_clean(env)?;
    let vm_key = vm.get_java_vm_pointer() as usize;
    let mut visits = slots.attempts_for(vm_key);
    loop {
        crate::ensure_clean(env)?; // BEFORE moving any next record out of storage.
        let Some(mut attempt) = visits.next() else {
            return Ok(());
        };
        if attempt.value().policy.vm.get_java_vm_pointer() as usize != vm_key {
            // Defensive policy/key consistency refusal is provably pre-invocation.
            // Guard Drop restores the real record to KnownUnscheduled.
            diagnostic("native-parent cleanup VM policy/key mismatch; deferred");
            continue;
        }
        // Set BEFORE entering the unchecked-call wrapper. Any wrapper/Java error
        // or unwind after this boundary is conservative Unknown, never retried.
        attempt.may_have_invoked();
        let requested = {
            let job = attempt.value();
            // SAFETY: this nonnull class global and exact (JZ)V method were
            // checked before retain and are still held by this real record.
            // Preserve JDK TOP-LEVEL-event release; main-queue CFRelease is not
            // a valid substitute in nested AppKit loops for the final retain.
            unsafe {
                env.call_static_method_unchecked(
                    &job.policy.release_class,
                    job.policy.release_method,
                    ReturnType::Primitive(Primitive::Void),
                    &[
                        jvalue {
                            j: job.pointer as jlong,
                        },
                        jvalue { z: JNI_TRUE },
                    ],
                )
            }
        };
        match (requested, env.exception_check()) {
            (Ok(_), Ok(false)) => {
                // Request ownership transferred. This does NOT prove actual
                // top-level CFRelease completion, native counts, or shutdown.
                attempt.request_transferred();
            }
            _ => {
                drop(attempt); // Actual record is quarantined; no metadata drop.
                diagnostic("native-parent release request outcome unknown; no retry");
                clear_new_cleanup_exception(env)?;
            }
        }
    }
}

pub(super) struct ParentLease {
    owner: OwnedWindow,
    window: GlobalRef,
    peer: GlobalRef,
    platform: GlobalRef,
    peer_field: JFieldID,
    get_platform: JMethodID,
    is_disposed: JMethodID,
    native_pointer: JFieldID,
}

impl ParentLease {
    pub(super) fn acquire(
        env: &mut JNIEnv,
        bridge: &JClass,
        window: &JObject,
    ) -> Result<Self, ParentError> {
        crate::ensure_clean(env)?;
        // PushLocalFrame itself is allowed with pending exceptions; the guard
        // prevents the subsequent object/class work, not the legal frame call.
        env.with_local_frame(24, |env| Self::acquire_in_frame(env, bridge, window))
    }

    fn acquire_in_frame(
        env: &mut JNIEnv,
        bridge: &JClass,
        window: &JObject,
    ) -> Result<Self, ParentError> {
        crate::ensure_clean(env)?;
        let vm = env.get_java_vm()?;
        crate::ensure_clean(env)?;
        let vm_key = vm.get_java_vm_pointer() as usize;
        let reservation = RELEASE_SLOTS
            .get_or_init(ReleaseSlots::new)
            .reserve(vm_key)
            .ok_or(ParentError::Unavailable(
                "Native parent recovery capacity (64) is exhausted; no parent retained",
            ))?;
        if window.is_null() {
            return Err(ParentError::Unavailable(
                "Requested AWT parent is absent or mismatched",
            ));
        }
        let is_window = env.is_instance_of(window, "java/awt/Window")?;
        crate::ensure_clean(env)?;
        if !is_window {
            return Err(ParentError::Unavailable(
                "Requested AWT parent is absent or mismatched",
            ));
        }
        let component_class = env.find_class("java/awt/Component")?;
        let peer_class = env.find_class("sun/lwawt/LWWindowPeer")?;
        let platform_class = env.find_class("sun/lwawt/macosx/CPlatformWindow")?;
        let resource_class = env.find_class(RESOURCE)?;
        let action_class = env.find_class(ACTION)?;
        let peer_field =
            env.get_field_id(&component_class, "peer", "Ljava/awt/peer/ComponentPeer;")?;
        let get_platform = env.get_method_id(
            &peer_class,
            "getPlatformWindow",
            "()Lsun/lwawt/PlatformWindow;",
        )?;
        let is_disposed = env.get_method_id(&peer_class, "isDisposed", "()Z")?;
        let execute = env.get_method_id(&resource_class, "execute", EXECUTE_SIGNATURE)?;
        let native_pointer = env.get_field_id(&resource_class, "ptr", "J")?;
        let release_method =
            env.get_static_method_id(&resource_class, "nativeCFRelease", "(JZ)V")?;
        let peer = env
            .get_field_unchecked(window, peer_field, ReturnType::Object)?
            .l()?;
        if peer.is_null() {
            return Err(ParentError::Unavailable(
                "Requested parent has no live LWWindowPeer",
            ));
        }
        let actual_peer_class = env.get_object_class(&peer)?;
        crate::ensure_clean(env)?;
        if actual_peer_class.is_null() {
            return Err(ParentError::Unavailable(
                "Requested parent peer class is unavailable",
            ));
        }
        let same_peer_class = env.is_same_object(&actual_peer_class, &peer_class)?;
        crate::ensure_clean(env)?;
        if !same_peer_class {
            return Err(ParentError::Unavailable(
                "Requested parent has a mismatched LWWindowPeer",
            ));
        }
        // SAFETY: exact peer class was checked; IDs came from its pinned class.
        if unsafe {
            env.call_method_unchecked(
                &peer,
                is_disposed,
                ReturnType::Primitive(Primitive::Boolean),
                &[],
            )
        }?
        .z()?
        {
            return Err(ParentError::Unavailable(
                "Requested AWT parent peer is disposed",
            ));
        }
        let platform =
            unsafe { env.call_method_unchecked(&peer, get_platform, ReturnType::Object, &[]) }?
                .l()?;
        if platform.is_null() {
            return Err(ParentError::Unavailable(
                "Requested parent platform peer is absent",
            ));
        }
        let actual_platform_class = env.get_object_class(&platform)?;
        crate::ensure_clean(env)?;
        if actual_platform_class.is_null() {
            return Err(ParentError::Unavailable(
                "Requested parent platform class is unavailable",
            ));
        }
        let same_platform_class = env.is_same_object(&actual_platform_class, &platform_class)?;
        crate::ensure_clean(env)?;
        if !same_platform_class {
            return Err(ParentError::Unavailable(
                "Requested parent platform peer is mismatched",
            ));
        }
        // Pin the original graph and release policy BEFORE any native ownership.
        let window = checked_global_ref(env, window, "Requested parent Window pin is unavailable")?;
        let peer = checked_global_ref(env, &peer, "Requested parent peer pin is unavailable")?;
        let platform = checked_global_ref(
            env,
            &platform,
            "Requested parent platform pin is unavailable",
        )?;
        let release_class = checked_global_ref(
            env,
            &resource_class,
            "Native parent release class pin is unavailable",
        )?;
        let policy = Arc::new(ReleasePolicy {
            vm,
            release_class,
            release_method,
        });
        let ticket = REQUEST_IDS.next().map_err(ParentError::Borrow)?;
        let action = env
            .call_static_method(
                bridge,
                "newMacOsRetainAction",
                "(Ljava/lang/Class;J)Ljava/lang/Object;",
                &[JValue::Object(&action_class), JValue::Long(ticket)],
            )?
            .l()?;
        if action.is_null() {
            return Err(ParentError::Unavailable(
                "Native parent borrow action is absent",
            ));
        }
        let is_action = env.is_instance_of(&action, &action_class)?;
        crate::ensure_clean(env)?;
        if !is_action {
            return Err(ParentError::Unavailable(
                "Native parent borrow action is mismatched",
            ));
        }
        RETAIN_SLOT
            .with(|slot| slot.borrow_mut().arm(ticket))
            .map_err(ParentError::Borrow)?;
        // No dispatch inside this callback. The JDK read lock protects the live
        // pointer THROUGH CFRetain, independently of later peer disposal.
        let executed = catch_unwind(AssertUnwindSafe(|| unsafe {
            env.call_method_unchecked(
                platform.as_obj(),
                execute,
                ReturnType::Primitive(Primitive::Void),
                &[jvalue { l: action.as_raw() }],
            )
        }));
        let outcome = RETAIN_SLOT.with(|slot| slot.borrow_mut().finish(ticket));
        let owner = outcome.owned.map(|pointer| OwnedWindow {
            // The actual pointer and precomputed policy enter the reserved
            // linear owner BEFORE propagating any callback/execute error.
            record: reservation.own(ReleaseJob { pointer, policy }),
        });
        // Failure Drop only parks the real record. It cannot create a cleanup
        // exception before the logical primary reaches the outer picker entry.
        executed.map_err(|_| ParentError::Panic)??;
        crate::ensure_clean(env)?;
        outcome.result.map_err(ParentError::Borrow)?;
        let lease = Self {
            owner: owner.ok_or(ParentError::Unavailable(
                "Requested native parent is no longer live",
            ))?,
            window,
            peer,
            platform,
            peer_field,
            get_platform,
            is_disposed,
            native_pointer,
        };
        lease.validate(env)?;
        Ok(lease)
    }

    fn validate(&self, env: &mut JNIEnv) -> Result<(), ParentError> {
        crate::ensure_clean(env)?;
        let current = env
            .get_field_unchecked(self.window.as_obj(), self.peer_field, ReturnType::Object)?
            .l()?;
        let current = env.auto_local(current);
        if current.is_null() {
            return Err(ParentError::Unavailable(
                "Requested native parent generation was replaced",
            ));
        }
        let same_peer = env.is_same_object(&*current, self.peer.as_obj())?;
        crate::ensure_clean(env)?;
        if !same_peer {
            return Err(ParentError::Unavailable(
                "Requested native parent generation was replaced",
            ));
        }
        // IDs remain valid: the window/peer/platform global references retain
        // the corresponding exact bootstrap class hierarchy for this lease.
        if unsafe {
            env.call_method_unchecked(
                self.peer.as_obj(),
                self.is_disposed,
                ReturnType::Primitive(Primitive::Boolean),
                &[],
            )
        }?
        .z()?
        {
            return Err(ParentError::Unavailable(
                "Requested native parent peer was disposed",
            ));
        }
        let platform = unsafe {
            env.call_method_unchecked(
                self.peer.as_obj(),
                self.get_platform,
                ReturnType::Object,
                &[],
            )
        }?
        .l()?;
        let platform = env.auto_local(platform);
        if platform.is_null() {
            return Err(ParentError::Unavailable(
                "Requested native parent platform generation changed",
            ));
        }
        let same_platform = env.is_same_object(&*platform, self.platform.as_obj())?;
        crate::ensure_clean(env)?;
        if !same_platform {
            return Err(ParentError::Unavailable(
                "Requested native parent platform generation changed",
            ));
        }
        // A volatile pointer read is ONLY a generation comparison, never an
        // acquisition/dereference: the independent CFRetain remains the owner.
        let pointer_value = env.get_field_unchecked(
            self.platform.as_obj(),
            self.native_pointer,
            ReturnType::Primitive(Primitive::Long),
        )?;
        crate::ensure_clean(env)?; // jni0.21.1 primitive field access is unchecked.
        let current_pointer = pointer_value.j()? as usize;
        if current_pointer != self.owner.pointer() || current_pointer == 0 {
            return Err(ParentError::Unavailable(
                "Requested native parent resource generation changed",
            ));
        }
        Ok(())
    }

    /// Build AND synchronously show under one main-only borrowed-view scope.
    /// The library caller returns only owned PathBuf data, never FileDialog/handles.
    pub(super) fn with_parent<R: Send>(
        &self,
        worker: &mut JNIEnv,
        show: impl FnOnce(&ScopedAppKitParent<'_>) -> R + Send,
    ) -> Result<R, ParentError> {
        crate::ensure_clean(worker)?; // Refuse before dispatch, not only on main.
        let worker_vm = worker.get_java_vm()?;
        crate::ensure_clean(worker)?;
        if worker_vm.get_java_vm_pointer()
            != self.owner.record.value().policy.vm.get_java_vm_pointer()
        {
            return Err(ParentError::Unavailable(
                "Requested native parent belongs to another JVM",
            ));
        }
        run_on_main(|mtm| {
            let mut env = self.owner.record.value().policy.vm.attach_current_thread()?;
            if env.exception_check()? {
                // Do not steal/clear an unrelated pre-existing main-thread exception.
                return Err(ParentError::Unavailable(
                    "AppKit thread already has a pending JNI exception",
                ));
            }
            let result = catch_unwind(AssertUnwindSafe(|| {
                self.validate(&mut env)?;
                let pointer = self.owner.pointer();
                // SAFETY: exact CPlatformWindow.ptr was CFRetained INSIDE execute's
                // actual read lock; this lease owns it; marker proves AppKit thread.
                let window = unsafe { &*(pointer as *const NSWindow) };
                let view = window.contentView().ok_or(ParentError::Unavailable(
                    "Native parent content view is absent",
                ))?;
                ensure_attached(&view, pointer, mtm)?;
                let parent = ScopedAppKitParent {
                    view,
                    _main: mtm,
                    _lease: PhantomData,
                };
                let result = show(&parent);
                self.validate(&mut env)?;
                ensure_attached(&parent.view, pointer, mtm)?;
                Ok(result)
            }))
            .unwrap_or(Err(ParentError::Panic));
            transport_main_exception(&mut env, result)
        })
    }
}

fn ensure_attached(
    view: &NSView,
    expected: usize,
    _main: MainThreadMarker,
) -> Result<(), ParentError> {
    if view
        .window()
        .is_some_and(|window| Retained::as_ptr(&window) as usize == expected)
    {
        Ok(())
    } else {
        Err(ParentError::Unavailable(
            "Native parent view is detached or attached to another window",
        ))
    }
}

/// Transport only exceptions raised by this main-thread operation back to JNI's
/// original worker. No local JNI reference or JNIEnv crosses the dispatch boundary.
fn transport_main_exception<R>(
    env: &mut JNIEnv,
    result: Result<R, ParentError>,
) -> Result<R, ParentError> {
    if !env.exception_check()? {
        return result;
    }
    let original = env.exception_occurred()?;
    let original = env.auto_local(original);
    if original.is_null() {
        // Main was clean at entry. This inconsistent newly-raised exception
        // cannot be transported; never construct Java(null) or call Throw(null).
        env.exception_clear()?;
        diagnostic("native-parent main exception has no transportable throwable");
        return Err(ParentError::Unavailable(
            "Native parent main exception is unavailable for transport",
        ));
    }
    env.exception_clear()?;
    crate::ensure_clean(env)?;
    match checked_global_ref(
        env,
        &original,
        "Native parent exception transport reference is unavailable",
    ) {
        Ok(throwable) => Err(ParentError::Java(throwable)),
        Err(_) => {
            // An allocation failure cannot create a transport global ref. Do
            // not preserve its newly raised OOM on the unrelated AppKit thread.
            // Exact original delivery is impossible without a usable strong ref.
            if clear_new_cleanup_exception(env).is_err() {
                diagnostic("new exception-transport failure could not be cleared on main");
            }
            diagnostic("native-parent Java exception transport allocation failed");
            Err(ParentError::Unavailable(
                "Native parent exception transport failed",
            ))
        }
    }
}

pub(super) struct ScopedAppKitParent<'lease> {
    view: Retained<NSView>,
    _main: MainThreadMarker,
    _lease: PhantomData<&'lease ParentLease>,
}

impl HasWindowHandle for ScopedAppKitParent<'_> {
    fn window_handle(&self) -> Result<raw_window_handle::WindowHandle<'_>, HandleError> {
        let view = NonNull::from(&*self.view).cast::<c_void>();
        let raw = RawWindowHandle::AppKit(AppKitWindowHandle::new(view));
        // SAFETY: borrowed handle is tied to this live retained NSView on main.
        Ok(unsafe { raw_window_handle::WindowHandle::borrow_raw(raw) })
    }
}

impl HasDisplayHandle for ScopedAppKitParent<'_> {
    fn display_handle(&self) -> Result<raw_window_handle::DisplayHandle<'_>, HandleError> {
        let raw = RawDisplayHandle::AppKit(AppKitDisplayHandle::new());
        Ok(unsafe { raw_window_handle::DisplayHandle::borrow_raw(raw) })
    }
}

fn run_on_main<R: Send>(
    work: impl FnOnce(MainThreadMarker) -> Result<R, ParentError> + Send,
) -> Result<R, ParentError> {
    let guarded =
        |mtm| catch_unwind(AssertUnwindSafe(|| work(mtm))).unwrap_or(Err(ParentError::Panic));
    if let Some(mtm) = MainThreadMarker::new() {
        return guarded(mtm);
    }
    let mut result = None;
    dispatch2::DispatchQueue::main().exec_sync(|| {
        // Catch INSIDE dispatch's C callback; no Rust unwind crosses that ABI.
        result = Some(match MainThreadMarker::new() {
            Some(mtm) => guarded(mtm),
            None => Err(ParentError::Unavailable(
                "AppKit main-thread dispatch mismatch",
            )),
        });
    });
    result.unwrap_or(Err(ParentError::Unavailable(
        "AppKit main-thread dispatch produced no result",
    )))
}

pub(super) fn retain_under_borrow(env: &mut JNIEnv, ticket: jlong, pointer: jlong) {
    if crate::ensure_clean(env).is_err() {
        // No retain or release drain while a Java primary is already pending.
        // execute's caller still finishes the original one-shot request.
        return;
    }
    let result = RETAIN_SLOT.with(|slot| match slot.try_borrow_mut() {
        Ok(mut slot) => slot.retain_once(ticket, pointer as usize, |pointer| {
            // SAFETY: this callback is synchronously authorized once by execute;
            // its live-pointer read lock is STILL HELD. Retain count operation
            // only: no AppKit messaging, external lock or nested dispatch.
            unsafe { CFRetain(pointer as *const c_void) as usize }
        }),
        Err(_) => Err(BorrowError::Busy),
    });
    if let Err(error) = result {
        let _ = ParentError::Borrow(error).throw(env);
    }
}
