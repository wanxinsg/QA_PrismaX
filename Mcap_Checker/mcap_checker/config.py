#!/usr/bin/env python3
"""
Configuration file - thresholds and rule switches.
Corresponds to the checklist threshold definitions in Instruction.md.
"""

# =========================
# A. File & structure integrity
# =========================
REQUIRED_TOPICS = [
    "/joint_states",
]

# Optional: stricter topic checks
CAMERA_TOPIC_PATTERN = r"/camera/.*/image_raw"
ACTION_TOPIC_PATTERNS = [
    r"/arm_controller/command",
    r"/action/.*"
]

MIN_CAMERA_COUNT = 2  # At least 2 camera topics

# =========================
# B/C. Time & frequency
# =========================
MIN_JOINT_HZ = 45.0          # C1: Minimum joint state frequency (Hz)
MIN_CAMERA_FPS = 14.5        # C2: Minimum camera frame rate (FPS)
MAX_TIME_GAP_MS = 200.0      # C1: Maximum time gap (ms), for drop-frame detection

# =========================
# D. Multi-modal synchronization
# =========================
MAX_SYNC_MS = 34.0           # D1: Max camera–joint sync error (ms)
MAX_DESYNC_RATIO = 0.05      # Allow up to 5% frames beyond sync threshold

# =========================
# E. Numerical validity
# =========================
MAX_JOINT_JUMP = 0.5         # E2: Maximum joint jump (rad)
MAX_TIMING_JITTER = 0.02     # F: Timestamp jitter threshold (seconds)

# =========================
# I. Metadata
# =========================
REQUIRED_METADATA_FIELDS = [
    "robot_model",
    "arm_dof",
    "control_mode",
    "task_description",
    "episode_id",
]

# =========================
# Rule switches (advanced usage)
# =========================
ENABLE_STRICT_MODE = False     # Strict mode: more checks treated as Hard Fail
ENABLE_VISION_CHECKS = False   # Enable vision quality checks (requires image decoding)
ENABLE_ADVANCED_CHECKS = False # Enable advanced checks (trajectory, vibration, etc.)
