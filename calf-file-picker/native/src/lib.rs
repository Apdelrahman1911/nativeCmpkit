// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
use jni::objects::{JClass, JObject, JObjectArray, JString};
use jni::sys::{jboolean, jint, jlong, jobjectArray, jstring, JNI_TRUE};
use jni::JNIEnv;
#[cfg(not(target_os = "macos"))]
use raw_window_handle::{
    HandleError, HasDisplayHandle, HasWindowHandle, RawDisplayHandle, RawWindowHandle,
};
use rfd::FileDialog;
use std::path::PathBuf;
use std::sync::{Arc, OnceLock};
#[cfg(test)]
mod jni_path_tests;
#[cfg(target_os = "macos")]
mod macos_parent;
#[cfg(any(target_os = "macos", test))]
mod macos_release_slots;
#[cfg(any(target_os = "macos", test))]
mod parent_retain_slot;
mod path_encoding;
mod registry;
#[cfg(target_os = "macos")]
type ParentWindow = macos_parent::ParentLease;
use path_encoding::unicode_path;
use registry::Registry;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Preserve a pending primary without clearing/replacing it or doing later JNI.
fn ensure_clean(env: &JNIEnv) -> Result<(), jni::errors::Error> {
    if env.exception_check()? {
        Err(jni::errors::Error::JavaException)
    } else {
        Ok(())
    }
}

/// Convert a JString to a Rust String, retaining None for a valid null argument.
/// JNI/reference failures are errors, never silently changed to an absent value.
fn jstring_to_string(
    env: &mut JNIEnv,
    js: &JString,
) -> Result<Option<String>, jni::errors::Error> {
    ensure_clean(env)?;
    if js.is_null() {
        return Ok(None);
    }
    let string_class = env.find_class("java/lang/String")?;
    let string_class = env.auto_local(string_class);
    let is_string = env.is_instance_of(js, &*string_class)?;
    ensure_clean(env)?;
    if !is_string {
        return Err(jni::errors::Error::JniCall(
            jni::errors::JniError::InvalidArguments,
        ));
    }
    // SAFETY: nonnull String instance was checked above in this clean env.
    // Do not use get_string's hidden unchecked GetObjectClass allocation path.
    let value = unsafe { env.get_string_unchecked(js) }?;
    let value = String::from(value); // JavaStr Drop releases UTF chars on all paths.
    ensure_clean(env)?;
    Ok(Some(value))
}

/// Convert a Java String[] to Vec<String>, properly releasing JNI local references.
fn jstring_array_to_vec(
    env: &mut JNIEnv,
    array: &JObjectArray,
) -> Result<Vec<String>, jni::errors::Error> {
    ensure_clean(env)?;
    if array.is_null() {
        return Ok(Vec::new());
    }
    let len = env.get_array_length(array)?;
    ensure_clean(env)?; // jni0.21.1 GetArrayLength is unchecked.
    let capacity = usize::try_from(len).map_err(|_| {
        jni::errors::Error::JniCall(jni::errors::JniError::InvalidArguments)
    })?;
    let mut result = Vec::new();
    result.try_reserve(capacity).map_err(|_| {
        jni::errors::Error::JniCall(jni::errors::JniError::NoMemory)
    })?;
    for i in 0..len {
        ensure_clean(env)?;
        let obj = env.get_object_array_element(array, i)?;
        let jstr = env.auto_local(JString::from(obj));
        if let Some(value) = jstring_to_string(env, &jstr)? {
            result.push(value);
        }
    }
    Ok(result)
}

/// Convert a Vec of paths to a Java String[], with proper error handling.
fn paths_to_jstring_array(
    env: &mut JNIEnv,
    paths: &[PathBuf],
) -> Result<jobjectArray, jni::errors::Error> {
    ensure_clean(env)?;
    let string_class = env.find_class("java/lang/String")?;
    let array = env.new_object_array(paths.len() as i32, &string_class, JString::default())?;
    // Test-only weak observer of the real result array; no production JNI export/hook.
    #[cfg(test)]
    jni_path_tests::observe_array_if_requested(env, &array)?;

    for (i, path) in paths.iter().enumerate() {
        ensure_clean(env)?;
        let path_str = match unicode_path(path) {
            Ok(s) => s,
            Err(message) => {
                env.throw_new("java/io/IOException", message)?;
                return Err(jni::errors::Error::JavaException);
            }
        };
        let jstr = env.new_string(path_str)?;
        env.set_object_array_element(&array, i as i32, &jstr)?;
        env.delete_local_ref(jstr)?;
    }

    Ok(array.into_raw())
}

/// Convert a path to a jstring, propagating an error before subsequent JNI work.
fn path_to_jstring(
    env: &mut JNIEnv,
    path: &std::path::Path,
) -> Result<jstring, jni::errors::Error> {
    ensure_clean(env)?;
    let s = match unicode_path(path) {
        Ok(s) => s,
        Err(message) => {
            env.throw_new("java/io/IOException", message)?;
            return Err(jni::errors::Error::JavaException);
        }
    };
    Ok(env.new_string(s)?.into_raw())
}

/// Throw a Java RuntimeException with the given message.
fn throw_runtime_exception(env: &mut JNIEnv, msg: &str) {
    // Preserve an existing JNI exception (e.g. path encoding or OutOfMemoryError).
    if !env.exception_check().unwrap_or(true) {
        let _ = env.throw_new("java/lang/RuntimeException", msg);
    }
}

/// Wrapper that catches panics and converts them to Java exceptions.
fn catch_panic_and_throw<F, T>(env: &mut JNIEnv, fallback: T, f: F) -> T
where
    F: FnOnce(&mut JNIEnv) -> T + std::panic::UnwindSafe,
{
    let env_ptr = env as *mut JNIEnv;
    match std::panic::catch_unwind(|| {
        let env = unsafe { &mut *env_ptr };
        if ensure_clean(env).is_err() {
            return None;
        }
        Some(f(env))
    }) {
        Ok(Some(result)) => result,
        Ok(None) => fallback,
        Err(panic_info) => {
            // Guard error formatting/JNI reporting too. A reporting panic must
            // not unwind across the exported JNI system ABI or replace a primary.
            let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                let msg = if let Some(s) = panic_info.downcast_ref::<&str>() {
                    format!("Native panic: {}", s)
                } else if let Some(s) = panic_info.downcast_ref::<String>() {
                    format!("Native panic: {}", s)
                } else {
                    "Native panic: unknown error".to_string()
                };
                throw_runtime_exception(env, &msg);
            }));
            fallback
        }
    }
}

/// Only outer create/show/destroy entries may drain. The retain callback must
/// use the plain panic wrapper while the JDK resource read lock is still held.
/// An Err/panic skips exit cleanup even if Throw itself failed: the logical
/// primary is not replaced by a later cleanup exception.
fn picker_entry<F, T>(env: &mut JNIEnv, fallback: T, f: F) -> T
where
    F: FnOnce(&mut JNIEnv) -> Result<T, ()> + std::panic::UnwindSafe,
{
    let result = catch_panic_and_throw(env, Err(()), |env| {
        // The common wrapper's pending guard has already run inside its panic
        // boundary. Only this explicit outer-picker closure admits any drain.
        #[cfg(target_os = "macos")]
        macos_parent::drain_pending_releases(env);
        ensure_clean(env).map_err(|_| ())?;
        match f(env) {
            Ok(value) => {
                ensure_clean(env).map_err(|_| ())?;
                // Closure locals (including the final Arc/parent owner) have
                // dropped. Only a successful clean result admits this pass.
                #[cfg(target_os = "macos")]
                macos_parent::drain_pending_releases(env);
                ensure_clean(env).map_err(|_| ())?;
                Ok(value)
            }
            Err(()) => Err(()),
        }
    });
    match result {
        Ok(value) => value,
        Err(()) => fallback,
    }
}

/// Report parsing/conversion failure, but preserve any original Java throwable.
fn picker_jni_failure(env: &mut JNIEnv, context: &str, error: jni::errors::Error) {
    throw_runtime_exception(env, &format!("{context}: {error}"));
}

// ---------------------------------------------------------------------------
// Parent window handle wrapper
// ---------------------------------------------------------------------------

/// A wrapper that implements HasWindowHandle + HasDisplayHandle for rfd::set_parent.
/// Constructed from a raw native window pointer passed from the JVM.
#[cfg(not(target_os = "macos"))]
struct ParentWindow {
    raw_window: RawWindowHandle,
    raw_display: RawDisplayHandle,
}

// Existing Windows/Linux assumptions remain UNVERIFIED under IO-023.
// macOS deliberately does NOT use these raw-handle Send/Sync assertions.
#[cfg(not(target_os = "macos"))]
unsafe impl Send for ParentWindow {}
#[cfg(not(target_os = "macos"))]
unsafe impl Sync for ParentWindow {}

#[cfg(not(target_os = "macos"))]
impl HasWindowHandle for ParentWindow {
    fn window_handle(&self) -> Result<raw_window_handle::WindowHandle<'_>, HandleError> {
        // Safety: The raw handle is valid for the lifetime of this struct.
        Ok(unsafe { raw_window_handle::WindowHandle::borrow_raw(self.raw_window) })
    }
}

#[cfg(not(target_os = "macos"))]
impl HasDisplayHandle for ParentWindow {
    fn display_handle(&self) -> Result<raw_window_handle::DisplayHandle<'_>, HandleError> {
        // Safety: The raw handle is valid for the lifetime of this struct.
        Ok(unsafe { raw_window_handle::DisplayHandle::borrow_raw(self.raw_display) })
    }
}

#[cfg(not(target_os = "macos"))]
impl ParentWindow {
    /// Create a ParentWindow from a native window pointer.
    /// Returns None if the pointer is 0 (no parent).
    fn from_raw_ptr(ptr: jlong) -> Option<Self> {
        if ptr == 0 {
            return None;
        }

        #[cfg(target_os = "windows")]
        {
            use raw_window_handle::{Win32WindowHandle, WindowsDisplayHandle};
            let mut handle =
                Win32WindowHandle::new(unsafe { std::num::NonZero::new_unchecked(ptr as isize) });
            let raw_window = RawWindowHandle::Win32(handle);
            let raw_display = RawDisplayHandle::Windows(WindowsDisplayHandle::new());
            Some(ParentWindow {
                raw_window,
                raw_display,
            })
        }

        #[cfg(target_os = "linux")]
        {
            // On Linux, rfd uses GTK which manages its own display connection.
            // The parent window hint is best-effort - GTK may ignore it
            // if the display handle does not match its internal connection.
            // The Window ID is still useful for focus/stacking behavior.
            use raw_window_handle::{XlibDisplayHandle, XlibWindowHandle};
            let raw_window = RawWindowHandle::Xlib(XlibWindowHandle::new(ptr as u64));
            let raw_display = RawDisplayHandle::Xlib(XlibDisplayHandle::new(None, 0));
            Some(ParentWindow {
                raw_window,
                raw_display,
            })
        }

        #[cfg(not(any(target_os = "macos", target_os = "windows", target_os = "linux")))]
        {
            None
        }
    }
}

/// Legacy numeric parent ABI is retained, but cannot establish macOS ownership.
fn legacy_parent(
    env: &mut JNIEnv,
    pointer: jlong,
) -> Result<Option<ParentWindow>, jni::errors::Error> {
    ensure_clean(env)?;
    #[cfg(target_os = "macos")]
    {
        if pointer != 0 {
            env.throw_new(
                "java/lang/UnsupportedOperationException",
                "A macOS parent requires the owned AWT-parent JNI capability, not a raw pointer",
            )?;
            return Err(jni::errors::Error::JavaException);
        }
        Ok(None)
    }
    #[cfg(not(target_os = "macos"))]
    {
        let _ = env;
        Ok(ParentWindow::from_raw_ptr(pointer))
    }
}

// ---------------------------------------------------------------------------
// Stored dialog configuration
// ---------------------------------------------------------------------------

/// The type of dialog to show.
enum DialogKind {
    PickFiles { multiple: bool },
    PickDirectory,
    SaveFile { default_name: Option<String> },
}

/// Stores dialog configuration so it can be reused across multiple show() calls.
struct DialogConfig {
    kind: DialogKind,
    title: Option<String>,
    initial_directory: Option<String>,
    extensions: Vec<String>,
    parent: Option<ParentWindow>,
}

impl DialogConfig {
    /// Build a fresh FileDialog from this stored config.
    fn build(&self) -> FileDialog {
        let mut dialog = FileDialog::new();
        // Test-only barrier inside the real builder; production has no hook or branch.
        #[cfg(test)]
        ownership_tests::pause_build_if_requested();

        if let Some(ref t) = self.title {
            dialog = dialog.set_title(t);
        }

        if let Some(ref dir) = self.initial_directory {
            dialog = dialog.set_directory(dir);
        }

        if !self.extensions.is_empty() {
            let ext_refs: Vec<&str> = self.extensions.iter().map(|s| s.as_str()).collect();
            dialog = dialog.add_filter("Selected types", &ext_refs);
        }

        if let DialogKind::SaveFile {
            default_name: Some(ref name),
        } = self.kind
        {
            dialog = dialog.set_file_name(name);
        }

        #[cfg(not(target_os = "macos"))]
        if let Some(ref parent) = self.parent {
            dialog = dialog.set_parent(parent);
        }

        dialog
    }

    /// Only current call sites return owned path data; a parent-bound dialog
    /// is constructed and synchronously shown inside the same AppKit scope.
    fn with_built_dialog<T: Send>(
        &self,
        _env: &mut JNIEnv,
        show: impl FnOnce(FileDialog) -> T + Send,
    ) -> Result<T, ()> {
        ensure_clean(_env).map_err(|error| {
            picker_jni_failure(_env, "Native dialog worker is not clean", error)
        })?;
        #[cfg(target_os = "macos")]
        if let Some(parent) = &self.parent {
            return match parent.with_parent(_env, |borrow| show(self.build().set_parent(borrow))) {
                Ok(result) => Ok(result),
                Err(error) => {
                    let _ = error.throw(_env);
                    Err(())
                }
            };
        }
        // Explicitly absent parent preserves the existing rfd path. Requested
        // but unavailable parents never reach this branch: creation throws.
        Ok(show(self.build()))
    }
}

// Config IDs are not addresses and are never recycled. A show clones its Arc under the lock.
fn configs() -> &'static Registry<DialogConfig> {
    static CONFIGS: OnceLock<Registry<DialogConfig>> = OnceLock::new();
    CONFIGS.get_or_init(Registry::new)
}

fn register_config(env: &mut JNIEnv, config: DialogConfig) -> Result<jlong, ()> {
    ensure_clean(env)
        .map_err(|error| picker_jni_failure(env, "Native dialog creation refused", error))?;
    match configs().insert(config) {
        Ok(handle) => Ok(handle),
        Err(message) => {
            throw_runtime_exception(env, message);
            Err(())
        }
    }
}

fn lease_config(env: &mut JNIEnv, handle: jlong) -> Result<Arc<DialogConfig>, ()> {
    ensure_clean(env)
        .map_err(|error| picker_jni_failure(env, "Native dialog show refused", error))?;
    match configs().lease(handle) {
        Ok(config) => Ok(config),
        Err(message) => {
            throw_runtime_exception(env, message);
            Err(())
        }
    }
}

// ---------------------------------------------------------------------------
// JNI exports
// ---------------------------------------------------------------------------

/// No-op — forces the native library to load.
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_init(
    _env: JNIEnv,
    _class: JClass,
) {
}

/// Non-GUI ABI handshake for both bundled and explicitly trusted external libraries.
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_abiVersion(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    1
}

/// Create a file picker dialog config with optional parent window handle.
///
/// Signature: (Ljava/lang/String;Ljava/lang/String;[Ljava/lang/String;ZJ)J
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_createFileDialog(
    mut env: JNIEnv,
    _class: JClass,
    title: JString,
    initial_directory: JString,
    extensions: JObjectArray,
    multiple: jboolean,
    parent_window: jlong,
) -> jlong {
    picker_entry(&mut env, 0, |env| {
        let title = jstring_to_string(env, &title)
            .map_err(|error| picker_jni_failure(env, "Native title parsing failed", error))?;
        let initial_directory = jstring_to_string(env, &initial_directory)
            .map_err(|error| picker_jni_failure(env, "Native directory parsing failed", error))?;
        let extensions = jstring_array_to_vec(env, &extensions)
            .map_err(|error| picker_jni_failure(env, "Native filter parsing failed", error))?;
        let parent = legacy_parent(env, parent_window)
            .map_err(|error| picker_jni_failure(env, "Native parent creation failed", error))?;
        let config = DialogConfig {
            kind: DialogKind::PickFiles {
                multiple: multiple == JNI_TRUE,
            },
            title,
            initial_directory,
            extensions,
            parent,
        };
        register_config(env, config)
    })
}

/// Create a directory picker dialog config with optional parent window handle.
///
/// Signature: (Ljava/lang/String;Ljava/lang/String;J)J
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_createDirectoryDialog(
    mut env: JNIEnv,
    _class: JClass,
    title: JString,
    initial_directory: JString,
    parent_window: jlong,
) -> jlong {
    picker_entry(&mut env, 0, |env| {
        let title = jstring_to_string(env, &title)
            .map_err(|error| picker_jni_failure(env, "Native title parsing failed", error))?;
        let initial_directory = jstring_to_string(env, &initial_directory)
            .map_err(|error| picker_jni_failure(env, "Native directory parsing failed", error))?;
        let parent = legacy_parent(env, parent_window)
            .map_err(|error| picker_jni_failure(env, "Native parent creation failed", error))?;
        let config = DialogConfig {
            kind: DialogKind::PickDirectory,
            title,
            initial_directory,
            extensions: Vec::new(),
            parent,
        };
        register_config(env, config)
    })
}

/// Create a save-file dialog config with optional parent window handle.
///
/// Signature: (Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)J
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_createSaveDialog(
    mut env: JNIEnv,
    _class: JClass,
    title: JString,
    initial_directory: JString,
    default_name: JString,
    extension: JString,
    parent_window: jlong,
) -> jlong {
    picker_entry(&mut env, 0, |env| {
        let title = jstring_to_string(env, &title)
            .map_err(|error| picker_jni_failure(env, "Native title parsing failed", error))?;
        let initial_directory = jstring_to_string(env, &initial_directory)
            .map_err(|error| picker_jni_failure(env, "Native directory parsing failed", error))?;
        let default_name = jstring_to_string(env, &default_name)
            .map_err(|error| picker_jni_failure(env, "Native default name parsing failed", error))?;
        let extension = jstring_to_string(env, &extension)
            .map_err(|error| picker_jni_failure(env, "Native extension parsing failed", error))?;
        let parent = legacy_parent(env, parent_window)
            .map_err(|error| picker_jni_failure(env, "Native parent creation failed", error))?;
        let config = DialogConfig {
            kind: DialogKind::SaveFile { default_name },
            title,
            initial_directory,
            extensions: extension.into_iter().filter(|e| !e.is_empty()).collect(),
            parent,
        };
        register_config(env, config)
    })
}

/// Additive feature handshake. Old ABI-1 payloads do not have this symbol.
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_macOsParentLeaseAbiVersion(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    if cfg!(target_os = "macos") {
        1
    } else {
        0
    }
}

/// Private additive JNI entry: actual Window, not a transferable raw Long.
/// Signature: (ILjava/lang/String;Ljava/lang/String;[Ljava/lang/String;ZLjava/lang/String;Ljava/awt/Window;)J
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_createDialogWithAwtParent(
    mut env: JNIEnv,
    class: JClass,
    kind: jint,
    title: JString,
    initial_directory: JString,
    extensions: JObjectArray,
    multiple: jboolean,
    default_name: JString,
    parent_window: JObject,
) -> jlong {
    picker_entry(&mut env, 0, |env| {
        #[cfg(target_os = "macos")]
        {
            if !matches!(kind, 0..=2) {
                let _ = env.throw_new(
                    "java/lang/IllegalArgumentException",
                    "Unsupported native dialog kind",
                );
                return Err(());
            }
            // Complete all fallible caller parsing BEFORE any parent borrow,
            // including save default_name and the optional filter array.
            let title = jstring_to_string(env, &title)
                .map_err(|error| picker_jni_failure(env, "Native title parsing failed", error))?;
            let initial_directory = jstring_to_string(env, &initial_directory)
                .map_err(|error| picker_jni_failure(env, "Native directory parsing failed", error))?;
            let extensions = jstring_array_to_vec(env, &extensions)
                .map_err(|error| picker_jni_failure(env, "Native filter parsing failed", error))?;
            let default_name = jstring_to_string(env, &default_name)
                .map_err(|error| picker_jni_failure(env, "Native default name parsing failed", error))?;
            let kind = match kind {
                0 => DialogKind::PickFiles {
                    multiple: multiple == JNI_TRUE,
                },
                1 => DialogKind::PickDirectory,
                2 => DialogKind::SaveFile { default_name },
                _ => unreachable!("dialog kind checked before parsing"),
            };
            let parent = match macos_parent::ParentLease::acquire(env, &class, &parent_window) {
                Ok(parent) => parent,
                Err(error) => {
                    let _ = error.throw(env);
                    return Err(());
                }
            };
            let config = DialogConfig {
                kind,
                title,
                initial_directory,
                extensions,
                parent: Some(parent),
            };
            register_config(env, config)
        }
        #[cfg(not(target_os = "macos"))]
        {
            let _ = (
                class,
                kind,
                title,
                initial_directory,
                extensions,
                multiple,
                default_name,
                parent_window,
            );
            let _ = env.throw_new(
                "java/lang/UnsupportedOperationException",
                "Owned AWT parenting is macOS-only",
            );
            Err(())
        }
    })
}

/// Called by the exact one-shot CFNativeAction during execute's read lock.
/// Signature: (JJ)V
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_retainMacOsParent(
    mut env: JNIEnv,
    _class: JClass,
    ticket: jlong,
    pointer: jlong,
) {
    catch_panic_and_throw(&mut env, (), |env| {
        #[cfg(target_os = "macos")]
        macos_parent::retain_under_borrow(env, ticket, pointer);
        #[cfg(not(target_os = "macos"))]
        {
            let _ = (ticket, pointer);
            let _ = env.throw_new(
                "java/lang/UnsupportedOperationException",
                "Owned AWT parenting is macOS-only",
            );
        }
    })
}

/// Show a previously created dialog. Returns file paths (pick), directory (pick dir), or save path.
///
/// For file picker: returns String[]
/// Signature: (J)[Ljava/lang/String;
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_showFileDialog(
    mut env: JNIEnv,
    _class: JClass,
    handle: jlong,
) -> jobjectArray {
    picker_entry(&mut env, std::ptr::null_mut(), |env| {
        let config = lease_config(env, handle)?;
        let paths = config.with_built_dialog(env, |dialog| match &config.kind {
            DialogKind::PickFiles { multiple: true } => dialog.pick_files().unwrap_or_default(),
            DialogKind::PickFiles { multiple: false } => dialog.pick_file().into_iter().collect(),
            _ => Vec::new(),
        })?;

        match paths_to_jstring_array(env, &paths) {
            Ok(arr) => Ok(arr),
            Err(e) => {
                throw_runtime_exception(env, &format!("Failed to create result array: {}", e));
                Err(())
            }
        }
    })
}

/// Show a previously created directory dialog. Returns the path or null.
///
/// Signature: (J)Ljava/lang/String;
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_showDirectoryDialog(
    mut env: JNIEnv,
    _class: JClass,
    handle: jlong,
) -> jstring {
    picker_entry(&mut env, std::ptr::null_mut(), |env| {
        let config = lease_config(env, handle)?;
        let path = config.with_built_dialog(env, |dialog| dialog.pick_folder())?;
        match path {
            Some(path) => path_to_jstring(env, &path)
                .map_err(|error| picker_jni_failure(env, "Native directory result failed", error)),
            None => Ok(std::ptr::null_mut()),
        }
    })
}

/// Show a previously created save dialog. Returns the path or null.
///
/// Signature: (J)Ljava/lang/String;
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_showSaveDialog(
    mut env: JNIEnv,
    _class: JClass,
    handle: jlong,
) -> jstring {
    picker_entry(&mut env, std::ptr::null_mut(), |env| {
        let config = lease_config(env, handle)?;
        let path = config.with_built_dialog(env, |dialog| dialog.save_file())?;
        match path {
            Some(path) => path_to_jstring(env, &path)
                .map_err(|error| picker_jni_failure(env, "Native save result failed", error)),
            None => Ok(std::ptr::null_mut()),
        }
    })
}

/// Close an opaque configuration ID. In-flight show leases keep their config alive.
///
/// Signature: (J)V
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_destroyDialog(
    mut env: JNIEnv,
    _class: JClass,
    handle: jlong,
) {
    picker_entry(&mut env, (), |env| {
        configs()
            .close(handle)
            .map_err(|message| throw_runtime_exception(env, message))?;
        Ok(())
    })
}

#[cfg(test)]
mod ownership_tests {
    use super::{DialogConfig, DialogKind, Registry};
    use std::cell::RefCell;
    use std::sync::{Arc, Barrier};

    thread_local! {
        static BUILD_GATE: RefCell<Option<(Arc<Barrier>, Arc<Barrier>)>> = const { RefCell::new(None) };
    }

    pub(super) fn pause_build_if_requested() {
        let gate = BUILD_GATE.with(|slot| slot.borrow_mut().take());
        if let Some((entered, resume)) = gate {
            entered.wait();
            resume.wait();
        }
    }

    fn config(kind: DialogKind) -> DialogConfig {
        DialogConfig {
            kind,
            title: Some("Résumé 研究 😀".into()),
            initial_directory: Some("/not-opened/nativecmpkit".into()),
            extensions: vec!["png".into(), "heic".into(), "txt".into()],
            parent: None,
        }
    }

    #[test]
    fn close_during_actual_dialog_build_preserves_lease_until_builder_returns() {
        let registry = Arc::new(Registry::new());
        let id = registry
            .insert(config(DialogKind::SaveFile {
                default_name: Some("研究 😀.txt".into()),
            }))
            .unwrap();
        let weak = Arc::downgrade(&registry.lease(id).unwrap());
        let entered = Arc::new(Barrier::new(2));
        let resume = Arc::new(Barrier::new(2));
        let worker = {
            let registry = registry.clone();
            let entered = entered.clone();
            let resume = resume.clone();
            std::thread::spawn(move || {
                let lease = registry.lease(id).unwrap();
                BUILD_GATE.with(|slot| *slot.borrow_mut() = Some((entered, resume)));
                // The production builder pauses after FileDialog::new, before reading
                // borrowed strings/filter/name. The other thread closes its registry ID.
                let dialog = lease.build();
                assert_eq!(lease.title.as_deref(), Some("Résumé 研究 😀"));
                assert_eq!(lease.extensions, ["png", "heic", "txt"]);
                assert!(
                    matches!(&lease.kind, DialogKind::SaveFile { default_name: Some(name) } if name == "研究 😀.txt")
                );
                drop(dialog);
                drop(lease);
            })
        };
        entered.wait();
        registry.close(id).unwrap();
        registry.close(id).unwrap();
        assert!(registry.lease(id).is_err());
        assert_eq!(
            weak.strong_count(),
            1,
            "Only the in-flight native build owns the configuration"
        );
        resume.wait();
        worker.join().unwrap();
        assert!(
            weak.upgrade().is_none(),
            "The actual configuration is freed after build returns"
        );
    }

    #[test]
    fn all_actual_configuration_kinds_are_freed_after_repeated_no_parent_builds() {
        let registry = Registry::new();
        let mut previous = 0;
        for round in 0..128 {
            let kind = match round % 4 {
                0 => DialogKind::PickFiles { multiple: false },
                1 => DialogKind::PickFiles { multiple: true },
                2 => DialogKind::PickDirectory,
                _ => DialogKind::SaveFile {
                    default_name: Some("Résumé 研究 😀.txt".into()),
                },
            };
            let id = registry.insert(config(kind)).unwrap();
            assert!(
                id > previous,
                "Opaque IDs must never alias an earlier freed configuration"
            );
            previous = id;
            let lease = registry.lease(id).unwrap();
            let weak = Arc::downgrade(&lease);
            drop(lease.build());
            registry.close(id).unwrap();
            registry.close(id).unwrap();
            assert!(registry.lease(id).is_err());
            // A held lease remains usable, with no raw parent or OS dialog opened.
            drop(lease.build());
            drop(lease);
            assert_eq!(weak.strong_count(), 0);
            assert!(weak.upgrade().is_none());
        }
    }
}
