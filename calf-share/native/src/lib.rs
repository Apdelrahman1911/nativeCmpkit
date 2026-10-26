// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
#[cfg(target_os = "macos")]
mod macos;
#[cfg_attr(not(any(target_os = "macos", test)), allow(dead_code))]
mod operation;

use jni::objects::{JClass, JObjectArray, JString};
use jni::sys::{jboolean, jint, jlong, JNI_FALSE};
use jni::JNIEnv;
use operation::{Registry, UNAVAILABLE};
use std::sync::{Mutex, OnceLock};

static REGISTRY: OnceLock<Mutex<Registry>> = OnceLock::new();
fn registry() -> std::sync::MutexGuard<'static, Registry> {
    REGISTRY
        .get_or_init(|| Mutex::new(Registry::default()))
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_init(
    _env: JNIEnv,
    _class: JClass,
) {
}
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_abiVersion(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    1
}
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_isNativeShareSupported(
    _env: JNIEnv,
    _class: JClass,
) -> jboolean {
    #[cfg(target_os = "macos")]
    {
        if macos::is_supported() {
            jni::sys::JNI_TRUE
        } else {
            JNI_FALSE
        }
    }
    #[cfg(not(target_os = "macos"))]
    {
        JNI_FALSE
    }
}

#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_beginShareSheet(
    mut env: JNIEnv,
    _class: JClass,
    text: JString,
    url: JString,
    file_paths: JObjectArray,
    subject: JString,
    parent_window: jlong,
) -> jlong {
    let data = read_inputs(&mut env, &text, &url, &file_paths, &subject);
    match data {
        Some(data) => begin_share(data, parent_window),
        None => 0,
    }
}
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_takeShareResult(
    _env: JNIEnv,
    _class: JClass,
    id: jlong,
) -> jint {
    registry().take(id)
}
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_cancelShare(
    _env: JNIEnv,
    _class: JClass,
    id: jlong,
) {
    cancel_share(id);
}
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_activeRequestCount(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    registry().len() as jint
}
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_liveUiOperationCount(
    _env: JNIEnv,
    _class: JClass,
) -> jint {
    #[cfg(target_os = "macos")]
    {
        macos::live_count() as jint
    }
    #[cfg(not(target_os = "macos"))]
    {
        0
    }
}

/// ABI-compatible legacy adapter. New Kotlin code uses nonblocking begin/take/cancel. The adapter
/// never blocks AppKit Main and has one absolute deadline, rather than restarting a Condvar timeout.
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_share_platform_NativeShareBridge_showShareSheet(
    mut env: JNIEnv,
    _class: JClass,
    text: JString,
    url: JString,
    file_paths: JObjectArray,
    parent_window: jlong,
) -> jint {
    #[cfg(target_os = "macos")]
    if objc2::MainThreadMarker::new().is_some() {
        return UNAVAILABLE;
    }
    let empty_subject = JString::default();
    let Some(data) = read_inputs(&mut env, &text, &url, &file_paths, &empty_subject) else {
        return UNAVAILABLE;
    };
    let id = begin_share(data, parent_window);
    if id <= 0 {
        return UNAVAILABLE;
    }
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(300);
    loop {
        let result = registry().take(id);
        if result != operation::PENDING {
            return result;
        }
        if std::time::Instant::now() >= deadline {
            cancel_share(id);
            return operation::FAILED;
        }
        std::thread::sleep(std::time::Duration::from_millis(25));
    }
}

#[cfg_attr(not(target_os = "macos"), allow(dead_code))]
struct ShareData {
    text: Option<String>,
    url: Option<String>,
    paths: Vec<String>,
    subject: Option<String>,
}
fn read_optional_string(env: &mut JNIEnv, input: &JString) -> Result<Option<String>, ()> {
    if input.is_null() {
        Ok(None)
    } else {
        env.get_string(input)
            .map(|s| Some(s.into()))
            .map_err(|_| ())
    }
}
fn read_inputs(
    env: &mut JNIEnv,
    text: &JString,
    url: &JString,
    paths: &JObjectArray,
    subject: &JString,
) -> Option<ShareData> {
    let text = read_optional_string(env, text).ok()?;
    let url = read_optional_string(env, url).ok()?;
    let subject = read_optional_string(env, subject).ok()?;
    let mut output = Vec::new();
    if !paths.is_null() {
        let len = env.get_array_length(paths).ok()?;
        for index in 0..len {
            let value = JString::from(env.get_object_array_element(paths, index).ok()?);
            let result = read_optional_string(env, &value);
            let _ = env.delete_local_ref(value);
            output.push(result.ok()??);
        }
    }
    Some(ShareData {
        text,
        url,
        paths: output,
        subject,
    })
}

fn begin_share(data: ShareData, parent_window: jlong) -> jlong {
    // Arbitrary borrowed NSWindow addresses cannot be safely retained after asynchronous dispatch.
    // ABI parameter is retained, but only focused-window ownership (0) is currently supported.
    if parent_window != 0 {
        return 0;
    }
    #[cfg(target_os = "macos")]
    {
        if data.text.is_none() && data.url.is_none() && data.paths.is_empty() {
            return 0;
        }
        let Some((id, completion)) = registry().begin() else {
            return -1;
        };
        macos::present(id, completion, data);
        id
    }
    #[cfg(not(target_os = "macos"))]
    {
        let _ = data;
        0
    }
}
fn cancel_share(id: i64) {
    if id <= 0 {
        return;
    }
    registry().cancel(id);
    #[cfg(target_os = "macos")]
    macos::cancel(id);
    #[cfg(not(target_os = "macos"))]
    registry().finish(id, operation::DISMISSED);
}
