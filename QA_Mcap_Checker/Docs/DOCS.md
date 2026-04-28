# 📚 Documentation Guide

## Document Locations

- **Project Root**: `README.md` - Quick overview and common commands
- **Docs/ Directory**: Detailed documentation (this directory)

## Core Documents (5)

### 0. [../README.md](../README.md) - Project Quick Overview
- Quick start
- Common commands
- Check category overview
- Documentation index

**Suitable for**: Quick understanding and daily use

---

### 1. [README.md](README.md) - Detailed Project Documentation
- Project introduction and features
- Check item list
- Quick start
- Installation instructions
- Output examples

**Suitable for**: First-time project introduction

---

### 2. [QUICKSTART.md](QUICKSTART.md) - Quick Start Guide
- 5-minute tutorial
- All commands and usage
- Python API usage
- Configuration instructions
- FAQ

**Suitable for**: Daily reference (most commonly used)

---

### 3. [Instruction.md](Instruction.md) - Design Document
- Complete check item definitions (A-J categories)
- Threshold standards
- Implementation solutions
- Code examples

**Suitable for**: Understanding design details, extension development

---

### 4. [analysis.md](analysis.md) - Original Analysis
- Initial requirements analysis
- Technical research
- Design concepts

**Suitable for**: Understanding project background

---

## Other Documents

### ../Reports/README.md - JSON Report Folder
- JSON report auto-save location
- File naming rules
- Cleanup methods

### mcap_checker/README.md - API Documentation
- Module detailed descriptions
- Function interfaces
- Usage examples

---

## Quick Navigation

```bash
# Project root quick overview
cat README.md

# Detailed usage guide
cat Docs/QUICKSTART.md

# View all check categories
grep "###" Docs/Instruction.md | head -20

# API documentation
cat mcap_checker/README.md
```

---

## Update History

- **2026-02-09**: Streamlined documentation, consolidated from 10+ documents to 4 core documents
  - Deleted: GET_STARTED.md, CHECK_CATEGORIES.md, CHECKING_GUIDE.md, COMMANDS.md, PROJECT_SUMMARY.md, SUMMARY_CHECKS.md
  - Retained: README.md, QUICKSTART.md, Instruction.md, analysis.md
  - Reason: Content duplication, scattered information, difficult to find

- **2026-02-09**: Initial version, complete document set
