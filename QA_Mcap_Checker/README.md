# MCAP Checker - Robot Arm Data Quality Validation Tool

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A quality validation tool for MCAP files based on best practices for robot arm data collection.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test installation
python3 test_installation.py

# 3. Check a file
python3 -m mcap_checker.checker demo_data/demo.mcap

# 4. Full check (all A-G categories)
python3 -m mcap_checker.checker demo_data/demo.mcap --enable-vision --enable-advanced
```

## 📋 Check Categories

| Category | Checks | Enabled by Default |
|----------|--------|-------------------|
| **A** | File Structure (3 items) | ✅ |
| **B** | Time Consistency (2 items) | ✅ |
| **C** | Frequency Coverage (3+ items) | ✅ |
| **D** | Multi-modal Synchronization (2 items) | ✅ |
| **E** | Numerical Validity (2 items) | ✅ |
| **F** | Time Stability (1 item) | ✅ |
| **F1-F2** | Advanced Features (2 items) | `--enable-advanced` |
| **G** | Visual Quality (2 items) | `--enable-vision` |
| **I** | Metadata (1 item) | ✅ |

**Total**: 20+ checks

## 💻 Common Commands

```bash
# Basic check
python3 -m mcap_checker.checker file.mcap

# View file contents
python3 inspect_mcap.py file.mcap

# Check and auto-generate JSON report (saved to Reports/ folder)
python3 -m mcap_checker.checker file.mcap

# Custom JSON output path
python3 -m mcap_checker.checker file.mcap --json /custom/path/report.json

# Batch check
for file in data/*.mcap; do
    python3 -m mcap_checker.checker "$file"
done
```

## 🐍 Python API

```python
from mcap_checker import run_checks

# Run checks
report = run_checks("file.mcap")

# View results
print(f"Result: {report.level}")  # PASS / WARN / FAIL

# Custom save report (optional)
report.save_json("custom_path/report.json")

# Note: When running from command line, JSON reports are automatically saved to Reports/ folder
```

## 📊 Output Example

```
============================================================
MCAP CHECK RESULT: WARN
============================================================
File: demo_data/demo.mcap

  ✓ [PASS] A1: MCAP readable | 41503 messages
  ⚠ [WARN] C2: Low camera FPS | 12.9 FPS
  ✓ [PASS] D1: Camera-joint sync OK

============================================================
Summary: 9 passed, 9 warnings, 0 failed
============================================================
```

## 🔧 Configuration

Edit `mcap_checker/config.py` to modify thresholds:

```python
MIN_JOINT_HZ = 45.0      # Minimum Joint State frequency (Hz)
MIN_CAMERA_FPS = 14.5    # Minimum camera frame rate (FPS)
MAX_SYNC_MS = 34.0       # Maximum synchronization error (ms)
```

## 📚 Full Documentation

- **[Quick Start Guide](Docs/QUICKSTART.md)** - Detailed commands and usage (recommended)
- **[Design Document](Docs/Instruction.md)** - Complete check item definitions
- **[Documentation Navigation](Docs/DOCS.md)** - All documentation descriptions
- **[API Documentation](mcap_checker/README.md)** - Module interface descriptions

## 🛠️ Utility Scripts

- `test_installation.py` - Test installation
- `inspect_mcap.py` - View MCAP file contents
- `example_usage.py` - Python usage examples

## 📂 Project Structure

```
mcap_checker/
├── Docs/                  # 📚 Documentation
│   ├── README.md          # Complete project documentation
│   ├── QUICKSTART.md      # Quick start guide
│   ├── Instruction.md     # Design document
│   └── DOCS.md            # Documentation navigation
├── Reports/               # 📊 JSON report output folder
│   └── *.json             # Auto-generated check reports
├── mcap_checker/          # Core code
│   ├── checker.py         # Main checker
│   ├── config.py          # Configuration
│   ├── report.py          # Report generation
│   ├── decoder.py         # ROS2 message parsing
│   └── rules/             # Check rules
├── demo_data/             # Example data
├── test_installation.py   # Installation test
├── inspect_mcap.py        # File viewer tool
└── example_usage.py       # Usage examples
```

## ❓ FAQ

**Q: How to view all check categories?**  
A: `python3 -m mcap_checker.checker file.mcap --enable-vision --enable-advanced`

**Q: How to modify check thresholds?**  
A: Edit the `mcap_checker/config.py` file

**Q: Does it support batch checking?**  
A: Yes, you can use shell loops or Python API

**Q: How to integrate into CI/CD?**  
A: Judge by exit codes: 0=PASS, 1=FAIL, 2=WARN

## 🎯 Exit Codes

- `0` - PASS: All checks passed
- `1` - FAIL: Hard Fail items exist
- `2` - WARN: Warnings exist but no Hard Fail

## 📝 Changelog

### v1.1.0 (2026-02-09)
- ✅ All A-G category checks are visible
- ✅ Support for non-standard topic names
- ✅ Improved error handling
- 📚 Streamlined documentation structure

### v1.0.0 (2026-02-09)
- 🎉 Initial version release

## 📞 Get Help

- Quick reference: `cat Docs/QUICKSTART.md`
- Detailed documentation: Check `Docs/` directory
- Usage examples: `python3 example_usage.py`

---

**License**: MIT  
**Author**: PrismaX QA Team
