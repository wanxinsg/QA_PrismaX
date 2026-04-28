# MCAP Checker - Robot Arm Data Validation Tool

A modular MCAP data validation tool designed based on `Instruction.md`.

## Installation

```bash
# Install dependencies
pip install mcap

# If image check functionality is needed
pip install numpy opencv-python
```

## Quick Start

### Basic Usage

```bash
# Check a single file
python -m mcap_checker.checker demo.mcap

# Output JSON report
python -m mcap_checker.checker demo.mcap --json report.json

# Enable strict mode
python -m mcap_checker.checker demo.mcap --strict
```

### Advanced Options

```bash
# Enable visual quality checks (slower)
python -m mcap_checker.checker demo.mcap --enable-vision

# Enable advanced checks (trajectory, jitter analysis)
python -m mcap_checker.checker demo.mcap --enable-advanced

# Combined usage
python -m mcap_checker.checker demo.mcap --strict --enable-advanced --json report.json
```

## Programming Interface

```python
from mcap_checker import run_checks

# Run checks
report = run_checks("demo.mcap")

# Print report
report.print_summary()

# Get results
print(f"Level: {report.level}")  # PASS / WARN / FAIL

# Export JSON
report.save_json("report.json")
```

## Directory Structure

```
mcap_checker/
├── __init__.py         # Package initialization
├── checker.py          # Main entry
├── report.py           # Report generation
├── config.py           # Configuration and thresholds
└── rules/              # Check rule modules
    ├── __init__.py
    ├── structure.py    # A: File structure
    ├── timing.py       # B/C/D: Time frequency synchronization
    ├── values.py       # E/F: Numerical and trajectory
    ├── metadata.py     # I: Metadata
    └── vision.py       # G: Visual quality
```

## Check Item Descriptions

### A. File & Structure Integrity (Hard Fail)
- A1: MCAP readability
- A2: Required Topics exist
- A3: Schema parseable

### B. Time & Order Consistency (Hard Fail)
- B1: Timestamps valid
- B2: Episode time range

### C. Frequency & Coverage (Soft Fail)
- C1: Joint State frequency ≥ 45 Hz
- C2: Camera frame rate ≥ 14.5 FPS
- C3: Action frequency check

### D. Multi-modal Synchronization (Critical Quality)
- D1: Camera ↔ Joint synchronization (≤ 34 ms)
- D2: Action ↔ State alignment

### E. Numerical Validity (Hard + Soft)
- E1: Joint values valid (Hard)
- E2: Motion continuity (Soft)

### F. Trajectory & Stability (Advanced)
- F1: EE trajectory continuity
- F2: Jitter detection

### G. Visual Quality (Optional)
- G1: Image integrity
- G2: Lighting & flicker

### I. Metadata Integrity
- I1: Required fields check

## Configuration

Edit `config.py` to modify thresholds and rule flags:

```python
# Frequency thresholds
MIN_JOINT_HZ = 45.0
MIN_CAMERA_FPS = 14.5

# Synchronization thresholds
MAX_SYNC_MS = 34.0

# Numerical thresholds
MAX_JOINT_JUMP = 0.5

# Feature flags
ENABLE_VISION_CHECKS = False
ENABLE_ADVANCED_CHECKS = False
```

## Output Format

### Terminal Output

```
============================================================
MCAP CHECK RESULT: WARN
============================================================
File: demo.mcap

  ✓ [PASS] A1: MCAP readable | 182394 messages, 5 chunks
  ✓ [PASS] A2: Required topics present | ...
  ⚠ [WARN] C2: Low camera FPS | /camera/front/image_raw: 12.9 FPS
  ✓ [PASS] D1: Camera-joint sync OK | 98.5% frames within 34.0 ms
  
============================================================
Summary: 15 passed, 3 warnings, 0 failed
============================================================
```

### JSON Output

```json
{
  "file": "demo.mcap",
  "level": "WARN",
  "summary": {
    "passed": 15,
    "warnings": 3,
    "failed": 0
  },
  "items": [
    {
      "level": "PASS",
      "name": "A1: MCAP readable",
      "info": "182394 messages, 5 chunks"
    },
    ...
  ]
}
```

## Exit Codes

- `0`: PASS - All checks passed
- `1`: FAIL - Hard Fail items exist
- `2`: WARN - Warning items exist but no Hard Fail

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Check MCAP Quality
  run: |
    python -m mcap_checker.checker data/*.mcap --json report.json
    
- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: mcap-check-report
    path: report.json
```

## Extension Development

### Adding New Check Rules

1. Create a new module in `rules/` directory
2. Implement check function:
```python
def check_custom(reader, report):
    # Your check logic
    if condition:
        report.fail("Custom check failed", "details")
    else:
        report.ok("Custom check passed")
```

3. Call it in `checker.py`:
```python
from .rules import custom
custom.check_custom(reader, report)
```

## Reference Documentation

See `Instruction.md` for detailed design

## License

MIT License
