"""Fixed same-checkout serial batches; original finite profiles remain available."""

BATCHES = {
    "android-io-permission-storage-api35": (
        "android-io-reference-regressions", "android-permission-demo",
        "android-storage-api35-normal", "android-storage-api35-all-files",
    ),
    "android-permission-storage-api35-recovery": (
        "android-permission-demo", "android-storage-api35-normal", "android-storage-api35-all-files",
    ),
    "android-permission-storage-compatibility": (
        "android-media-selection-api33", "android-media-selection-api34",
        "android-storage-api28", "android-storage-api29-target28",
        "android-storage-api29-legacy", "android-storage-api29-scoped",
        "android-storage-api30-normal", "android-storage-api30-all-files",
    ),
    "android-media-selection-compatibility": (
        "android-media-selection-api33", "android-media-selection-api34",
    ),
    "android-storage-compatibility": (
        "android-storage-api28", "android-storage-api29-target28",
        "android-storage-api29-legacy", "android-storage-api29-scoped",
        "android-storage-api30-normal", "android-storage-api30-all-files",
    ),
}
SELECTIONS = {
    "android-io-reference-regressions": (35, "calf-io", "android-io-reference-regressions"),
    "android-permission-demo": (35, "calf-permissions/core", "android-permission-demo-contracts"),
    "android-storage-api35-normal": (35, "calf-permissions/core", "android-storage-api35-normal"),
    "android-storage-api35-all-files": (35, "calf-permissions/core", "android-storage-api35-all-files"),
    "android-media-selection-api33": (33, "calf-permissions/core", "android-media-selection"),
    "android-media-selection-api34": (34, "calf-permissions/core", "android-media-selection"),
    "android-storage-api28": (28, "calf-permissions/core", "android-storage-api28"),
    "android-storage-api29-target28": (29, "calf-permissions/core", "android-storage-api29-target28"),
    "android-storage-api29-legacy": (29, "calf-permissions/core", "android-storage-api29-legacy"),
    "android-storage-api29-scoped": (29, "calf-permissions/core", "android-storage-api29-scoped"),
    "android-storage-api30-normal": (30, "calf-permissions/core", "android-storage-api30-normal"),
    "android-storage-api30-all-files": (30, "calf-permissions/core", "android-storage-api30-all-files"),
}
MODULES = {
    "android-io-permission-storage-api35": "calf-io,calf-permissions/core",
    "android-permission-storage-api35-recovery": "calf-permissions/core",
    "android-permission-storage-compatibility": "calf-permissions/core",
    "android-media-selection-compatibility": "calf-permissions/core",
    "android-storage-compatibility": "calf-permissions/core",
}
SLOTS = {
    "android-io-permission-storage-api35": "android-device-batch-api35",
    "android-permission-storage-api35-recovery": "android-device-batch-permission-storage-api35-recovery",
    "android-permission-storage-compatibility": "android-device-batch-compatibility",
    "android-media-selection-compatibility": "android-device-batch-media-compatibility",
    "android-storage-compatibility": "android-device-batch-storage-compatibility",
}
SDK_PACKAGES = {
    "android-io-permission-storage-api35": "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64",
    "android-permission-storage-api35-recovery": "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-35;google_apis;x86_64",
    "android-permission-storage-compatibility": "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-28;google_apis;x86_64 system-images;android-29;google_apis;x86_64 system-images;android-30;google_apis;x86_64 system-images;android-33;google_apis;x86_64 system-images;android-34;google_apis;x86_64",
    "android-media-selection-compatibility": "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-33;google_apis;x86_64 system-images;android-34;google_apis;x86_64",
    "android-storage-compatibility": "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-28;google_apis;x86_64 system-images;android-29;google_apis;x86_64 system-images;android-30;google_apis;x86_64",
}
