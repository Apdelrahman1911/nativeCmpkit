# SPDX-License-Identifier: Apache-2.0
"""Complete preserved FallbackHome records; never an owned/removable task.

Finite Android15 Task.dump templates include the manifest-specific FallbackHome
affinity and the prior package-affinity form. Neither attests the installed
image. Callers separately prove the fresh guest, platform Settings identity,
no live Settings Activity and the exact baseline around their native UI lease.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

MAX_ROW_LENGTH = 2048
MAX_REPLY_BYTES = 65536
MAX_INT = 2147483647
MAX_LONG = 9223372036854775807
POSITIVE_INT = r"([1-9][0-9]{0,9})"
DECIMAL = r"(?:0|[1-9][0-9]{0,18})"
HEADER = re.compile(r"  \* Recent #(0|[1-9][0-9]{0,9}): (Task\{[a-f0-9]{1,8} #" +
                    POSITIVE_INT + r" type=home A=(1000:com\.android\.settings(?:\.FallbackHome)?)})")
INTENT = re.compile(r"    intent=\{act=android\.intent\.action\.MAIN "
                    r"cat=\[android\.intent\.category\.HOME] flg=0x[1-9a-f][0-9a-f]{0,7} "
                    r"cmp=com\.android\.settings/\.FallbackHome}")
POLICY = re.compile(r"    autoRemoveRecents=(true|false) isPersistable=(true|false) activityType=2")
ROOT_POLICY = re.compile(r"    rootWasReset=(true|false) mNeverRelinquishIdentity=(true|false) "
                         r"mReuseTask=(true|false) mLockTaskAuth=LOCK_TASK_AUTH_"
                         r"(?:DONT_LOCK|PINNABLE|LAUNCHABLE|ALLOWLISTED|LAUNCHABLE_PRIV)")
IDS = re.compile(r"    taskId=" + POSITIVE_INT + r" rootTaskId=" + POSITIVE_INT)
RESIZE_POLICY = re.compile(r"    mResizeMode=RESIZE_MODE_(?:UNRESIZEABLE|RESIZEABLE|FORCE_RESIZEABLE|"
                           r"RESIZEABLE_VIA_SDK_VERSION|FORCE_RESIZABLE_LANDSCAPE_ONLY|"
                           r"FORCE_RESIZABLE_PORTRAIT_ONLY|FORCE_RESIZABLE_PRESERVE_ORIENTATION) "
                           r"mSupportsPictureInPicture=(true|false) isResizeable=(true|false)")
LAST_ACTIVE = re.compile(r"    lastActiveTime=(" + DECIMAL + r") \(inactive for (" + DECIMAL + r")s\)")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


@dataclass(frozen=True, repr=False)
class SettingsHomeTaskBaseline:
    task_id: int
    root_task_id: int
    _stable_rows: tuple[str, ...] = field(repr=False)

    def __repr__(self) -> str:
        return "SettingsHomeTaskBaseline(preserved, not owned)"

    def safe(self) -> dict:
        return {"preserved_home_task_count": 1,
                "stable_record_sha256": hashlib.sha256("\n".join(self._stable_rows).encode("ascii")).hexdigest(),
                "owned_or_removable": False}


def parse_home_task(rows: list[str] | tuple[str, ...]) -> SettingsHomeTaskBaseline:
    require(type(rows) in (list, tuple) and len(rows) == 13 and all(
        type(row) is str and 1 <= len(row) <= MAX_ROW_LENGTH and all(32 <= ord(c) <= 126 for c in row)
        for row in rows), "Complete bounded ASCII fallback HOME task required")
    header = HEADER.fullmatch(rows[0])
    require(header is not None, "Exact fallback HOME header required")
    require(int(header[1]) <= MAX_INT and int(header[3]) <= MAX_INT,
            "Fallback HOME rank/task ID overflow")
    task_id = int(header[3])
    require(rows[1] == "    userId=0 effectiveUid=1000 mCallingUid=0 mUserSetupComplete=false "
            "mCallingPackage=null mCallingFeatureId=null", "Exact bootstrap user/UID/caller required")
    require(rows[2] == "    affinity=" + header[4] and INTENT.fullmatch(rows[3]) is not None and
            rows[4] == "    mActivityComponent=com.android.settings/.FallbackHome", "Exact HOME affinity/intent/component required")
    require(POLICY.fullmatch(rows[5]) is not None and ROOT_POLICY.fullmatch(rows[6]) is not None and
            rows[6] != "    rootWasReset=false mNeverRelinquishIdentity=false mReuseTask=false mLockTaskAuth=LOCK_TASK_AUTH_PINNABLE",
            "Exact printed HOME policies required")
    require(rows[7] == "    Activities=[]", "A live or nested Activity cannot be an empty HOME baseline")
    ids = IDS.fullmatch(rows[8])
    require(ids is not None and int(ids[1]) == task_id and int(ids[2]) <= MAX_INT,
            "Exact bounded matching leaf and preserved root identities required")
    require(rows[9] == "    hasChildPipActivity=false" and
            re.fullmatch(r"    mHasBeenVisible=(true|false)", rows[10]) is not None and
            RESIZE_POLICY.fullmatch(rows[11]) is not None, "Exact empty HOME child/visibility/resize policies required")
    clock = LAST_ACTIVE.fullmatch(rows[12])
    require(clock is not None and int(clock[1]) <= MAX_LONG and int(clock[2]) <= MAX_LONG,
            "Exact bounded HOME clock required")
    # Rank moves when OUR task is added/removed; elapsed inactivity is a clock.
    # Preserve EVERY other byte, including object/leaf/root IDs and lastActiveTime.
    stable = (header[2], *rows[1:12], "    lastActiveTime=" + clock[1])
    return SettingsHomeTaskBaseline(task_id, int(ids[2]), stable)


def parse_recent_home_baseline(payload: bytes) -> SettingsHomeTaskBaseline | None:
    """An empty list or ONE completely parsed nonowned HOME task, nothing else.

    Hidden/visible-only lists, live/standard/competing tasks, unknown sections or
    unfinished commands fail. Command exit/stderr are separately proved by the
    controller's unchanged result_bytes before this pure parser is called.
    """
    require(type(payload) is bytes and 0 < len(payload) <= MAX_REPLY_BYTES,
            "Bounded completed recent-task payload required")
    require(all(c in (10,) or 32 <= c <= 126 for c in payload), "Unsafe recent-task bytes")
    rows = payload.decode("ascii").removesuffix("\n").split("\n")
    require(all(len(row) <= MAX_ROW_LENGTH for row in rows) and len(rows) in (5, 6, 19),
            "Exact complete recent-task row count required")
    require(rows[0] == "ACTIVITY MANAGER RECENT TASKS (dumpsys activity recents)" and
            re.fullmatch(r"mRecentsUid=(0|[1-9][0-9]{0,9})", rows[1]) is not None and
            int(rows[1].split("=", 1)[1]) <= MAX_INT and
            re.fullmatch(r"mRecentsComponent=ComponentInfo\{[^{}]+}", rows[2]) is not None and
            re.fullmatch(r"mFreezeTaskListReordering=(true|false)", rows[3]) is not None and
            re.fullmatch(r"mFreezeTaskListReorderingPendingTimeout=(true|false)", rows[4]) is not None,
            "Exact complete recent-task framing required")
    if rows[5:] in ([], ["  (nothing)"]):
        return None
    require(rows[5] == "  Recent tasks:", "Only the complete raw task list can preserve a HOME baseline")
    return parse_home_task(rows[6:])
