// NativeCmpKit test-only JNI versions; never packaged in library artifacts.
#![no_std]
use core::ffi::c_void;
#[panic_handler]
fn panic(_: &core::panic::PanicInfo<'_>) -> ! { loop {} }
#[cfg(fixture_v1)]
const VERSION: i32 = 1;
#[cfg(fixture_v2)]
const VERSION: i32 = 2;
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeCacheProcessPayload_version(
    _environment: *mut c_void, _class: *mut c_void,
) -> i32 { VERSION }
