// NativeCmpKit test-only incompatible ABI2 image, never packaged in library artifacts.
#![no_std]
use core::ffi::c_void;
use core::sync::atomic::{AtomicUsize, Ordering};
#[panic_handler]
fn panic(_: &core::panic::PanicInfo<'_>) -> ! { loop {} }
static INIT_CALLS: AtomicUsize = AtomicUsize::new(0);
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_abiVersion(
    _: *mut c_void, _: *mut c_void,
) -> i32 { 2 }
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeFilePickerBridge_init(
    _: *mut c_void, _: *mut c_void,
) { INIT_CALLS.fetch_add(1, Ordering::SeqCst); }
#[no_mangle]
pub extern "system" fn Java_com_mohamedrejeb_calf_picker_platform_NativeRejectedAbiDiagnostics_initCalls(
    _: *mut c_void, _: *mut c_void,
) -> i32 { INIT_CALLS.load(Ordering::SeqCst) as i32 }
