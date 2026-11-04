// Compiles the actual JNI/registry/AppKit implementation, not a replacement lifetime model.
include!("../src/lib.rs");

#[cfg(target_os = "macos")]
fn main() {
    macos::lifecycle_tests::run();
}

#[cfg(not(target_os = "macos"))]
fn main() {
    eprintln!("AppKit lifecycle verification requires a real macOS graphical host; this is not N/A or a native pass");
    std::process::exit(2);
}
