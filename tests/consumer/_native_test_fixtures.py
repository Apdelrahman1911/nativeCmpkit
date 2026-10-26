"""Synthetic sanitized graph fixture. This is not Cargo/build evidence."""
from verify_artifacts import NATIVE_CRATE_NAMES, NATIVE_METADATA_SCOPE


def metadata_fixture(module="calf-file-picker", checksum="3" * 64,
                     manifest_hash="1" * 64, lock_hash="2" * 64):
    root = NATIVE_CRATE_NAMES[module]
    return {
        "schema_version": 1, "module": module, "target_filter": None,
        "scope": NATIVE_METADATA_SCOPE,
        "cargo_toml_sha256": manifest_hash, "cargo_lock_sha256": lock_hash,
        "packages": [
            {"id": "example@1.0.0", "name": "example", "version": "1.0.0", "source_kind": "crates.io",
             "license": "MIT", "checksum": checksum, "license_file": None},
            {"id": root + "@0.1.0", "name": root, "version": "0.1.0", "source_kind": "local-root",
             "license": "Apache-2.0", "checksum": None, "license_file": None},
        ],
        "resolve": [
            {"id": root + "@0.1.0", "dependencies": ["example@1.0.0"]},
            {"id": "example@1.0.0", "dependencies": []},
        ],
    }
