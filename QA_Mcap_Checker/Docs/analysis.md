# MCAP Data Structure Description

Generally, an MCAP (Machine-Generated Data Container) file is essentially a high-performance, scalable log container, commonly used in ROS / robotics / autonomous driving / robot arms / sensor systems. It typically contains the following "layers" of content.

## I. Basic Structure Layer (All MCAP files have)

These are **container-level** things that exist regardless of what data you store:

### 1️⃣ Channel

Defines "what this data stream is"

Includes:
- topic name (e.g., `/camera/front/image_raw`)
- message type (e.g., `sensor_msgs/Image`)
- encoding (cdr, protobuf, json, etc.)

Similar to: Data specification sheet

### 2️⃣ Schema (Structure Definition)

Describes the field structure of messages

For ROS, this means:
- `.msg` definitions
- `.idl` / `.proto`

Purpose: Tells you how to parse this message

### 3️⃣ Message (Actual Data)

Specific data stored in chronological order

Each has:
- timestamp (log time / publish time)
- channel_id
- Raw payload (binary)

## II. Time & Synchronization Related Content (Very Important)

### 4️⃣ Timestamps

Usually at least two types:
- `log_time`: Time when written to MCAP
- `publish_time`: Time when device or ROS node generated data

👉 Used for:
- Multi-sensor alignment
- Latency analysis
- Temporal consistency checks

### 5️⃣ Clock / Time Reference (Some datasets have)

- `/clock` topic (common in simulation environments)
- External time sources (GPS time, PTP)

## III. Most Common Data Types in Robotics / Autonomous Driving

### 6️⃣ Pose / Motion State

- Odometry
- PoseStamped
- TF / TFStatic
- JointState (robot arm joint angles)

👉 Used for:
- Trajectory reconstruction
- Drift evaluation
- Motion smoothness analysis

### 7️⃣ Sensor Data (Main body of MCAP)

**📷 Camera**
- Image
- CompressedImage
- CameraInfo
- Multi-view / multi-perspective

**🌐 LiDAR / Depth**
- PointCloud2
- LaserScan
- Depth image

**🧭 IMU / Odometry**
- Imu
- Wheel odometry

**🎤 Others**
- Microphone
- Force sensors (Force / Wrench)
- Tactile, pressure arrays

### 8️⃣ Control / Behavior Data (Critical for imitation / RL)

- `cmd_vel`
- Robot arm FollowJointTrajectory
- Gripper open / close
- action / command topics

## IV. Task & Semantic Layer (Only high-quality datasets have)

### 9️⃣ Task Annotation / Events

- task start / end
- success / failure
- grasp success
- contact detect

### 🔟 Semantic / Annotation Information

- bounding boxes
- segmentation masks
- object id / class
- affordance

👉 Many benchmarks / datasets store these as separate topics in MCAP

## V. Metadata (Often Overlooked but Very Valuable)

### 1️⃣1️⃣ Metadata

- Recording environment (indoor / outdoor)
- Device model
- Operator / policy name
- Task description (natural language)
- episode id / scene id

### 1️⃣2️⃣ Statistics / Index (MCAP Unique Advantage)

- message index
- chunk index
- Compression information (zstd / lz4)
- Fast random access support

## VI. One-Sentence Summary 🧠

A typical MCAP =

- Time-synchronized multi-sensor data
- Motion state / control signals
- Structured schema
- Rich metadata
- Efficient indexing

---

# Robot Arm MCAP Standard Content Template (Recommended)

## I. Basic Information (Required)

### 1️⃣ Metadata: Doesn't consume bandwidth, but extremely important

**Required field examples:**
- `dataset_name`: `pick_and_place_v1`
- `robot_model`: `franka_panda`
- `arm_dof`: `7`
- `gripper_type`: `parallel`
- `control_mode`: `joint_position`
- `operator`: `human_demo` / `policy_v3`
- `environment`: `tabletop_indoor`
- `episode_id`: `ep_000123`
- `task_description`: "Pick the red cube and place it in the tray"

**Uses:**
- Data filtering
- Task reproduction
- Train set / test set splitting

## II. Timing & Synchronization (Required)

### 2️⃣ Time System

| Content | Topic | Required |
|---------|-------|----------|
| Unified time reference | `/clock` or system time | ✅ |
| Multi-topic synchronization capability | timestamps | ✅ |

## III. Robot Arm State (Required)

### 3️⃣ Joint State (Joint-level)

**Topic:** `/joint_states`  
**Type:** `sensor_msgs/JointState`

**Field requirements:**
- `position` ✅
- `velocity` ✅ (strongly recommended)
- `effort` ⚠️ (optional)

**Frequency:**
- ≥ 50 Hz (recommended 100 Hz)

### 4️⃣ End-effector Pose

**Topic:** `/ee_pose`  
**Type:** `geometry_msgs/PoseStamped`

Or:
- `/tf` - `tf2_msgs/TFMessage`
- `/tf_static`

**Requirements:**
- World coordinate frame clear (e.g., `base_link`)
- Pose continuous, no jumps

## IV. Perception Data (Required)

### 5️⃣ Camera (At least one view)

**RGB:**
- `/camera/front/image_raw` - `sensor_msgs/Image`
- `/camera/front/camera_info`

**Depth (if available):**
- `/camera/front/depth/image_raw`

**Minimum standards:**
- ≥ 15 FPS
- Images throughout
- Aligned with action time (< 30–40 ms)

## V. Control / Action Signals (Required)

### 6️⃣ Action / Command

- `/arm_controller/command`
- `/gripper/command`

Or abstract actions:
- `/action/joint_target`
- `/action/ee_delta`

This is the "label" for imitation learning

## VI. Task Boundaries & Events (Strongly Recommended)

### 7️⃣ Episode / Phase Marking

- `/episode_start` - `std_msgs/Bool`
- `/episode_end` - `std_msgs/Bool`
- `/phase` - `std_msgs/String`

Examples:
- `approach` → `grasp` → `lift` → `place` → `retreat`

### 8️⃣ Success / Failure Signals

- `/task_success` - `std_msgs/Bool`
- `/grasp_success` - `std_msgs/Bool`
- `/failure_reason` - `std_msgs/String`

## VII. Contact & Force Sensing (Strongly Recommended)

### 9️⃣ Force / Torque (If hardware supports)

- `/wrench` - `geometry_msgs/WrenchStamped`

Or:
- `/gripper/force`

## VIII. Environment & Semantics (Advanced Optional)

### 🔟 Object State

- `/object_pose/<id>` - `geometry_msgs/PoseStamped`

### 🔟 Visual Annotation

- `/bbox`
- `/segmentation_mask`
- `/object_id`

## IX. Quality Assurance (Dataset-level Strongly Recommended)

### 1️⃣1️⃣ Data Quality Metrics (Can be stored as metadata)

- `avg_camera_fps`: `29.8`
- `imu_rate`: `200`
- `odometry_drift`: `1.2%`
- `camera_sync_error_ms`: `18`
- `missing_frames`: `false`

## X. Recommended Topic Overview Table (Simplified)

| Category | Topic | Required |
|----------|-------|----------|
| Metadata | `/metadata` | ✅ |
| Joint | `/joint_states` | ✅ |
| EE Pose | `/ee_pose` or `/tf` | ✅ |
| RGB | `/camera/*` | ✅ |
| Action | `/arm_controller/command` | ✅ |
| Episode | `/episode_*` | ⭐ |
| Success | `/task_success` | ⭐ |
| Force | `/wrench` | ⭐ |
| Labels | `/segmentation` | ⭕ |
