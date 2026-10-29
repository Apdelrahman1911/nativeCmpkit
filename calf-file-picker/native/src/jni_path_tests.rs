//! Actual JVM/JNI conversions, never a fake Java environment.
//! The selected-path boundary is driven directly, not by an OS picker or UI automation.
//! Linux negative cases use real invalid-byte entries. macOS first verifies its
//! EILSEQ filesystem boundary, then explicitly uses controlled unrepresentable
//! PathBuf inputs with real valid peers; these are not actual selected files.
use super::{path_to_jstring, paths_to_jstring_array};
use jni::objects::{GlobalRef, JObject, JObjectArray, JString, JValue};
use jni::{InitArgsBuilder, JNIEnv, JNIVersion, JavaVM};
use std::cell::RefCell;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::OnceLock;

static VM: OnceLock<JavaVM> = OnceLock::new();
static NEXT: AtomicUsize = AtomicUsize::new(1);
thread_local! {
    static ARRAY_OBSERVER: RefCell<Option<Vec<GlobalRef>>> = const { RefCell::new(None) };
}

fn vm() -> &'static JavaVM {
    VM.get_or_init(|| {
        let args = InitArgsBuilder::new()
            .version(JNIVersion::V8)
            .option("-Xcheck:jni")
            .option("-Xmx64m")
            .option("-Djava.awt.headless=true")
            .build()
            .unwrap();
        let vm = JavaVM::new(args).expect("A genuine installed JVM is required; no skip or JNI substitute");
        {
            let mut env = vm.attach_current_thread().unwrap();
            env.with_local_frame(16, |env| -> jni::errors::Result<()> {
                let key = env.new_string("java.specification.version")?;
                let value = env.call_static_method("java/lang/System", "getProperty", "(Ljava/lang/String;)Ljava/lang/String;", &[JValue::Object(key.as_ref())])?.l()?;
                let version = java_string(env, JString::from(value));
                assert_eq!(version, "17", "Actual JNI verification must run in JDK17, not only a configured launcher");
                println!("NATIVECMPKIT_ACTUAL_PATH_JVM major={version} checked_jni=true real_filesystem=true");
                Ok(())
            }).unwrap();
        }
        vm
    })
}

struct OwnedDirectory(PathBuf);
impl OwnedDirectory {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "nativecmpkit-jni-paths-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::SeqCst)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
    fn file(&self, name: &str, bytes: &[u8]) -> PathBuf {
        let path = self.0.join(name);
        std::fs::write(&path, bytes).unwrap();
        path
    }
    #[cfg(target_os = "linux")]
    fn invalid(&self, directory: bool) -> PathBuf {
        use std::os::unix::ffi::OsStringExt;
        let path = self
            .0
            .join(std::ffi::OsString::from_vec(b"selected-\xff.txt".to_vec()));
        if directory {
            std::fs::create_dir(&path).unwrap();
        } else {
            std::fs::write(&path, b"owned-invalid-byte-content").unwrap();
        }
        path
    }
}
impl Drop for OwnedDirectory {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0)
            .expect("Remove only the successfully created owned fixture");
    }
}

fn java_string(env: &mut JNIEnv, value: JString) -> String {
    env.get_string(&value).unwrap().into()
}

fn assert_io_exception(env: &mut JNIEnv) {
    assert!(env.exception_check().unwrap());
    let failure = env.exception_occurred().unwrap();
    env.exception_clear().unwrap(); // Do not perform ordinary JNI operations while pending.
    assert!(env.is_instance_of(&failure, "java/io/IOException").unwrap());
    env.delete_local_ref(failure).unwrap();
    assert!(!env.exception_check().unwrap());
}

pub(super) fn observe_array_if_requested(
    env: &mut JNIEnv,
    array: &JObjectArray,
) -> jni::errors::Result<()> {
    ARRAY_OBSERVER.with(|slot| {
        let mut slot = slot.borrow_mut();
        if let Some(ref mut references) = *slot {
            let weak = env.new_object(
                "java/lang/ref/WeakReference",
                "(Ljava/lang/Object;)V",
                &[JValue::Object(array.as_ref())],
            )?;
            references.push(env.new_global_ref(&weak)?); // Own the weak witness, never the array.
            env.delete_local_ref(weak)?;
        }
        Ok(())
    })
}

#[test]
fn actual_jni_keeps_non_ascii_and_supplementary_filename_bytes_exact() {
    let root = OwnedDirectory::new();
    let paths = [
        root.file("Résumé 研究 😀.txt", b"all valid Unicode"),
        root.file("space % #.txt", b"literal filename punctuation"),
    ];
    let mut env = vm().attach_current_thread().unwrap();
    env.with_local_frame(32, |env| -> jni::errors::Result<()> {
        let raw = paths_to_jstring_array(env, &paths)?;
        let array = unsafe { JObjectArray::from_raw(raw) };
        assert_eq!(env.get_array_length(&array)?, 2);
        for (index, path) in paths.iter().enumerate() {
            let value = JString::from(env.get_object_array_element(&array, index as i32)?);
            let returned = java_string(env, value);
            assert_eq!(Path::new(&returned), path);
            assert_eq!(
                std::fs::read(&returned).unwrap(),
                std::fs::read(path).unwrap()
            );
        }
        let raw = path_to_jstring(env, &paths[0]);
        assert!(!raw.is_null());
        assert_eq!(
            java_string(env, unsafe { JString::from_raw(raw) }),
            paths[0].to_str().unwrap()
        );
        assert!(!env.exception_check()?);
        Ok(())
    })
    .unwrap();
}

#[cfg(target_os = "linux")]
#[test]
fn actual_invalid_byte_file_is_rejected_without_selecting_its_replacement_character_peer() {
    let root = OwnedDirectory::new();
    let invalid = root.invalid(false);
    let peer = root.file("selected-�.txt", b"different replacement-character peer");
    assert_ne!(invalid, peer);
    assert!(invalid.is_file() && peer.is_file());
    assert_eq!(invalid.to_string_lossy(), peer.to_string_lossy());
    let mut env = vm().attach_current_thread().unwrap();
    env.with_local_frame(32, |env| -> jni::errors::Result<()> {
        assert!(matches!(
            paths_to_jstring_array(env, &[invalid.clone()]),
            Err(jni::errors::Error::JavaException)
        ));
        assert_io_exception(env);
        let raw = paths_to_jstring_array(env, &[peer.clone()])?;
        let array = unsafe { JObjectArray::from_raw(raw) };
        let value = JString::from(env.get_object_array_element(&array, 0)?);
        let returned = java_string(env, value);
        assert_eq!(Path::new(&returned), peer);
        assert_eq!(
            std::fs::read(&returned).unwrap(),
            b"different replacement-character peer"
        );
        Ok(())
    })
    .unwrap();
    assert_eq!(
        std::fs::read(invalid).unwrap(),
        b"owned-invalid-byte-content"
    );
}

#[cfg(target_os = "linux")]
#[test]
fn actual_directory_result_raises_io_exception_instead_of_returning_a_lossy_path() {
    let root = OwnedDirectory::new();
    let invalid = root.invalid(true);
    let mut env = vm().attach_current_thread().unwrap();
    env.with_local_frame(16, |env| -> jni::errors::Result<()> {
        assert!(path_to_jstring(env, &invalid).is_null());
        assert_io_exception(env);
        assert!(invalid.is_dir());
        Ok(())
    })
    .unwrap();
}

#[cfg(target_os = "linux")]
#[test]
fn actual_save_path_failure_does_not_open_or_overwrite_the_lossy_peer() {
    let root = OwnedDirectory::new();
    let invalid = root.invalid(false);
    let peer = root.file("selected-�.txt", b"must not be overwritten");
    let mut env = vm().attach_current_thread().unwrap();
    env.with_local_frame(16, |env| -> jni::errors::Result<()> {
        assert!(path_to_jstring(env, &invalid).is_null());
        assert_io_exception(env);
        Ok(())
    })
    .unwrap();
    assert_eq!(
        std::fs::read(invalid).unwrap(),
        b"owned-invalid-byte-content"
    );
    assert_eq!(std::fs::read(peer).unwrap(), b"must not be overwritten");
}

#[cfg(target_os = "linux")]
#[test]
fn repeated_mid_array_failure_releases_actual_jni_frame_arrays_and_clears_only_the_expected_error()
{
    let root = OwnedDirectory::new();
    let valid = root.file("valid 研究 😀.txt", b"valid prefix element");
    let invalid = root.invalid(false);
    let paths = [valid.clone(), valid, invalid];
    assert_mid_array_frame_cleanup(&paths);
}

#[cfg(any(target_os = "linux", target_os = "macos"))]
fn assert_mid_array_frame_cleanup(paths: &[PathBuf]) {
    let mut env = vm().attach_current_thread().unwrap();
    ARRAY_OBSERVER.with(|slot| *slot.borrow_mut() = Some(Vec::new()));
    for _ in 0..128 {
        env.with_local_frame(16, |env| -> jni::errors::Result<()> {
            assert!(matches!(
                paths_to_jstring_array(env, paths),
                Err(jni::errors::Error::JavaException)
            ));
            assert_io_exception(env);
            Ok(())
        })
        .unwrap(); // Mirror automatic cleanup at a real JNI native-method return.
    }
    let witnesses = ARRAY_OBSERVER.with(|slot| slot.borrow_mut().take().unwrap());
    assert_eq!(witnesses.len(), 128);
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(10);
    loop {
        env.call_static_method("java/lang/System", "gc", "()V", &[])
            .unwrap();
        let all_gone = env
            .with_local_frame(256, |env| -> jni::errors::Result<bool> {
                for weak in &witnesses {
                    let value = env
                        .call_method(weak.as_obj(), "get", "()Ljava/lang/Object;", &[])?
                        .l()?;
                    if !value.is_null() {
                        return Ok(false);
                    }
                }
                Ok(true)
            })
            .unwrap();
        if all_gone {
            break;
        }
        assert!(
            std::time::Instant::now() < deadline,
            "Failed actual arrays still have a strong JNI owner"
        );
        std::thread::sleep(std::time::Duration::from_millis(20));
    }
    assert!(!env.exception_check().unwrap());
    // Weak references alone must not be able to collect a deliberately live positive control.
    env.with_local_frame(16, |env| -> jni::errors::Result<()> {
        let control = env.new_object("java/lang/Object", "()V", &[])?;
        let retained = env.new_global_ref(&control)?;
        let weak = env.new_object(
            "java/lang/ref/WeakReference",
            "(Ljava/lang/Object;)V",
            &[JValue::Object(&control)],
        )?;
        env.call_static_method("java/lang/System", "gc", "()V", &[])?;
        let value: JObject = env
            .call_method(&weak, "get", "()Ljava/lang/Object;", &[])?
            .l()?;
        assert!(!value.is_null());
        drop(retained);
        Ok(())
    })
    .unwrap();
}

#[cfg(target_os = "macos")]
mod macos_domain {
    use super::*;
    use std::os::unix::ffi::OsStringExt;

    fn controlled_unrepresentable_path(root: &OwnedDirectory) -> PathBuf {
        root.0
            .join(std::ffi::OsString::from_vec(b"selected-\xff.txt".to_vec()))
    }

    fn controlled_marker(method: &str) {
        println!("NATIVECMPKIT_MACOS_JNI_CONTROLLED method={method} real_invalid_entry=false");
    }

    #[test]
    fn actual_macos_filesystem_rejects_invalid_file_and_directory_with_eilseq_before_jni() {
        let root = OwnedDirectory::new();
        let invalid = controlled_unrepresentable_path(&root);
        let peer = root.file("selected-�.txt", b"real peer must remain unchanged");
        assert!(invalid.to_str().is_none());
        assert_ne!(invalid, peer);
        assert_eq!(invalid.to_string_lossy(), peer.to_string_lossy());
        // Darwin EILSEQ is 92. This is a required actual filesystem result,
        // not an arbitrary error/skip waiver or a JNI failure.
        let file_error = std::fs::write(&invalid, b"must not create a lossy peer")
            .expect_err("This macOS filesystem must reject an invalid-byte file name");
        assert_eq!(file_error.raw_os_error(), Some(92));
        let directory_error = std::fs::create_dir(&invalid)
            .expect_err("This macOS filesystem must reject an invalid-byte directory name");
        assert_eq!(directory_error.raw_os_error(), Some(92));
        assert_eq!(
            std::fs::read(&peer).unwrap(),
            b"real peer must remain unchanged"
        );
        assert_eq!(std::fs::read_dir(&root.0).unwrap().count(), 1);
        println!("NATIVECMPKIT_MACOS_FILENAME_DOMAIN rejected_invalid_file=EILSEQ92 rejected_invalid_directory=EILSEQ92 peer_bytes_preserved=true");
    }

    #[test]
    fn controlled_unrepresentable_file_path_raises_io_exception_and_preserves_real_peer() {
        let root = OwnedDirectory::new();
        let invalid = controlled_unrepresentable_path(&root);
        let peer = root.file("selected-�.txt", b"real replacement-character peer");
        assert!(invalid.to_str().is_none());
        assert_eq!(invalid.to_string_lossy(), peer.to_string_lossy());
        let mut env = vm().attach_current_thread().unwrap();
        env.with_local_frame(32, |env| -> jni::errors::Result<()> {
            assert!(matches!(
                paths_to_jstring_array(env, &[invalid]),
                Err(jni::errors::Error::JavaException)
            ));
            assert_io_exception(env);
            let raw = paths_to_jstring_array(env, &[peer.clone()])?;
            let array = unsafe { JObjectArray::from_raw(raw) };
            let value = JString::from(env.get_object_array_element(&array, 0)?);
            let returned = java_string(env, value);
            assert_eq!(Path::new(&returned), peer);
            assert_eq!(
                std::fs::read(returned).unwrap(),
                b"real replacement-character peer"
            );
            Ok(())
        })
        .unwrap();
        controlled_marker(
            "controlled_unrepresentable_file_path_raises_io_exception_and_preserves_real_peer",
        );
    }

    #[test]
    fn controlled_unrepresentable_directory_path_raises_io_exception_before_path_transport() {
        let root = OwnedDirectory::new();
        let invalid = controlled_unrepresentable_path(&root);
        let peer = root.0.join("selected-�.txt");
        std::fs::create_dir(&peer).unwrap();
        let mut env = vm().attach_current_thread().unwrap();
        env.with_local_frame(16, |env| -> jni::errors::Result<()> {
            assert!(path_to_jstring(env, &invalid).is_null());
            assert_io_exception(env);
            let raw = path_to_jstring(env, &peer);
            assert!(!raw.is_null());
            assert_eq!(
                Path::new(&java_string(env, unsafe { JString::from_raw(raw) })),
                peer
            );
            assert!(peer.is_dir());
            assert!(!env.exception_check()?);
            Ok(())
        })
        .unwrap();
        controlled_marker(
            "controlled_unrepresentable_directory_path_raises_io_exception_before_path_transport",
        );
    }

    #[test]
    fn controlled_unrepresentable_save_path_never_overwrites_real_peer() {
        let root = OwnedDirectory::new();
        let invalid = controlled_unrepresentable_path(&root);
        let peer = root.file("selected-�.txt", b"real peer must not be overwritten");
        let mut env = vm().attach_current_thread().unwrap();
        env.with_local_frame(16, |env| -> jni::errors::Result<()> {
            assert!(path_to_jstring(env, &invalid).is_null());
            assert_io_exception(env);
            Ok(())
        })
        .unwrap();
        assert_eq!(
            std::fs::read(peer).unwrap(),
            b"real peer must not be overwritten"
        );
        controlled_marker("controlled_unrepresentable_save_path_never_overwrites_real_peer");
    }

    #[test]
    fn controlled_mid_array_failure_releases_actual_jni_frames_with_a_real_prefix() {
        let root = OwnedDirectory::new();
        let valid = root.file("valid 研究 😀.txt", b"real valid prefix");
        let invalid = controlled_unrepresentable_path(&root);
        assert_mid_array_frame_cleanup(&[valid.clone(), valid, invalid]);
        controlled_marker(
            "controlled_mid_array_failure_releases_actual_jni_frames_with_a_real_prefix",
        );
    }
}
