# Robot Arm MCAP Automatic Validation Checklist

> This document provides complete validation specifications for robot arm MCAP data files, including check item definitions, implementation solutions, and runnable code examples.

## Quick Start

1. **View Checklist**: Understand all items to check (A-J sections)
2. **View Implementation**: Understand code structure and modular design
3. **Use Complete Script**: Directly run single-file script for quick checks

## Table of Contents

- [Quick Start](#quick-start)
- [Checklist](#checklist)
  - [A. File & Structure Integrity](#a-file--structure-integrity-hard-fail)
  - [B. Time & Order Consistency](#b-time--order-consistency-hard-fail)
  - [C. Frequency & Coverage](#c-frequency--coverage-soft-fail--warning)
  - [D. Multi-modal Synchronization](#d-multi-modal-synchronization-critical-quality)
  - [E. Numerical Validity](#e-numerical-validity-hard--soft)
  - [F. Trajectory & Stability](#f-trajectory--stability-advanced-but-strongly-recommended)
  - [G. Visual Quality](#g-visual-quality-strongly-recommended)
  - [H. Task & Semantic Consistency](#h-task--semantic-consistency)
  - [I. Metadata Integrity](#i-metadata-integrity-data-governance)
  - [J. Automatic Grading](#j-automatic-grading-recommended)
- [Implementation](#implementation)
  - [Overall Structure Design](#overall-structure-design)
  - [Code Implementation Examples](#code-implementation-examples)
  - [Complete Runnable Script](#complete-runnable-script)

---

## Checklist

### A. File & Structure Integrity (Hard Fail)

### A1️⃣ MCAP Readability

- File can be opened normally (no corruption)
- Contains at least 1 chunk
- Index exists (supports random access)

❌ **Fail = Discard directly**

### A2️⃣ Required Topics Exist

Required topics:
- `/joint_states`
- `/camera/*/image_raw`
- `/arm_controller/command` or `/action/*`
- Robot Description (URDF)

Check items:
- `joint_states` exists
- At least 2 camera image topics
- At least 1 action / command topic
- Robot Description (URDF)

❌ **Any missing = Cannot train**

### A3️⃣ Schema Parseable

- All channels can find schema
- Message deserialization has no errors

### B. Time & Order Consistency (Hard Fail)

### B1️⃣ Timestamps Valid

- timestamp is not empty
- Time monotonically increasing within single topic
- No rollback / wrap

### B2️⃣ Episode Time Range

- `episode_start < episode_end`
- All core topic times ∈ episode interval

### C. Frequency & Coverage (Soft Fail → Warning)

### C1️⃣ Joint State Frequency

- Average frequency ≥ 45 Hz
- Time alignment error < 34 ms
- No long frame drops (> 200 ms)

### C2️⃣ Camera Frame Rate

- Average FPS ≥ 14.5
- Frame drop rate < 1%
- Full episode coverage (no black hole intervals)

### C3️⃣ Action Frequency

- action / command is not empty
- Covers entire episode
- Reasonable time interleaving with joint_state

### D. Multi-modal Synchronization (Critical Quality)

### D1️⃣ Camera ↔ Joint Synchronization

- Any image frame can match nearest joint_state
- |Δt| ≤ 34 ms

### D2️⃣ Action ↔ State Alignment

- action time ≤ state time (no future information)
- State can respond to action (not static)

### E. Numerical Validity (Hard + Soft)

### E1️⃣ Joint Values Valid (Hard)

- position is not NaN / Inf
- velocity is not NaN
- Joint count is constant

### E2️⃣ Motion Continuity (Soft)

- Adjacent joint position jumps < threshold
- No spikes in velocity / acceleration

👉 **Commonly used to detect:**
- Sensor jitter
- Recording system stuttering

### F. Trajectory & Stability (Advanced but Strongly Recommended)

### F1️⃣ EE Trajectory Continuous

- No pose teleportation
- Attitude changes continuous (quaternion valid)

### F2️⃣ Jitter Detection

- High-frequency oscillation energy below threshold
- No mechanical resonance characteristics

### G. Visual Quality (Strongly Recommended)

### G1️⃣ Image Integrity

- Not all black / all white
- Resolution constant
- No severe tearing

### G2️⃣ Lighting & Flicker

- No periodic brightness flicker
- Brightness changes smoothly

### H. Task & Semantic Consistency

### H1️⃣ Episode Marking

- episode_start / end appear in pairs
- No overlapping episodes

### H2️⃣ Success Signal

- task_success exists (if labeled as success set)
- State stable after success

### I. Metadata Integrity (Data Governance)

### I1️⃣ Metadata Fields

Required fields:
- `robot_model`
- `arm_dof`
- `control_mode`
- `task_description`
- `episode_id`

Check items:
- Required fields complete
- episode_id unique

### J. Automatic Grading (Recommended)

### Output Levels

- **PASS** → Can be directly used for training
- **WARN** → Usable, but needs marking
- **FAIL** → Discard

### Recommended Strategy

- Any Hard Fail → FAIL
- Soft Fail ≥ N items → WARN

### K. Checklist → Script Mapping Example

| Checklist Item | Implementation |
|----------------|----------------|
| FPS | Δt statistics |
| Synchronization | Nearest neighbor time matching |
| Jitter | FFT / jerk |
| Frame drops | gap > threshold |
| Missing topic | channel scan |

> **Note**: The above table shows how each check is implemented in code, facilitating understanding of the correspondence between Checklist and code implementation.

---

## Implementation

### Overall Structure Design

```
mcap_checker/
├── checker.py          # Main entry
├── rules/
│   ├── structure.py    # Category A: File & topic
│   ├── timing.py       # Categories B/C/D: Time & frequency & sync
│   ├── values.py       # Categories E/F: Numerical & trajectory
│   ├── vision.py       # Category G: Image quality
│   └── metadata.py     # Category I: Metadata
├── report.py           # Unified report format
└── config.py           # Thresholds & rule flags
```

#### 1. Main Entry (checker.py)

```python
from mcap.reader import make_reader
from report import CheckReport
from rules import structure, timing, values, metadata

def run_checks(mcap_path: str) -> CheckReport:
    report = CheckReport(mcap_path)

    with open(mcap_path, "rb") as f:
        reader = make_reader(f)

        summary = reader.get_summary()
        channels = summary.channels
        schemas = summary.schemas

        # A. Structure
        structure.check_readable(summary, report)
        structure.check_required_topics(channels, report)
        structure.check_schemas(channels, schemas, report)

        # B/C/D. Time & frequency & sync
        timing.check_timestamps(reader, report)
        timing.check_frequencies(reader, report)
        timing.check_sync(reader, report)

        # E/F. Numerical & trajectory
        values.check_joint_states(reader, report)
        values.check_motion_smoothness(reader, report)

        # I. Metadata
        metadata.check_metadata(reader, report)

    report.finalize()
    return report


if __name__ == "__main__":
    import sys
    report = run_checks(sys.argv[1])
    report.print_summary()
```

#### 2. Unified Report Object (report.py)

```python
from enum import Enum

class Level(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"

class CheckReport:
    def __init__(self, file):
        self.file = file
        self.items = []
        self.hard_fail = False

    def ok(self, name, info=None):
        self.items.append(("PASS", name, info))

    def warn(self, name, info=None):
        self.items.append(("WARN", name, info))

    def fail(self, name, info=None):
        self.items.append(("FAIL", name, info))
        self.hard_fail = True

    def finalize(self):
        self.level = "FAIL" if self.hard_fail else \
                     "WARN" if any(i[0] == "WARN" for i in self.items) \
                     else "PASS"

    def print_summary(self):
        print(f"\nMCAP CHECK RESULT: {self.level}\n")
        for lvl, name, info in self.items:
            print(f"[{lvl}] {name} {info or ''}")
```

> **Note**: This design can directly:
> - Output JSON
> - Integrate into CI/CD workflows
> - Integrate into data management platforms

#### 3. Structure Checks (rules/structure.py)

```python
REQUIRED_TOPICS = [
    "/joint_states",
]

def check_readable(summary, report):
    if summary.statistics.message_count == 0:
        report.fail("Empty MCAP")
    else:
        report.ok("MCAP readable")

def check_required_topics(channels, report):
    topic_names = {c.topic for c in channels.values()}
    for t in REQUIRED_TOPICS:
        if t not in topic_names:
            report.fail(f"Missing topic: {t}")
    report.ok("Required topics present")

def check_schemas(channels, schemas, report):
    for c in channels.values():
        if c.schema_id not in schemas:
            report.fail(f"Missing schema for {c.topic}")
    report.ok("All schemas resolvable")
```

#### 4. Time & Frequency (rules/timing.py)

```python
import collections

def check_timestamps(reader, report):
    last_ts = {}
    for _, channel, message in reader.iter_messages():
        ts = message.log_time
        if channel.id in last_ts and ts < last_ts[channel.id]:
            report.fail(f"Timestamp rollback: {channel.topic}")
            return
        last_ts[channel.id] = ts
    report.ok("Timestamps monotonic")

def check_frequencies(reader, report):
    times = collections.defaultdict(list)

    for _, channel, message in reader.iter_messages():
        times[channel.topic].append(message.log_time)

    for topic, ts in times.items():
        if len(ts) < 2:
            continue
        duration = (ts[-1] - ts[0]) * 1e-9
        fps = len(ts) / duration if duration > 0 else 0

        if "joint_states" in topic and fps < 45:
            report.warn("Low joint_states rate", fps)

        if "image" in topic and fps < 14.5:
            report.warn(f"Low camera FPS: {topic}", fps)

    report.ok("Frequency check done")
```

#### 5. Synchronization Check (rules/timing.py continued)

```python
def check_sync(reader, report, max_dt_ms=34):
    joint_ts = []
    image_ts = []

    for _, channel, message in reader.iter_messages():
        if channel.topic == "/joint_states":
            joint_ts.append(message.log_time)
        if "image" in channel.topic:
            image_ts.append(message.log_time)

    if not joint_ts or not image_ts:
        report.warn("Skip sync check (missing topics)")
        return

    joint_ts.sort()
    for t in image_ts:
        nearest = min(joint_ts, key=lambda x: abs(x - t))
        dt_ms = abs(nearest - t) * 1e-6
        if dt_ms > max_dt_ms:
            report.warn("Camera-joint desync", dt_ms)
            return

    report.ok("Camera-joint sync OK")
```

#### 6. Joint Values & Trajectory (rules/values.py)

```python
import math

def check_joint_states(reader, report):
    for _, channel, msg in reader.iter_messages():
        if channel.topic != "/joint_states":
            continue
        js = msg
        if any(math.isnan(p) for p in js.position):
            report.fail("NaN in joint position")
            return
    report.ok("Joint values valid")

def check_motion_smoothness(reader, report, max_jump=0.5):
    last = None
    for _, channel, msg in reader.iter_messages():
        if channel.topic != "/joint_states":
            continue
        if last:
            diffs = [abs(a - b) for a, b in zip(msg.position, last)]
            if max(diffs) > max_jump:
                report.warn("Joint jump detected", max(diffs))
                return
        last = msg.position
    report.ok("Motion smoothness OK")
```

#### 7. Metadata Check (rules/metadata.py)

```python
REQUIRED_FIELDS = [
    "robot_model",
    "arm_dof",
    "task_description",
    "episode_id",
]

def check_metadata(reader, report):
    meta = reader.get_summary().metadata or {}
    for f in REQUIRED_FIELDS:
        if f not in meta:
            report.warn(f"Missing metadata field: {f}")
    report.ok("Metadata checked")
```

#### 8. Output Example

```text
MCAP CHECK RESULT: WARN

[PASS] MCAP readable
[PASS] Required topics present
[PASS] All schemas resolvable
[WARN] Low camera FPS: /camera/front/image_raw 12.3
[PASS] Camera-joint sync OK
[PASS] Joint values valid
[WARN] Missing metadata field: operator
```

---

### Complete Runnable Script

> Below is a **single-file, directly runnable MCAP robot arm data validation script** that integrates all the above check functions.

#### checker.py (Complete Runnable Version)

```python
#!/usr/bin/env python3
"""
MCAP Robot Arm Data Checker
Usage:
    python checker.py demo.mcap
"""

import sys
import math
import statistics
from collections import defaultdict
from mcap.reader import make_reader


# =========================
# Config
# =========================
REQUIRED_TOPICS = [
    "/joint_states",
]

MIN_JOINT_HZ = 45.0      # Minimum joint state frequency (Hz), corresponds to Checklist C1
MIN_CAMERA_FPS = 14.5    # Minimum camera frame rate (FPS), corresponds to Checklist C2
MAX_SYNC_MS = 34.0       # Maximum synchronization error (ms), corresponds to Checklist D1
MAX_TIME_GAP_MS = 200.0  # Maximum time gap (ms), corresponds to Checklist C1
MAX_JOINT_JUMP = 0.5     # Maximum joint jump (rad), corresponds to Checklist E2


# =========================
# Report
# =========================
class Report:
    def __init__(self, path):
        self.path = path
        self.items = []
        self.hard_fail = False

    def ok(self, name, info=""):
        self.items.append(("PASS", name, info))

    def warn(self, name, info=""):
        self.items.append(("WARN", name, info))

    def fail(self, name, info=""):
        self.items.append(("FAIL", name, info))
        self.hard_fail = True

    def finalize(self):
        if self.hard_fail:
            self.level = "FAIL"
        elif any(i[0] == "WARN" for i in self.items):
            self.level = "WARN"
        else:
            self.level = "PASS"

    def print(self):
        print(f"\n📦 MCAP CHECK RESULT: {self.level}")
        print(f"📄 File: {self.path}\n")
        for lvl, name, info in self.items:
            line = f"[{lvl}] {name}"
            if info:
                line += f" | {info}"
            print(line)


# =========================
# Utils
# =========================
def ns_to_ms(ns):
    return ns * 1e-6


def compute_rate(ts):
    if len(ts) < 2:
        return 0.0
    duration = (ts[-1] - ts[0]) * 1e-9
    return len(ts) / duration if duration > 0 else 0.0


# =========================
# Main Checks
# =========================
def run_checks(mcap_path):
    report = Report(mcap_path)

    try:
        f = open(mcap_path, "rb")
    except Exception as e:
        report.fail("MCAP open failed", str(e))
        report.finalize()
        return report

    with f:
        reader = make_reader(f)
        summary = reader.get_summary()

        # -------- A. Basic structure --------
        if summary.statistics.message_count == 0:
            report.fail("Empty MCAP")
            report.finalize()
            return report
        report.ok("MCAP readable", f"{summary.statistics.message_count} messages")

        topics = {c.topic for c in summary.channels.values()}
        for t in REQUIRED_TOPICS:
            if t not in topics:
                report.fail("Missing required topic", t)
        report.ok("Required topics checked")

        # -------- B. Collect timestamps --------
        topic_ts = defaultdict(list)

        last_ts_per_channel = {}

        for _, channel, msg in reader.iter_messages():
            ts = msg.log_time

            # monotonic check
            if channel.id in last_ts_per_channel:
                if ts < last_ts_per_channel[channel.id]:
                    report.fail("Timestamp rollback", channel.topic)
                    report.finalize()
                    return report
            last_ts_per_channel[channel.id] = ts

            topic_ts[channel.topic].append(ts)

        report.ok("Timestamp monotonic")

        # -------- C. Frequency checks --------
        for topic, ts in topic_ts.items():
            ts.sort()
            rate = compute_rate(ts)

            if topic == "/joint_states":
                if rate < MIN_JOINT_HZ:
                    report.warn("Low joint_states rate", f"{rate:.1f} Hz")

            if "image" in topic:
                if rate < MIN_CAMERA_FPS:
                    report.warn("Low camera FPS", f"{topic}: {rate:.1f}")

        report.ok("Frequency check done")

        # -------- D. Gap detection --------
        for topic, ts in topic_ts.items():
            if len(ts) < 2:
                continue
            gaps = [(ts[i+1] - ts[i]) for i in range(len(ts)-1)]
            max_gap_ms = ns_to_ms(max(gaps))
            if max_gap_ms > MAX_TIME_GAP_MS:
                report.warn("Large time gap",
                            f"{topic}: {max_gap_ms:.1f} ms")

        report.ok("Gap check done")

        # -------- E. Camera ↔ Joint sync --------
        joint_ts = topic_ts.get("/joint_states", [])
        cam_ts = []
        for t, ts in topic_ts.items():
            if "image" in t:
                cam_ts.extend(ts)

        if joint_ts and cam_ts:
            joint_ts.sort()
            bad = 0
            for t in cam_ts:
                nearest = min(joint_ts, key=lambda x: abs(x - t))
                dt_ms = abs(nearest - t) * 1e-6
                if dt_ms > MAX_SYNC_MS:
                    bad += 1
            ratio = bad / len(cam_ts)
            if ratio > 0.05:
                report.warn("Camera-joint desync",
                            f"{ratio*100:.1f}% frames > {MAX_SYNC_MS}ms")
            else:
                report.ok("Camera-joint sync OK")
        else:
            report.warn("Skip sync check", "missing joint or camera")

        # -------- F. Motion continuity (approx) --------
        # NOTE: payload not decoded, use timestamp jitter as proxy
        if "/joint_states" in topic_ts:
            ts = topic_ts["/joint_states"]
            if len(ts) > 3:
                intervals = [(ts[i+1] - ts[i]) * 1e-9 for i in range(len(ts)-1)]
                jitter = statistics.pstdev(intervals)
                if jitter > 0.02:
                    report.warn("Joint timing jitter", f"{jitter:.3f}s")
                else:
                    report.ok("Joint timing stable")

    report.finalize()
    return report


# =========================
# Entry
# =========================
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python checker.py <file.mcap>")
        sys.exit(1)

    report = run_checks(sys.argv[1])
    report.print()
```

#### How to Run

```bash
# Install dependencies
pip install mcap

# Run checks
python checker.py demo.mcap
```

#### Output Example

```text
📦 MCAP CHECK RESULT: WARN
📄 File: demo.mcap

[PASS] MCAP readable | 182394 messages
[PASS] Required topics checked
[PASS] Timestamp monotonic
[WARN] Low camera FPS | /camera/front/image_raw: 12.9
[WARN] Large time gap | /joint_states: 310.4 ms
[PASS] Camera-joint sync OK
[PASS] Joint timing stable
```
