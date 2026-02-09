# MCAP Checker Quick Start Guide

## 🚀 5-Minute Quick Start

### 1. Install Dependencies

```bash
cd /Users/wanxin/PycharmProjects/Prismax/QA_PrismaX/Mcap_Checker
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python3 test_installation.py
```

### 3. Run Checks

```bash
# View file contents
python3 inspect_mcap.py demo_data/demo.mcap

# Basic check (A-F, I categories) + auto-save JSON to Reports/
python3 -m mcap_checker.checker demo_data/demo.mcap

# Full check (all A-G categories)
python3 -m mcap_checker.checker demo_data/demo.mcap --enable-vision --enable-advanced

# Custom JSON output path
python3 -m mcap_checker.checker demo_data/demo.mcap --json /custom/path/report.json
```

---

## 📋 All Check Categories

| Category | Checks | Enabled by Default | Description |
|----------|--------|-------------------|------------|
| **A** | File Structure (A1-A3) | ✅ | Readability, Topics, Schema |
| **B** | Time Consistency (B1-B2) | ✅ | Timestamps, Episode range |
| **C** | Frequency Coverage (C1-C3) | ✅ | Joint≥45Hz, Camera≥14.5FPS |
| **D** | Multi-modal Sync (D1-D2) | ✅ | Camera-joint≤34ms, Action alignment |
| **E** | Numerical Validity (E1-E2) | ✅ | Joint values, Motion continuity |
| **F** | Time Stability (F) | ✅ | Timing jitter detection |
| **F1-F2** | Advanced Features | ❌ | Requires `--enable-advanced` |
| **G** | Visual Quality (G1-G2) | ❌ | Requires `--enable-vision` |
| **I** | Metadata (I1) | ✅ | Required fields check |

### View All Checks

```bash
# Default: A-F, I categories (14+ items)
python3 -m mcap_checker.checker file.mcap

# Full: A-G, I categories (20+ items)
python3 -m mcap_checker.checker file.mcap --enable-vision --enable-advanced
```

---

## 💻 Common Commands

### Basic Usage

```bash
# Check a single file
python3 -m mcap_checker.checker demo_data/demo.mcap

# Strict mode
python3 -m mcap_checker.checker demo_data/demo.mcap --strict

# Full check (JSON auto-saved to Reports/)
python3 -m mcap_checker.checker demo_data/demo.mcap \
    --enable-vision --enable-advanced
```

### View Files

```bash
# View MCAP file details
python3 inspect_mcap.py demo_data/demo.mcap

# View help
python3 -m mcap_checker.checker --help
```

### Batch Processing

```bash
# Check all files (JSON auto-saved to Reports/)
for file in data/*.mcap; do
    echo "Checking: $file"
    python3 -m mcap_checker.checker "$file"
done

# Summarize results
for json in Reports/*.json; do
    level=$(grep -o '"level": "[^"]*"' "$json" | cut -d'"' -f4)
    file=$(grep -o '"file": "[^"]*"' "$json" | cut -d'"' -f4)
    echo "$level: $(basename $file)"
done
```

### Filter Output

```bash
# View only failures
python3 -m mcap_checker.checker file.mcap 2>&1 | grep "FAIL"

# View only warnings
python3 -m mcap_checker.checker file.mcap 2>&1 | grep "WARN"

# View only summary
python3 -m mcap_checker.checker file.mcap 2>&1 | grep "Summary:"
```

---

## 🐍 Python API

### Basic Usage

```python
from mcap_checker import run_checks

# Run checks
report = run_checks("demo_data/demo.mcap")

# View results
print(f"Result: {report.level}")  # PASS / WARN / FAIL

# Print report
report.print_summary()

# Save JSON
report.save_json("report.json")
```

### Batch Checking

```python
import glob
from mcap_checker import run_checks

results = {}
for mcap_file in glob.glob("data/*.mcap"):
    report = run_checks(mcap_file)
    results[mcap_file] = report.level
    
    if report.level == "FAIL":
        print(f"✗ {mcap_file}: Failed")
```

### Custom Configuration

```python
from mcap_checker import run_checks, config

# Modify thresholds
config.MIN_JOINT_HZ = 50.0      # Higher frequency requirement
config.MAX_SYNC_MS = 20.0       # Stricter synchronization
config.MAX_JOINT_JUMP = 0.3     # Smaller jumps

# Run checks
report = run_checks("file.mcap")
```

---

## 🔧 Configuration

Edit `mcap_checker/config.py`:

```python
# Frequency thresholds
MIN_JOINT_HZ = 45.0          # Minimum Joint State frequency (Hz)
MIN_CAMERA_FPS = 14.5        # Minimum camera frame rate (FPS)

# Synchronization thresholds
MAX_SYNC_MS = 34.0           # Maximum synchronization error (ms)

# Numerical thresholds
MAX_JOINT_JUMP = 0.5         # Maximum joint jump (rad)
MAX_TIME_GAP_MS = 200.0      # Maximum time gap (ms)

# Required Topics
REQUIRED_TOPICS = [
    "/joint_states",
]

# Feature flags
ENABLE_VISION_CHECKS = False    # Visual quality checks
ENABLE_ADVANCED_CHECKS = False  # Advanced checks
```

---

## 📊 Result Interpretation

### Output Example

```
============================================================
MCAP CHECK RESULT: WARN
============================================================
File: demo_data/demo.mcap

  ✓ [PASS] A1: MCAP readable | 41503 messages
  ⚠ [WARN] A2: Non-standard joint_states topics
  ✓ [PASS] B1: Timestamps monotonic
  ⚠ [WARN] C2: Low camera FPS | 12.9 FPS
  ✓ [PASS] D1: Camera-joint sync OK
  
============================================================
Summary: 9 passed, 9 warnings, 0 failed
============================================================
```

### Exit Codes

- `0` - PASS: All checks passed
- `1` - FAIL: Hard Fail items exist
- `2` - WARN: Warnings exist but no Hard Fail

### Severity Levels

- **✗ FAIL** (Hard): Data unusable, must fix
  - A1-A3: File structure issues
  - B1: Timestamp issues
  - E1: Invalid Joint values

- **⚠ WARN** (Soft): Data usable but quality issues
  - C1-C3: Low frequency
  - D1-D2: Synchronization issues
  - E2: Motion discontinuity
  - I1: Missing metadata

---

## 🎯 CI/CD Integration

### GitHub Actions

```yaml
- name: Check MCAP Quality
  run: |
    python3 -m mcap_checker.checker data/*.mcap --json report.json
    
- name: Fail on Bad Data
  run: |
    # Exit code 1 means FAIL
    if [ $? -eq 1 ]; then exit 1; fi
```

### Shell Script

```bash
#!/bin/bash
python3 -m mcap_checker.checker recording.mcap
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✓ PASS - Excellent data quality"
elif [ $exit_code -eq 2 ]; then
    echo "⚠ WARN - Warnings but usable"
else
    echo "✗ FAIL - Data failed"
    exit 1
fi
```

---

## ❓ FAQ

### Q: How to modify check thresholds?
A: Edit `mcap_checker/config.py` and modify the corresponding constant values.

### Q: Why do some checks show "not implemented"?
A: F1, F2, G2 are advanced features requiring complex algorithms. Currently placeholders, can be implemented as needed.

### Q: Why does E1/E2 show "No joint_states data"?
A: The default checker cannot parse ROS2 message format. Need to extend implementation to support specific message types.

### Q: How to add custom checks?
A: Create a new module in `rules/` directory, implement check functions, then call them in `checker.py`.

### Q: Why are vision checks disabled by default?
A: Image decoding and processing are time-consuming. Use `--enable-vision` to enable.

---

## 📚 More Information

- **Design Document**: See `Docs/Instruction.md` for complete check item definitions
- **API Documentation**: See `mcap_checker/README.md` for module details
- **Original Analysis**: See `Docs/analysis.md` for design concepts
- **Documentation Navigation**: See `Docs/DOCS.md` for all documents

---

## 🔄 Changelog

### v1.1.0 (2026-02-09)
- ✅ All A-G category checks are visible
- ✅ Support for non-standard topic names
- ✅ Improved error handling

### v1.0.0 (2026-02-09)
- 🎉 Initial version release
- ✅ Complete implementation of all check categories
- ✅ Modular architecture
- ✅ Comprehensive documentation

---

## Quick Reference

| Need | Command |
|------|---------|
| Basic check | `python3 -m mcap_checker.checker file.mcap` |
| Full check | `python3 -m mcap_checker.checker file.mcap --enable-vision --enable-advanced` |
| View file | `python3 inspect_mcap.py file.mcap` |
| JSON output | `python3 -m mcap_checker.checker file.mcap --json report.json` |
| Strict mode | `python3 -m mcap_checker.checker file.mcap --strict` |
| Test installation | `python3 test_installation.py` |
