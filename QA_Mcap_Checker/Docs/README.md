# MCAP Checker - Robot Arm Data Quality Validation Tool

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A quality validation tool for MCAP files based on best practices for robot arm data collection.

## ✨ Features

- ✅ **Complete Check Coverage** - Implements 10+ categories of checks from file structure to data quality
- 🔧 **Flexible Configuration** - All thresholds customizable, supports strict mode and optional features
- 📊 **Multiple Output Formats** - Terminal-friendly output + JSON reports, easy to integrate
- 🚀 **Easy to Use** - Command-line tool + Python API, 5-minute setup
- 🔌 **CI/CD Ready** - Returns standard exit codes, can be directly integrated into CI workflows
- 📦 **Modular Design** - Clear code structure, easy to extend and maintain

## 📋 Check Item List

### ✅ All Check Categories (A-G, I)

| Category | Check Items | Enabled by Default | Description |
|----------|------------|-------------------|-------------|
| **A** | 3 | ✅ | File structure integrity |
| **B** | 2 | ✅ | Time order consistency |
| **C** | 3+ | ✅ | Frequency and coverage |
| **D** | 2 | ✅ | Multi-modal synchronization |
| **E** | 2 | ✅ | Numerical validity |
| **F** | 1 | ✅ | Time stability |
| **F1-F2** | 2 | ❌ | Advanced features (requires `--enable-advanced`) |
| **G** | 2 | ❌ | Visual quality (requires `--enable-vision`) |
| **I** | 1 | ✅ | Metadata integrity |

> 💡 **View all checks**: `python3 -m mcap_checker.checker demo.mcap --enable-vision --enable-advanced`

### Hard Fail (Critical errors, data unusable)
- ✗ **A1**: MCAP file corrupted or empty
- ✗ **A2**: Missing required topics (joint_states, cameras)
- ✗ **A3**: Schema cannot be parsed
- ✗ **B1**: Timestamps reversed or empty
- ✗ **E1**: Joint values are NaN/Inf

### Soft Fail (Warnings, data usable but quality issues)
- ⚠ **C1**: Joint State frequency too low (< 45 Hz)
- ⚠ **C2**: Camera frame rate too low (< 14.5 FPS)
- ⚠ **C3**: Action/Command messages too few
- ⚠ **D1**: Camera-joint synchronization error too large (> 34 ms)
- ⚠ **E2**: Joint jumps too large
- ⚠ **F**: Large time jitter
- ⚠ **I1**: Missing metadata fields

### Optional Checks (require additional enablement)
- 🎨 **G1**: Image integrity (`--enable-vision`)
- 🎨 **G2**: Lighting flicker detection (`--enable-vision`)
- 🔬 **F1**: EE trajectory continuity (`--enable-advanced`)
- 🔬 **F2**: Vibration/jitter analysis (`--enable-advanced`)

> 📖 **Detailed description**: See [CHECK_CATEGORIES.md](CHECK_CATEGORIES.md) and [CHECKING_GUIDE.md](CHECKING_GUIDE.md)

## 🚀 Quick Start

### Installation

```bash
# Clone or enter project directory
cd QA_PrismaX/QA_Mcap_Checker

# Install dependencies
pip install -r requirements.txt

# Or install as Python package (recommended)
pip install -e .
```

### Basic Usage

```bash
# Check a single file
python3 -m mcap_checker.checker demo.mcap

# Output JSON report
python3 -m mcap_checker.checker demo.mcap --json report.json

# Strict mode (more checks become Hard Fail)
python3 -m mcap_checker.checker demo.mcap --strict

# Enable advanced checks
python3 -m mcap_checker.checker demo.mcap --enable-advanced
```

### Python API

```python
from mcap_checker import run_checks

# Run checks
report = run_checks("demo.mcap")

# View results
print(f"Result: {report.level}")  # PASS / WARN / FAIL

# Print detailed report
report.print_summary()

# Save JSON
report.save_json("report.json")
```

## 📊 Output Examples

### Terminal Output

```
============================================================
MCAP CHECK RESULT: WARN
============================================================
File: demo.mcap

  ✓ [PASS] A1: MCAP readable | 182394 messages, 5 chunks
  ✓ [PASS] A2: Required topics present | joint_states, 2 cameras, 1 actions
  ✓ [PASS] B1: Timestamps monotonic | All timestamps valid and ordered
  ✓ [PASS] C1: Joint states frequency OK | 50.2 Hz
  ⚠ [WARN] C2: Low camera FPS | /camera/front/image_raw: 12.9 FPS (min 14.5 FPS)
  ✓ [PASS] D1: Camera-joint sync OK | 98.5% frames within 34.0 ms
  ✓ [PASS] E1: Joint values valid | 50000 messages, 6 joints
  ✓ [PASS] E2: Motion smoothness OK | Max jump 0.023 rad < 0.5 rad
  
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
    {
      "level": "WARN",
      "name": "C2: Low camera FPS",
      "info": "/camera/front/image_raw: 12.9 FPS (min 14.5 FPS)"
    }
  ]
}
```

## 🔧 Configuration

Edit `mcap_checker/config.py` to modify check thresholds:

```python
# Frequency thresholds
MIN_JOINT_HZ = 45.0          # Minimum Joint State frequency (Hz)
MIN_CAMERA_FPS = 14.5        # Minimum camera frame rate (FPS)

# Synchronization thresholds
MAX_SYNC_MS = 34.0           # Maximum synchronization error (ms)

# Numerical thresholds
MAX_JOINT_JUMP = 0.5         # Maximum joint jump (rad)

# Feature flags
ENABLE_VISION_CHECKS = False  # Enable visual quality checks
ENABLE_ADVANCED_CHECKS = False # Enable advanced checks
```

## 📁 Project Structure

```
mcap_checker/
├── __init__.py              # Package initialization
├── checker.py               # Main entry, coordinates all checks
├── report.py                # Report generation (terminal/JSON)
├── config.py                # Configuration file (thresholds/flags)
└── rules/                   # Check rule modules
    ├── structure.py         # A: File structure checks
    ├── timing.py            # B/C/D: Time frequency synchronization
    ├── values.py            # E/F: Numerical trajectory checks
    ├── metadata.py          # I: Metadata checks
    └── vision.py            # G: Visual quality checks
```

## 📚 Documentation

- **[Quick Start](QUICKSTART.md)** - 5-minute getting started guide (recommended reading)
- **[Design Document](Instruction.md)** - Complete check item definitions and design solutions
- **[API Documentation](../mcap_checker/README.md)** - Module and interface detailed descriptions
- **[Usage Examples](../example_usage.py)** - Python code examples

## 🧪 Testing

```bash
# Run installation test
python3 test_installation.py

# View MCAP file contents
python3 inspect_mcap.py demo.mcap

# Basic check (A-F, I categories)
python3 -m mcap_checker.checker demo.mcap

# Full check (A-G, I categories + advanced)
python3 -m mcap_checker.checker demo.mcap --enable-vision --enable-advanced

# Run usage examples
python3 example_usage.py
```

## 🔄 CI/CD Integration

### Exit Codes

- `0`: PASS - All checks passed
- `1`: FAIL - Hard Fail items exist
- `2`: WARN - Warning items exist but no Hard Fail

### GitHub Actions Example

```yaml
- name: Check MCAP Quality
  run: |
    python3 -m mcap_checker.checker data/*.mcap --json report.json
  
- name: Fail on Bad Data
  run: |
    # If exit code is 1 (FAIL), then fail
    if [ $? -eq 1 ]; then exit 1; fi
```

## 🛠️ Extension Development

### Adding Custom Check Rules

1. Create a new module in `rules/` directory:

```python
# rules/custom.py
def check_custom(reader, report):
    # Your check logic
    if condition:
        report.fail("Custom check failed", "details")
    else:
        report.ok("Custom check passed")
```

2. Call it in `checker.py`:

```python
from .rules import custom
custom.check_custom(reader, report)
```

## 📦 Dependencies

### Required
- `mcap >= 0.8.0` - MCAP file reading

### Optional
- `numpy >= 1.20.0` - Numerical computation (advanced features)
- `opencv-python >= 4.5.0` - Image processing (vision checks)

## ❓ FAQ

**Q: How to modify check thresholds?**  
A: Edit constants in the `mcap_checker/config.py` file.

**Q: Why are vision checks disabled by default?**  
A: Vision checks require image decoding, which is time-consuming. Use `--enable-vision` to enable.

**Q: How to batch check multiple files?**  
A: Use shell loops or write Python scripts calling `run_checks()`.

**Q: Can it be integrated into existing systems?**  
A: Yes! Supports Python API, JSON output, and standard exit codes.

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 👥 Maintainers

PrismaX QA Team

---

## 🎯 Next Steps

1. ✅ Installation test: `python3 test_installation.py`
2. 📖 Read quick start: See `Docs/QUICKSTART.md`
3. 🔍 Check file: `python3 inspect_mcap.py file.mcap`
4. 🚀 Run checks: `python3 -m mcap_checker.checker file.mcap`

**Full Documentation**: For detailed usage instructions, see [Docs/QUICKSTART.md](QUICKSTART.md)
