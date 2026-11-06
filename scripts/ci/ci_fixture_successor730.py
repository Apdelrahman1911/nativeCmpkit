# SPDX-License-Identifier: Apache-2.0
"""One exact finite fixture successor; original740/742/current303 pins remain sealed.

No reconstructed source is imported, executed, written or enrolled as current.
"""
from __future__ import annotations

import hashlib
import json
import json.encoder
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/ci/ci_fixture_successor730.py"
CONTROL = "scripts/ci/test_ci_fixture_successor730.py"
SPEC = "scripts/ci/fixtures/ci-fixture-successor730-source-inverse.json"
SPEC_SHA256 = "cb91f33d96e0e3e4c79cd039b43346f1f7add10557f6dc8b4a8f79f83343bdda"
MAX_SOURCE = 4 * 1024 * 1024
MAX_SPEC = 512 * 1024
SCOPE = 'Exact six failed-producer742 fixture successors and their two owning routing sources/control above unchanged740742/raw301/current303; copied dependencies are never raw enrollment; source-only'
ORIGINALS = {'scripts/ci/fixtures/macos-share-ci668-composition.json': {'bytes': 518906, 'sha256': '06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24'}, 'scripts/ci/fixtures/ci-source-domain740-source-inverse.json': {'bytes': 36274, 'sha256': '5b450daf9874a62a4b452b0d6502c3a77426e670ec6fd79a6b1ed3a3aecf6e52'}, 'scripts/ci/fixtures/ci-source-recovery740-742-source-inverse.json': {'bytes': 209811, 'sha256': '2be8ac55c4253f303f0e93bd120b4277f9dc3b22c0b7ec209a452aebb3f59835'}}
BEFORE = {'scripts/ci/ci_source_recovery740_742.py': {'bytes': 20636, 'sha256': 'b891572937299dbf8ca1eef6327774d5b9076a9968b4304fd57ec65732edaab7'}, 'scripts/ci/macos_share_ci668_composition.py': {'bytes': 80011, 'sha256': 'fad15c34dbe4b4b91a347527c24e86a56a332fd5217b75aaee9dcdfed8d8670f'}, 'scripts/ci/test_android_io_remote_routing.py': {'bytes': 33865, 'sha256': 'e0e25800d691e4fc859f22d16c1ca4362da2bae36f80b76a3e976ddf35628018'}, 'scripts/ci/test_android_io_remote_routing_source_projection.py': {'bytes': 30209, 'sha256': '1ebc15e15b782b54411351116aff9fa070fde4190576643b78d34fa97023fb47'}, 'scripts/ci/test_camera_ios_ownership_source_projection.py': {'bytes': 15167, 'sha256': 'ab5f18af2709ca9eab5ccaff30249dd85e120aadf1c24068a72e448d7bd9e263'}, 'scripts/ci/test_camera_tooling562_source_projection.py': {'bytes': 7953, 'sha256': '73a402c49c93a29db3bb5d8a46ad20423b84a803b333cbc0ec1f717c6db21dbd'}, 'scripts/ci/test_camera_tooling566_source_projection.py': {'bytes': 9498, 'sha256': 'b5fb8f12b24df974931c5cb8c850afee8f9a1c103fdd4b01f742290ad7f346db'}, 'scripts/ci/test_ci_source_domain740.py': {'bytes': 16648, 'sha256': '2e6184cd259db9acd0148815dfc7890199b985aa7319e0415737361f3d233e5f'}, 'scripts/ci/test_ci_source_recovery740_742.py': {'bytes': 28844, 'sha256': 'b995929d6e6538631ff0b176bba281940bc41e8924e29c114214c35e497465c6'}}
FRAGMENT_COUNTS = {'scripts/ci/ci_source_recovery740_742.py': 5, 'scripts/ci/macos_share_ci668_composition.py': 4, 'scripts/ci/test_android_io_remote_routing.py': 2, 'scripts/ci/test_android_io_remote_routing_source_projection.py': 2, 'scripts/ci/test_camera_ios_ownership_source_projection.py': 2, 'scripts/ci/test_camera_tooling562_source_projection.py': 3, 'scripts/ci/test_camera_tooling566_source_projection.py': 4, 'scripts/ci/test_ci_source_domain740.py': 8, 'scripts/ci/test_ci_source_recovery740_742.py': 4}
FIXTURES = frozenset(('scripts/ci/test_android_io_remote_routing.py', 'scripts/ci/test_android_io_remote_routing_source_projection.py', 'scripts/ci/test_camera_ios_ownership_source_projection.py', 'scripts/ci/test_camera_tooling562_source_projection.py', 'scripts/ci/test_camera_tooling566_source_projection.py', 'scripts/ci/test_ci_source_domain740.py'))
RAW_FIXTURES = frozenset(('scripts/ci/test_android_io_remote_routing.py', 'scripts/ci/test_android_io_remote_routing_source_projection.py', 'scripts/ci/test_camera_tooling566_source_projection.py'))
CAPACITY = 'scripts/ci/offline_tooling_reuse.py'
CAPACITY_SCOPE = 'One exact existing raw301 producer-capacity734 row, two fixed copied NEW734 sources and one owning joint inventory tuple before the sealed r1 nine bindings; no raw301/current303 enrollment or generic layer search'
CAPACITY_BEFORE = {'bytes': 60138, 'sha256': '3f19d0f4e93a66b8ba4928e88819fb35ac469709f9c26bfef87ee57fbd4778ca'}
ROUTING = 'scripts/ci/macos_share_ci668_composition.py'
ROUTING_BEFORE = {'bytes': 80498, 'sha256': '1cf7d1faea1f053b9873ec175549745d0914c81f1246cb23754bd4357527f84a'}
COPIED734 = {'scripts/ci/offline_tooling_ci_parallel734.py': {'bytes': 15740, 'sha256': 'ace02723bb3c11cf1dd9fadf835df6b1a02b78ede07b3760de773080acdfdd34'}, 'scripts/ci/test_offline_tooling_ci_parallel734.py': {'bytes': 23853, 'sha256': 'b279fd83c9fcdac642878287a54767943016a5ca0a2c62e90c996d9e95aefe0f'}}
REMOTE = 'scripts/ci/android_io_remote_routing_source_projection.py'
REMOTE_BEFORE = {'bytes': 15979, 'sha256': 'da51c70226edceedddbc6176c8244680f1fa6a3350e7adab56fe6faf982c0cc0'}
BASE_MODIFIED = frozenset(BEFORE) | {CAPACITY, REMOTE}
ORDINARY_FIXTURE_SCOPE = 'Exact six owning ordinary-discovery fixture contexts above unchanged original730 bindings/current303: existing734 history peel, original711/620 comparison, exact ten commands, private worker socket bound and current-owner set; source-only, no deadline/output/native/trust/closure changes'
ORDINARY_FIXTURE_BEFORE = {'scripts/ci/test_offline_tooling_failure_evidence711.py': {'bytes': 15718, 'sha256': 'bb3ab2b5a7f5868aeef81de0d11dd8cd86224e332ebbd83b247a3738c18014f6'}, 'scripts/ci/test_offline_tooling_failure_inventory.py': {'bytes': 21208, 'sha256': '6c9db9a3b50b03a16aafe9065221151619361ecf797cbba4a4951e317913b4cb'}, 'scripts/ci/test_offline_tooling_failure_parent_ids658.py': {'bytes': 30925, 'sha256': '90d99f07e04381a34b8a542ec171154ffa1af4d9c3cc706ce7595bf0bc14016a'}, 'scripts/ci/test_offline_tooling_reuse.py': {'bytes': 49957, 'sha256': '6012ff90b004ec2631c17c05f65e116c88766d3089113a5ad2fee7a6e61ff94e'}, 'scripts/ci/test_desktop_media_context.py': {'bytes': 8892, 'sha256': '7f78bdc3071fca2726b6a422dde7a2a7f33fcdc013b1f13a6514b7600e369465'}, 'scripts/ci/test_ci_source_domain740.py': {'bytes': 22341, 'sha256': 'bb8138b08b105b74381018b7784063dd1c6174ebbcb6c0f11f6edc68d583fbd6'}}
ORDINARY_FIXTURE_FRAGMENT_COUNTS = {'scripts/ci/test_offline_tooling_failure_evidence711.py': 1, 'scripts/ci/test_offline_tooling_failure_inventory.py': 2, 'scripts/ci/test_offline_tooling_failure_parent_ids658.py': 1, 'scripts/ci/test_offline_tooling_reuse.py': 1, 'scripts/ci/test_desktop_media_context.py': 3, 'scripts/ci/test_ci_source_domain740.py': 1}
ORDINARY_PREVIOUS730 = {'bytes': 34278, 'sha256': '65e45763c96ee12d6317f35be7566038ea21b319661ccbb68b3c8e34013694f7', 'control': {'bytes': 17068, 'path': 'scripts/ci/test_ci_fixture_successor730.py', 'sha256': 'e2064214f6f1dfd54b8f04d39f028a2bbd67cd8135444ed0b65d32d1854a1ea9'}, 'own_guard': {'bytes': 11755, 'template_sha256': '916b2bb844176e4200704adf0fc8d6d137d5017fcfa9dfb89886506dc01ac1c0'}}
ORDINARY_FIXTURES = frozenset(ORDINARY_FIXTURE_BEFORE)
ORDINARY_MODIFIED = BASE_MODIFIED | ORDINARY_FIXTURES
RELATED_SCOPE = 'Exact fourteen producer421425 owning fixture failures plus two material inherited WebView TestFilter calls and narrowly owned Cookie raw self/control comparisons; original56/base59/base11/ordinary6/ordinary16/raw301/current303/named1751904036 remain distinct; FF is inverse DATA only, no actual FF rewrite; source-only'
RELATED_BEFORE = {'calf-webview/build.gradle.kts': {'bytes': 9474, 'sha256': '01801ef71db7b6b404a663eaf3a4585745b7e9fa8decad81dcb601f2b11d66c8'}, 'scripts/ci/camera_handoff_fixture_source_projection.py': {'bytes': 3952, 'sha256': '9d226779c3c8b5cd20010315d794a2e7be7ded258aa72c3ac73ebd49fc67e588'}, 'scripts/ci/cookie_ci668_outer_source_projection.py': {'bytes': 25045, 'sha256': '70df74292fb2fc7c92266f7197cbcbcd6dbce75d18d180d4082a6d430c5946c2'}, 'scripts/ci/test_android_camera_callback_configure_once793.py': {'bytes': 60792, 'sha256': '3c020b94308321ebd3c583151cdf92d38b12ff1cecf0eb92b29ad8f87c8f20e4'}, 'scripts/ci/test_android_camera_pre_reporter_fail_fast.py': {'bytes': 69818, 'sha256': '8a2f0d6a5f8a7e06f8721fc7ac4f3a38f5fd159b1c602b725032795ce33d4114'}, 'scripts/ci/test_ios_webview_request_focus.py': {'bytes': 20878, 'sha256': '32cd5dc9c33e7113e6b653d53ea2b67497506b3fa56bdb2fce2869f42db7603b'}, 'scripts/ci/test_macos_share_missing_only.py': {'bytes': 22881, 'sha256': '93b69767337d4a224a9624e7ca431b3b3a5c96bdbd2909f33c6c6d8d8475f01d'}, 'scripts/ci/test_platform_recovery659_source_projection.py': {'bytes': 18018, 'sha256': '35d2f7328d63799daa2a2ed5d387d40691cb64253e329acedc07610fd5fddb15'}, 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': {'bytes': 17755, 'sha256': '64f53402082ab86a255f22634ee9e73871b735bb78d81bed50d60919e0f29a2a'}, 'scripts/ci/tests/test_cookie_common_jdk_scope681.py': {'bytes': 20253, 'sha256': '1b571686e32c733b759572d83a75833e4bf6031797a4505239e542209ab2d4cb'}}
RELATED_FRAGMENT_COUNTS = {'calf-webview/build.gradle.kts': 2, 'scripts/ci/camera_handoff_fixture_source_projection.py': 2, 'scripts/ci/cookie_ci668_outer_source_projection.py': 9, 'scripts/ci/test_android_camera_callback_configure_once793.py': 4, 'scripts/ci/test_android_camera_pre_reporter_fail_fast.py': 1, 'scripts/ci/test_ios_webview_request_focus.py': 2, 'scripts/ci/test_macos_share_missing_only.py': 2, 'scripts/ci/test_platform_recovery659_source_projection.py': 2, 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': 2, 'scripts/ci/tests/test_cookie_common_jdk_scope681.py': 8}
RELATED_PREVIOUS730 = {'bytes': 55485, 'sha256': '792ce3e18e070877a95d69f514b36c7552bdaa9bf91904f4b57baaa01b096817', 'control': {'bytes': 21300, 'path': 'scripts/ci/test_ci_fixture_successor730.py', 'sha256': 'f48ebda9e81f130eb83bf8bf514250fefc04da889792c9a2b5b3724e3f4d6a45'}, 'own_guard': {'bytes': 16060, 'template_sha256': 'aa5509ee7548602dba3967dc571d0d01c2f1e3e94d980a2dd54222f64dfc6080'}}
RELATED_COPIED = {'scripts/ci/tests/test_webview_kotlin_test_filter_api777.py': {'bytes': 5875, 'sha256': '67872886beb28e4f414d83c4bc2d5e838c4761f3c37ffcfcdc7db5f314d9ed43'}}
RELATED_MODIFIED = frozenset(RELATED_BEFORE)
V1_MODIFIED = ORDINARY_MODIFIED | RELATED_MODIFIED
FAILURE_SCOPE = 'Exact FIRST37 failed10 recovery only: raw-only FF External328/ARM64 boundaries, named Cookie681 raw admission, independently scoped old hook/endpoint fixtures and original two desktop headers; sealed V1/first-nine/777, original56/recovery59/base11/ordinary6/16/related10/raw301/current303/named1751904036 stay DATA; copied777 is never MODIFIED or raw enrollment; source-only'
FAILURE_BEFORE = {'scripts/ci/android_external328_source_projection.py': {'bytes': 7071, 'sha256': '10743e0b14e7ee6fcdc31fe51f6dc7b8fda7237d02a77733b2ab37b8d57c93c1'}, 'scripts/ci/arm64_stop_candidate_source_projection.py': {'bytes': 5064, 'sha256': '79c4af44b4846e730c89d12ce963a0f3caa1c64667de64f1c1b6026ee9dd8af6'}, 'scripts/ci/cookie_common_jdk_source_projection.py': {'bytes': 16302, 'sha256': '88bc6780a31a5a3c338f7ac7f6936d0846f487a1aa0f92308e2388fc5c5521bd'}, 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': {'bytes': 18430, 'sha256': 'f4c4e5b6a715a502c5ddee542d578764117f232d7e47a000905b26ccb37ac836'}, 'scripts/ci/tests/test_cookie_common_jdk_scope681.py': {'bytes': 21015, 'sha256': '799b2fafa3d985c88d8b1db6b8a2d37f102e40e0392541682b4f1555a3698aae'}, 'scripts/ci/tests/test_webview_kotlin_test_filter_api777.py': {'bytes': 5875, 'sha256': '67872886beb28e4f414d83c4bc2d5e838c4761f3c37ffcfcdc7db5f314d9ed43'}}
FAILURE_FRAGMENT_COUNTS = {'scripts/ci/android_external328_source_projection.py': 1, 'scripts/ci/arm64_stop_candidate_source_projection.py': 1, 'scripts/ci/cookie_common_jdk_source_projection.py': 1, 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': 16, 'scripts/ci/tests/test_cookie_common_jdk_scope681.py': 1, 'scripts/ci/tests/test_webview_kotlin_test_filter_api777.py': 1}
FAILURE_PREVIOUS730 = {'bytes': 84713, 'sha256': '1e4b8338579207f1530b91ed75472ece6492a162fa6613ddfb132ce7acd68cf3', 'control': {'bytes': 25848, 'path': 'scripts/ci/test_ci_fixture_successor730.py', 'sha256': 'e9884d90b67746d3b3fbaa31ad9dbbc1d58adc624412ccb5182676e05a7f77f1'}, 'own_guard': {'bytes': 21499, 'template_sha256': 'c74f7da103368f9d1815384c82d5acc4ff90aa24c4b8e3132535c3595d5d9e86'}}
FAILURE_COPIED = frozenset(('scripts/ci/tests/test_webview_kotlin_test_filter_api777.py',))
FAILURE_MODIFIED = frozenset(FAILURE_BEFORE) - FAILURE_COPIED
PLATFORM_CUSTODY_SCOPE743 = 'Exact owning Platform659 ten-extra refusal before667/664/Remote/tooling history; additive R2 source DATA only, original raw303/named1751904036 and later fresh validation retained, no cache/admission/native/budget changes; exact existing-current MacShare two scalar-leaf spans and eight materialization controls in the same owning control, immutable-success cache limits16/3 unchanged; exact tooling671 existing-operation composition once/private inverse-row arithmetic and NEW4 fresh-public controls, original671 SPEC and singleton34940 guard remain unchanged; exact existing-operation RAW prefix/tooling reuse and once-qualified immutable730/recovery740/domain740 private rows; every public fresh reader, successful suffix, descriptor/settings custody, original671 singleton34940, original80690 DATA guards and caps remain; explicit Remote existing endpoint, no cross-operation cache or LAST-loop changes'
PLATFORM_CUSTODY_FIELDS743 = frozenset(("platform_custody_scope743", "platform_custody_bindings743", "platform_custody_previous730"))
PLATFORM_CUSTODY_BEFORE743 = {'scripts/ci/platform_recovery659_source_projection.py': {'bytes': 12858, 'sha256': '4505c503a7cf2b354e7d18dbf9129a43071ffc9a0fbb8e2093dfbca8f179960a'}, 'scripts/ci/test_platform_recovery659_source_projection.py': {'bytes': 18094, 'sha256': '813a2deea6d376a4426d3a2197d24158e56d68e09938f85e8af3f1a0a0d739d5'}, 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': {'bytes': 29472, 'sha256': '34aeff21c808a117edfbef0e9607ab93c4985cb35d97a102f752c50a6bd72273'}, 'scripts/ci/test_ci_fixture_successor730.py': {'bytes': 45027, 'sha256': 'b346d227ecd18fdd00a7b79a0826e70fb424293d9e9a5c39be897274f7b1ae5c'}, 'scripts/ci/macos_share_ci668_composition.py': {'bytes': 80582, 'sha256': '86bd1dc1b3685c5167e0ccd207a3048213e765e49c7a88dac73faa6c659d0ede'}, 'scripts/ci/tooling_recovery671_source_projection.py': {'bytes': 34940, 'sha256': '9177e99552be5a6319e1f722fc0db43f73f2f68782d91829abc4028fff248d1c'}, 'scripts/ci/android_io_remote_routing_source_projection.py': {'bytes': 16661, 'sha256': '95fe8ec1b01cd81e49f8475f781f0218c1344d275ca70115784cfe45d67446e1'}}
PLATFORM_CUSTODY_FRAGMENT_COUNTS743 = {'scripts/ci/platform_recovery659_source_projection.py': 3, 'scripts/ci/test_platform_recovery659_source_projection.py': 4, 'scripts/ci/tests/test_cookie_ci668_outer_scope609.py': 7, 'scripts/ci/test_ci_fixture_successor730.py': 10, 'scripts/ci/macos_share_ci668_composition.py': 12, 'scripts/ci/tooling_recovery671_source_projection.py': 3, 'scripts/ci/android_io_remote_routing_source_projection.py': 1}
PLATFORM_CUSTODY_PREVIOUS743 = {'bytes': 142095, 'sha256': '460c50f1706dc134bc0dcdabb83afa334d367e67603d65343f45f6bfd7927530'}
PLATFORM_CUSTODY_BOUND743 = frozenset(PLATFORM_CUSTODY_BEFORE743)
PLATFORM_CUSTODY_MODIFIED743 = PLATFORM_CUSTODY_BOUND743 - {CONTROL}
PRE_PLATFORM_MODIFIED743 = V1_MODIFIED | FAILURE_MODIFIED
MODIFIED = PRE_PLATFORM_MODIFIED743 | PLATFORM_CUSTODY_MODIFIED743


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _identity(relative, payload):
    from ci_source_domain740 import _identity as identity740
    identity740(relative, payload)  # Original exact-str/path/bytes/size grammar.


def _ordinary(root, relative, maximum=MAX_SOURCE):
    from macos_share_appkit_only_source_projection import ordinary_bytes
    return ordinary_bytes(root, relative, maximum)  # Actual descriptor bytes only.


def _endpoint(value):
    need(type(value) is dict and set(value) == {"bytes", "sha256"}
         and type(value["bytes"]) is int and 0 < value["bytes"] <= MAX_SOURCE
         and type(value["sha256"]) is str and len(value["sha256"]) == 64
         and all(char in "0123456789abcdef" for char in value["sha256"]),
         "exact-finite-fixture-successor-endpoint-required")



MAX_ANCESTOR_RAW743 = 512 * 1024
MAX_ANCESTOR_KEY_CHARS743 = 512 * 1024
MAX_ANCESTOR_KEY_NODES743 = 8192


def _ancestor_tree743(value, budget, depth=0):
    """Only exact type-tagged immutable content; foreign/large values fall back."""
    budget[0] += 1
    if budget[0] > MAX_ANCESTOR_KEY_NODES743 or depth > 64:
        raise TypeError("ancestor content is outside the finite memo key")
    kind = type(value)
    if kind is dict:
        rows = []
        for key, child in value.items():
            if type(key) is not str:
                raise TypeError("ancestor object key is not an exact string")
            budget[1] += len(key)
            if budget[1] > MAX_ANCESTOR_KEY_CHARS743:
                raise TypeError("ancestor content key is too large")
            rows.append((key, _ancestor_tree743(child, budget, depth + 1)))
        return ("object", tuple(rows))
    if kind is list:
        return ("array", tuple(_ancestor_tree743(child, budget, depth + 1) for child in value))
    if kind is str:
        budget[1] += len(value)
        if budget[1] > MAX_ANCESTOR_KEY_CHARS743:
            raise TypeError("ancestor content key is too large")
        return ("string", value)
    if kind is bool:
        return ("boolean", value)
    if kind is int and value.bit_length() <= 64:
        return ("integer", value)
    if kind is float and -float("inf") < value < float("inf"):
        return ("float", value.hex())  # Keeps -0.0 distinct from 0.0 and ints/bools.
    if value is None:
        return ("null", None)
    raise TypeError("ancestor content has a foreign or nonfinite value")


def _ancestor_thaw743(tree):
    kind, value = tree
    if kind == "object":
        return {key: _ancestor_thaw743(child) for key, child in value}
    if kind == "array":
        return [_ancestor_thaw743(child) for child in value]
    if kind == "float":
        return float.fromhex(value)
    return value


def _ancestor_uncached743(document):
    """The original canonical serialization/hash; no FS or document admission."""
    encoded = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode()
    return sha(encoded), len(encoded)


@lru_cache(maxsize=3)
def _ancestor_cached743(key):
    """Only successful immutable digest/length tuples, never mutable trees or IO.

    Concurrent misses may repeat pure arithmetic. This is not synchronization
    against hostile concurrent monkeypatches; every ordinary/schema wrapper stays
    live. Actual fresh content, raw bytes, authority and stage all enter the key.
    """
    raw, tree, expected, stage, reason = key
    identity = _ancestor_uncached743(_ancestor_thaw743(tree))
    need(identity == expected, reason)
    return identity


def _ancestor_context743():
    """Warm serializer/helper/crypto drift must use original uncached arithmetic."""
    try:
        functions = (json.dumps, json.JSONEncoder.__init__, json.JSONEncoder.encode,
                     json.JSONEncoder.iterencode, json.encoder._make_iterencode,
                     sha, need, _ancestor_tree743, _ancestor_thaw743,
                     _ancestor_uncached743, _ancestor_cached743.__wrapped__,
                     _ancestor_context743)
        function_context = tuple(
            (function, getattr(function, "__code__", None),
             tuple((type(value), value) for value in (getattr(function, "__defaults__", None) or ())),
             tuple((name, type(value), value) for name, value in
                   sorted((getattr(function, "__kwdefaults__", None) or {}).items())))
            for function in functions)
        encoder = json.encoder
        separator_state = []
        for encoder_class in (json.JSONEncoder, encoder.JSONEncoder):
            for name in ("item_separator", "key_separator"):
                value = getattr(encoder_class, name)
                if type(value) is not str:
                    return None  # Foreign mutable class state must use original arithmetic.
                separator_state.append((encoder_class, name, type(value), value))
        context = (json, encoder, hashlib, function_context, json.JSONEncoder,
                   encoder.JSONEncoder, tuple(separator_state), encoder.encode_basestring_ascii,
                   encoder.encode_basestring, encoder.c_make_encoder, encoder.INFINITY,
                   hashlib.sha256, _ancestor_cached743,
                   MAX_ANCESTOR_RAW743, MAX_ANCESTOR_KEY_CHARS743, MAX_ANCESTOR_KEY_NODES743,
                   tuple((name, globals().get(name, _ANCESTOR_BUILTINS743.get(name)))
                         for name in _ANCESTOR_BUILTIN_NAMES743))
        hash(context)
        return context
    except (AttributeError, TypeError):
        return None


_ANCESTOR_BUILTINS743 = _ancestor_uncached743.__builtins__
_ANCESTOR_BUILTIN_NAMES743 = (
    "type", "len", "dict", "list", "tuple", "str", "bool", "int", "float", "bytes",
    "getattr", "sorted", "hash", "ValueError", "TypeError", "RecursionError")
_ANCESTOR_CONTEXT743 = _ancestor_context743()
_ANCESTOR_STDLIB743 = (
    getattr(json.dumps, "__module__", None) == "json"
    and getattr(json.dumps, "__globals__", None) is json.__dict__
    and getattr(json.JSONEncoder.encode, "__globals__", None) is json.encoder.__dict__
    and type(hashlib.sha256) is type(len)
    and getattr(hashlib.sha256, "__module__", None) in {"_hashlib", "_sha256", "_sha2"})


def _canonical_ancestor_identity743(raw, document, expected, stage, reason):
    """Memo eligibility only; unsupported inputs retain original arithmetic."""
    if (not _ANCESTOR_STDLIB743 or _ANCESTOR_CONTEXT743 is None
            or _ancestor_context743() != _ANCESTOR_CONTEXT743
            or type(raw) is not bytes or not 0 < len(raw) <= MAX_ANCESTOR_RAW743
            or type(stage) is not int or stage not in (0, 1, 2)
            or type(expected) is not tuple or len(expected) != 2
            or type(expected[0]) is not str or len(expected[0]) != 64
            or type(expected[1]) is not int or not 0 < expected[1] <= MAX_ANCESTOR_RAW743
            or type(reason) is not str or not 0 < len(reason) <= 256):
        return _ancestor_uncached743(document)
    try:
        tree = _ancestor_tree743(document, [0, 0])
    except (TypeError, RecursionError):
        return _ancestor_uncached743(document)
    return _ancestor_cached743((raw, tree, expected, stage, reason))


def _platform_same_json743(left, right):
    """Fresh exact-type R2 DATA comparison, not a memo or schema admission."""
    kind = type(left)
    if kind is not type(right):
        return False
    if kind is dict:
        return (set(left) == set(right) and all(type(key) is str and
                _platform_same_json743(left[key], right[key]) for key in left))
    if kind is list:
        return len(left) == len(right) and all(_platform_same_json743(a, b) for a, b in zip(left, right))
    if kind is float:
        return (-float("inf") < left < float("inf") and left.hex() == right.hex())
    return kind in (str, int, bool, type(None)) and left == right


def _platform_previous_document743(document):
    """Exact sealed R2 JSON stays DATA; no new serializer cache or extra source file."""
    from macos_share_ci668_composition import _json as json_bytes
    previous = document["platform_custody_previous730"]
    need(type(previous) is dict and set(previous) == {"bytes", "sha256", "source"}
         and type(previous["source"]) is str and type(previous["bytes"]) is int
         and type(previous["sha256"]) is str
         and {key: previous[key] for key in ("bytes", "sha256")} == PLATFORM_CUSTODY_PREVIOUS743,
         "exact-separately-sealed-R2-predecessor-DATA-required")
    raw = previous["source"].encode()
    need((sha(raw), len(raw)) == (PLATFORM_CUSTODY_PREVIOUS743["sha256"], PLATFORM_CUSTODY_PREVIOUS743["bytes"])
         and len(raw) <= MAX_SPEC, "complete-byte-identical-R2-predecessor-DATA-required")
    sealed = json_bytes(raw)  # Existing fresh private parse path; no admission is cached.
    need(type(sealed) is dict, "ordinary-sealed-R2-object-required")
    projection = {key: value for key, value in document.items() if key not in PLATFORM_CUSTODY_FIELDS743}
    projection["own_guard"] = sealed["own_guard"]  # New executable endpoint remains separately exact.
    control_row = document["platform_custody_bindings743"][CONTROL]
    need(document["control"] == {"path": CONTROL, "bytes": control_row["after_bytes"], "sha256": control_row["after_sha256"]},
         "new-owning-control-metadata-must-equal-its-exact-declared-current-row")
    projection["control"] = sealed["control"]  # NEW09 correction does not rewrite R2 control DATA.
    try:
        same = _platform_same_json743(projection, sealed)
    except RecursionError:
        same = False
    need(same, "every-unchanged-R2-binding-metadata-and-control-byte-required")
    return sealed


def _document(root=ROOT):
    from ci_source_domain740 import _binding
    from macos_share_ci668_composition import _json as json_bytes
    raw = _ordinary(root, SPEC, MAX_SPEC)[0]
    need(sha(raw) == SPEC_SHA256, "exact-six-fixture-successor-manifest-required")
    document = json_bytes(raw)
    need(type(document) is dict and set(document) == {
         "schema_version", "scope", "originals", "bindings", "control", "own_guard",
         "capacity_scope", "capacity_binding", "routing_binding", "remote_binding",
         "ordinary_fixture_scope", "ordinary_fixture_bindings", "ordinary_previous730",
         "related_scope", "related_bindings", "related_previous730", "related_copied",
          "failure_scope", "failure_bindings", "failure_previous730", "failure_copied",
          "platform_custody_scope743", "platform_custody_bindings743", "platform_custody_previous730"}
         and type(document["schema_version"]) is int and document["schema_version"] == 1
         and document["scope"] == SCOPE and document["originals"] == ORIGINALS
         and document["capacity_scope"] == CAPACITY_SCOPE
         and type(document["bindings"]) is dict and set(document["bindings"]) == frozenset(BEFORE),
         "unchanged740742-current303-and-finite-fixture-successor-schema-required")
    need(document["platform_custody_scope743"] == PLATFORM_CUSTODY_SCOPE743
         and type(document["platform_custody_bindings743"]) is dict
         and set(document["platform_custody_bindings743"]) == PLATFORM_CUSTODY_BOUND743,
         "only-five-explicit-owning-Platform-successor-source-bindings-required")
    for relative, row in document["platform_custody_bindings743"].items():
        _identity(relative, b"owning-Platform-current-source-only")
        _binding(row, PLATFORM_CUSTODY_BEFORE743[relative], PLATFORM_CUSTODY_FRAGMENT_COUNTS743[relative])
    sealed_r2 = _platform_previous_document743(document)
    for relative, row in document["bindings"].items():
        _identity(relative, b"finite-fixture-successor-identity")
        _binding(row, BEFORE[relative], FRAGMENT_COUNTS[relative])
    _binding(document["capacity_binding"], CAPACITY_BEFORE, 2)
    _binding(document["routing_binding"], ROUTING_BEFORE, 1)
    _binding(document["remote_binding"], REMOTE_BEFORE, 1)
    need(document["ordinary_fixture_scope"] == ORDINARY_FIXTURE_SCOPE
         and document["ordinary_previous730"] == ORDINARY_PREVIOUS730
         and type(document["ordinary_fixture_bindings"]) is dict
         and set(document["ordinary_fixture_bindings"]) == ORDINARY_FIXTURES,
         "exact-six-owning-ordinary-fixtures-and-original730-metadata-required")
    for relative, row in document["ordinary_fixture_bindings"].items():
        _identity(relative, b"ordinary-fixture-only-source-identity")
        _binding(row, ORDINARY_FIXTURE_BEFORE[relative], ORDINARY_FIXTURE_FRAGMENT_COUNTS[relative])
    need(document["failure_scope"] == FAILURE_SCOPE
         and document["failure_previous730"] == FAILURE_PREVIOUS730
         and type(document["failure_copied"]) is list
         and document["failure_copied"] == sorted(FAILURE_COPIED)
         and type(document["failure_bindings"]) is dict
         and set(document["failure_bindings"]) == frozenset(FAILURE_BEFORE),
         "exact-failed10-owning-rows-and-separate777-copy-required")
    for relative, row in document["failure_bindings"].items():
        _identity(relative, b"failed10-only-source-identity")
        _binding(row, FAILURE_BEFORE[relative], FAILURE_FRAGMENT_COUNTS[relative])
    # Restore every sealed V1 byte as DATA; no prior target is executed.
    failure_legacy = {key: value for key, value in sealed_r2.items() if key not in
                      {"failure_scope", "failure_bindings", "failure_previous730", "failure_copied"}}
    failure_legacy["control"] = FAILURE_PREVIOUS730["control"]
    failure_legacy["own_guard"] = FAILURE_PREVIOUS730["own_guard"]
    import json
    identity = _canonical_ancestor_identity743(raw, failure_legacy,
        (FAILURE_PREVIOUS730["sha256"], FAILURE_PREVIOUS730["bytes"]), 0,
        "all-sealed-V1-related-and-ordinary-bindings-metadata-must-remain-byte-identical")
    need(identity == (FAILURE_PREVIOUS730["sha256"], FAILURE_PREVIOUS730["bytes"]),
         "all-sealed-V1-related-and-ordinary-bindings-metadata-must-remain-byte-identical")
    need(document["related_scope"] == RELATED_SCOPE
         and document["related_previous730"] == RELATED_PREVIOUS730
         and document["related_copied"] == RELATED_COPIED
         and type(document["related_bindings"]) is dict
         and set(document["related_bindings"]) == RELATED_MODIFIED,
         "exact-related-owning-fixtures-and-separate-copied-control-required")
    for relative, row in document["related_bindings"].items():
        _identity(relative, b"related-owning-fixture-source-identity")
        _binding(row, RELATED_BEFORE[relative], RELATED_FRAGMENT_COUNTS[relative])
    # Authenticate every immutable first-nine and original730 field as DATA.
    related_legacy = {key: value for key, value in failure_legacy.items() if key not in
                      {"related_scope", "related_bindings", "related_previous730", "related_copied"}}
    related_legacy["control"] = RELATED_PREVIOUS730["control"]
    related_legacy["own_guard"] = RELATED_PREVIOUS730["own_guard"]
    import json
    identity = _canonical_ancestor_identity743(raw, related_legacy,
        (RELATED_PREVIOUS730["sha256"], RELATED_PREVIOUS730["bytes"]), 1,
        "all-first-nine742-730-bindings-and-metadata-must-remain-byte-identical")
    need(identity == (RELATED_PREVIOUS730["sha256"], RELATED_PREVIOUS730["bytes"]),
         "all-first-nine742-730-bindings-and-metadata-must-remain-byte-identical")
    legacy = {key: value for key, value in related_legacy.items() if key not in
              {"ordinary_fixture_scope", "ordinary_fixture_bindings", "ordinary_previous730"}}
    legacy["control"] = ORDINARY_PREVIOUS730["control"]
    legacy["own_guard"] = ORDINARY_PREVIOUS730["own_guard"]
    identity = _canonical_ancestor_identity743(raw, legacy,
        (ORDINARY_PREVIOUS730["sha256"], ORDINARY_PREVIOUS730["bytes"]), 2,
        "all-original730-bindings-capacity-routing-remote-and-metadata-must-remain-byte-identical")
    need(identity == (ORDINARY_PREVIOUS730["sha256"], ORDINARY_PREVIOUS730["bytes"]),
         "all-original730-bindings-capacity-routing-remote-and-metadata-must-remain-byte-identical")
    control, own = document["control"], document["own_guard"]
    need(type(control) is dict and set(control) == {"path", "bytes", "sha256"}
         and control["path"] == CONTROL,
         "exact-fixture-successor-control-source-required")
    _endpoint({key: control[key] for key in ("bytes", "sha256")})
    need(type(own) is dict and set(own) == {"bytes", "template_sha256"},
         "exact-fixture-successor-own-template-required")
    _endpoint({"bytes": own["bytes"], "sha256": own["template_sha256"]})
    for relative, endpoint in RELATED_COPIED.items():
        _identity(relative, b"separate-copied-control-identity")
        _endpoint(endpoint)
    return document

def _inverse(payload, row):
    from ci_source_domain740 import _inverse as inverse740
    return inverse740(payload, row)  # Unchanged strict inverse/forward arithmetic.


def current_source_before_fixture_successor(relative, payload, root=ROOT):
    """Exact failed10 raw first, then sealed V1/capacity/r1 rows; no OLD admission."""
    _identity(relative, payload)
    if relative not in MODIFIED:
        return payload  # Unlisted bytes gain no301/303 or other admission.
    document = _document(root)
    if relative in PLATFORM_CUSTODY_MODIFIED743:
        payload = _inverse(payload, document["platform_custody_bindings743"][relative])
        if relative not in PRE_PLATFORM_MODIFIED743:
            return payload  # R2 DATA only; OLD cannot pass this strict current inverse.
    if relative in FAILURE_MODIFIED:
        payload = _inverse(payload, document["failure_bindings"][relative])
        if relative not in V1_MODIFIED:
            return payload  # Exact named predecessor DATA, not generic old-current admission.
    if relative in RELATED_MODIFIED:
        payload = _inverse(payload, document["related_bindings"][relative])
        if relative not in ORDINARY_MODIFIED:
            return payload
    if relative in ORDINARY_FIXTURES:
        payload = _inverse(payload, document["ordinary_fixture_bindings"][relative])
        if relative not in BASE_MODIFIED:
            return payload
    if relative == CAPACITY:
        return _inverse(payload, document["capacity_binding"])
    if relative == REMOTE:
        return _inverse(payload, document["remote_binding"])
    if relative == ROUTING:
        payload = _inverse(payload, document["routing_binding"])
    return _inverse(payload, document["bindings"][relative])

def peel_fixture_successor_for_history(relative, payload, root=ROOT):
    """Exact after-only failed10 then sealed V1 history; no generic layer search."""
    _identity(relative, payload)
    if relative not in MODIFIED:
        return payload
    document = _document(root)
    if relative in PLATFORM_CUSTODY_MODIFIED743:
        platform = document["platform_custody_bindings743"][relative]
        if (sha(payload), len(payload)) == (platform["after_sha256"], platform["after_bytes"]):
            payload = _inverse(payload, platform)
        if relative not in PRE_PLATFORM_MODIFIED743:
            return payload  # After-only R2 DATA; no generic current admission.
    if relative in FAILURE_MODIFIED:
        failure = document["failure_bindings"][relative]
        if (sha(payload), len(payload)) == (failure["after_sha256"], failure["after_bytes"]):
            payload = _inverse(payload, failure)
        if relative not in V1_MODIFIED:
            return payload  # After-only source DATA; every older pin remains required.
    if relative in RELATED_MODIFIED:
        related = document["related_bindings"][relative]
        if (sha(payload), len(payload)) == (related["after_sha256"], related["after_bytes"]):
            payload = _inverse(payload, related)
        if relative not in ORDINARY_MODIFIED:
            return payload  # After-only DATA, not an older-current certificate.
    if relative in ORDINARY_FIXTURES:
        ordinary = document["ordinary_fixture_bindings"][relative]
        if (sha(payload), len(payload)) == (ordinary["after_sha256"], ordinary["after_bytes"]):
            payload = _inverse(payload, ordinary)
        if relative not in BASE_MODIFIED:
            return payload  # After-only data, never OLD-as-current admission.
    if relative == CAPACITY:
        row = document["capacity_binding"]
    elif relative == REMOTE:
        row = document["remote_binding"]
    else:
        if relative == ROUTING:
            routing = document["routing_binding"]
            if (sha(payload), len(payload)) == (routing["after_sha256"], routing["after_bytes"]):
                payload = _inverse(payload, routing)
        row = document["bindings"][relative]
    if (sha(payload), len(payload)) == (row["after_sha256"], row["after_bytes"]):
        return _inverse(payload, row)
    return payload  # OLD/unknown remains history data; every next-owner pin stays exact.  # OLD/unknown stays data; every next-owner pin is retained.  # No generic layer search or reconstructed-as-current execution.

def dependency_inputs():
    """Finite copied custody only, never fixture_inputs/raw301/current303 growth."""
    return MODIFIED | set(ORIGINALS) | {OWNER, CONTROL, SPEC} | set(COPIED734) | set(RELATED_COPIED)


def validate_current_sources(root=ROOT):
    """Before all shaping, exact ordinary custody; final failures preserve primary."""
    from macos_share_ci668_composition import _source_projection_custody
    with _source_projection_custody() as capture:
        raw = {relative: capture(root, relative, MAX_SPEC if relative in set(ORIGINALS) | {SPEC}
                                 else MAX_SOURCE) for relative in sorted(dependency_inputs())}
        document = _document(root)  # Fresh schema/refusals, never a cached admission.
        for relative, endpoint in ORIGINALS.items():
            need((sha(raw[relative]), len(raw[relative])) == (endpoint["sha256"], endpoint["bytes"]),
                 "unchanged-fixture-successor740742-current303-authority-required")
        platform_before = {relative: _inverse(raw[relative], row)
                           for relative, row in document["platform_custody_bindings743"].items()}
        failure_before = {relative: _inverse(platform_before.get(relative, raw[relative]), row)
                          for relative, row in document["failure_bindings"].items()}
        related_before = {relative: _inverse(failure_before.get(relative, platform_before.get(relative, raw[relative])), row)
                          for relative, row in document["related_bindings"].items()}
        for relative, endpoint in RELATED_COPIED.items():
            comparison = failure_before.get(relative, raw[relative])
            need((sha(comparison), len(comparison)) == (endpoint["sha256"], endpoint["bytes"]),
                 "exact-separate-webview-filter-control-source-required")
        ordinary_before = {relative: _inverse(related_before.get(relative, raw[relative]), row)
                           for relative, row in document["ordinary_fixture_bindings"].items()}
        for relative, row in document["bindings"].items():
            payload = ordinary_before.get(relative, platform_before.get(relative, raw[relative]))
            if relative == ROUTING:
                payload = _inverse(payload, document["routing_binding"])
            _inverse(payload, row)
        _inverse(raw[CAPACITY], document["capacity_binding"])
        _inverse(platform_before.get(REMOTE, raw[REMOTE]), document["remote_binding"])
        for relative, endpoint in COPIED734.items():
            need((sha(raw[relative]), len(raw[relative])) == (endpoint["sha256"], endpoint["bytes"]),
                 "exact-two-capacity734-copied-current-sources-required")
        own = document["own_guard"]
        needle = ('SPEC_SHA256 = "' + SPEC_SHA256 + '"\n').encode()
        template = ('SPEC_SHA256 = "' + '0' * 64 + '"\n').encode()
        need(len(raw[OWNER]) == own["bytes"] and raw[OWNER].count(needle) == 1
             and sha(raw[OWNER].replace(needle, template, 1)) == own["template_sha256"],
             "exact-fixture-successor-own-helper-singleton-template-required")
        control = document["control"]
        need((sha(raw[CONTROL]), len(raw[CONTROL])) == (control["sha256"], control["bytes"]),
             "exact-fixture-successor-control-current-source-required")
        need(sha(raw[SPEC]) == SPEC_SHA256, "fixture-successor-manifest-held-through-validation-required")
    return True
