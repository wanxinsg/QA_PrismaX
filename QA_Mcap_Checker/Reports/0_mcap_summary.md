# MCAP Summary: `0.mcap`

- **File path**: `/Users/wanxin/Downloads/Mcap/Airbot数据采集/zd-20260205/0.mcap`

## Topics (Channels)

| Channel ID | Topic | Message Encoding | Schema ID | Schema Name | Message Count |
| --- | --- | --- | --- | --- | --- |
| 1 | `/robot/arm_left_lead/joint_states` | `cdr` | 1 | `sensor_msgs/msg/JointState` | 4106 |
| 2 | `/robot/arm_left_follow/joint_states` | `cdr` | 1 | `sensor_msgs/msg/JointState` | 4106 |
| 3 | `/robot/arm_right_lead/joint_states` | `cdr` | 1 | `sensor_msgs/msg/JointState` | 4106 |
| 4 | `/robot/arm_right_follow/joint_states` | `cdr` | 1 | `sensor_msgs/msg/JointState` | 4106 |
| 5 | `/robot/left_camera/image_raw/compressed/camera_info` | `cdr` | 2 | `sensor_msgs/msg/CameraInfo` | 1 |
| 6 | `/robot/env_camera/image_raw/compressed/camera_info` | `cdr` | 2 | `sensor_msgs/msg/CameraInfo` | 1 |
| 7 | `/robot/right_camera/image_raw/compressed/camera_info` | `cdr` | 2 | `sensor_msgs/msg/CameraInfo` | 1 |

## Schemas

### Schema 1: `sensor_msgs/msg/JointState`

- **Encoding**: `ros2msg`
- **Byte size**: 1954

```
# This is a message that holds data to describe the state of a set of torque controlled joints.
#
# The state of each joint (revolute or prismatic) is defined by:
#  * the position of the joint (rad or m),
#  * the velocity of the joint (rad/s or m/s) and
#  * the effort that is applied in the joint (Nm or N).
#
# Each joint is uniquely identified by its name
# The header specifies the time at which the joint states were recorded. All the joint states
# in one message have to be recorded at the same time.
#
# This message consists of a multiple arrays, one for each part of the joint state.
# The goal is to make each of the fields optional. When e.g. your joints have no
# effort associated with them, you can leave the effort array empty.
#
# All arrays in this message should have the same size, or be empty.
# This is the only way to uniquely associate the joint name with the correct
# states.

std_msgs/Header header

string[] name
float64[] position
float64[] velocity
float64[] effort

================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data
# in a particular coordinate frame.

# Two-integer timestamp that is expressed as seconds and nanoseconds.
builtin_interfaces/Time stamp

# Transform frame with which this data is associated.
string frame_id

================================================================================
MSG: builtin_interfaces/Time
# This message communicates ROS Time defined here:
# https://design.ros2.org/articles/clock_and_time.html

# The seconds component, valid over all int32 values.
int32 sec

# The nanoseconds component, valid in the range [0, 1e9), to be added to the seconds component.
# e.g.
# The time -1.7 seconds is represented as {sec: -2, nanosec: 3e8}
# The time 1.7 seconds is represented as {sec: 1, nanosec: 7e8}
uint32 nanosec
```

### Schema 2: `sensor_msgs/msg/CameraInfo`

- **Encoding**: `ros2msg`
- **Byte size**: 8294

```
# This message defines meta information for a camera. It should be in a
# camera namespace on topic "camera_info" and accompanied by up to five
# image topics named:
#
#   image_raw - raw data from the camera driver, possibly Bayer encoded
#   image            - monochrome, distorted
#   image_color      - color, distorted
#   image_rect       - monochrome, rectified
#   image_rect_color - color, rectified
#
# The image_pipeline contains packages (image_proc, stereo_image_proc)
# for producing the four processed image topics from image_raw and
# camera_info. The meaning of the camera parameters are described in
# detail at http://www.ros.org/wiki/image_pipeline/CameraInfo.
#
# The image_geometry package provides a user-friendly interface to
# common operations using this meta information. If you want to, e.g.,
# project a 3d point into image coordinates, we strongly recommend
# using image_geometry.
#
# If the camera is uncalibrated, the matrices D, K, R, P should be left
# zeroed out. In particular, clients may assume that K[0] == 0.0
# indicates an uncalibrated camera.

#######################################################################
#                     Image acquisition info                          #
#######################################################################

# Time of image acquisition, camera coordinate frame ID
std_msgs/Header header # Header timestamp should be acquisition time of image
                             # Header frame_id should be optical frame of camera
                             # origin of frame should be optical center of camera
                             # +x should point to the right in the image
                             # +y should point down in the image
                             # +z should point into the plane of the image


#######################################################################
#                      Calibration Parameters                         #
#######################################################################
# These are fixed during camera calibration. Their values will be the #
# same in all messages until the camera is recalibrated. Note that    #
# self-calibrating systems may "recalibrate" frequently.              #
#                                                                     #
# The internal parameters can be used to warp a raw (distorted) image #
# to:                                                                 #
#   1. An undistorted image (requires D and K)                        #
#   2. A rectified image (requires D, K, R)                           #
# The projection matrix P projects 3D points into the rectified image.#
#######################################################################

# The image dimensions with which the camera was calibrated.
# Normally this will be the full camera resolution in pixels.
uint32 height
uint32 width

# The distortion model used. Supported models are listed in
# sensor_msgs/distortion_models.hpp. For most cameras, "plumb_bob" - a
# simple model of radial and tangential distortion - is sufficent.
string distortion_model

# The distortion parameters, size depending on the distortion model.
# For "plumb_bob", the 5 parameters are: (k1, k2, t1, t2, k3).
float64[] d

# Intrinsic camera matrix for the raw (distorted) images.
#     [fx  0 cx]
# K = [ 0 fy cy]
#     [ 0  0  1]
# Projects 3D points in the camera coordinate frame to 2D pixel
# coordinates using the focal lengths (fx, fy) and principal point
# (cx, cy).
float64[9]  k # 3x3 row-major matrix

# Rectification matrix (stereo cameras only)
# A rotation matrix aligning the camera coordinate system to the ideal
# stereo image plane so that epipolar lines in both stereo images are
# parallel.
float64[9]  r # 3x3 row-major matrix

# Projection/camera matrix
#     [fx'  0  cx' Tx]
# P = [ 0  fy' cy' Ty]
#     [ 0   0   1   0]
# By convention, this matrix specifies the intrinsic (camera) matrix
#  of the processed (rectified) image. That is, the left 3x3 portion
#  is the normal camera intrinsic matrix for the rectified image.
# It projects 3D points in the camera coordinate frame to 2D pixel
#  coordinates using the focal lengths (fx', fy') and principal point
#  (cx', cy') - these may differ from the values in K.
# For monocular cameras, Tx = Ty = 0. Normally, monocular cameras will
#  also have R = the identity and P[1:3,1:3] = K.
# For a stereo pair, the fourth column [Tx Ty 0]' is related to the
#  position of the optical center of the second camera in the first
#  camera's frame. We assume Tz = 0 so both cameras are in the same
#  stereo image plane. The first camera always has Tx = Ty = 0. For
#  the right (second) camera of a horizontal stereo pair, Ty = 0 and
#  Tx = -fx' * B, where B is the baseline between the cameras.
# Given a 3D point [X Y Z]', the projection (x, y) of the point onto
#  the rectified image is given by:
#  [u v w]' = P * [X Y Z 1]'
#         x = u / w
#         y = v / w
#  This holds for both images of a stereo pair.
float64[12] p # 3x4 row-major matrix


#######################################################################
#                      Operational Parameters                         #
#######################################################################
# These define the image region actually captured by the camera       #
# driver. Although they affect the geometry of the output image, they #
# may be changed freely without recalibrating the camera.             #
#######################################################################

# Binning refers here to any camera setting which combines rectangular
#  neighborhoods of pixels into larger "super-pixels." It reduces the
#  resolution of the output image to
#  (width / binning_x) x (height / binning_y).
# The default values binning_x = binning_y = 0 is considered the same
#  as binning_x = binning_y = 1 (no subsampling).
uint32 binning_x
uint32 binning_y

# Region of interest (subwindow of full camera resolution), given in
#  full resolution (unbinned) image coordinates. A particular ROI
#  always denotes the same window of pixels on the camera sensor,
#  regardless of binning settings.
# The default setting of roi (all values 0) is considered the same as
#  full resolution (roi.width = width, roi.height = height).
RegionOfInterest roi

================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data
# in a particular coordinate frame.

# Two-integer timestamp that is expressed as seconds and nanoseconds.
builtin_interfaces/Time stamp

# Transform frame with which this data is associated.
string frame_id

================================================================================
MSG: builtin_interfaces/Time
# This message communicates ROS Time defined here:
# https://design.ros2.org/articles/clock_and_time.html

# The seconds component, valid over all int32 values.
int32 sec

# The nanoseconds component, valid in the range [0, 1e9), to be added to the seconds component.
# e.g.
# The time -1.7 seconds is represented as {sec: -2, nanosec: 3e8}
# The time 1.7 seconds is represented as {sec: 1, nanosec: 7e8}
uint32 nanosec

================================================================================
MSG: sensor_msgs/RegionOfInterest
# This message is used to specify a region of interest within an image.
#
# When used to specify the ROI setting of the camera when the image was
# taken, the height and width fields should either match the height and
# width fields for the associated image; or height = width = 0
# indicates that the full resolution image was captured.

uint32 x_offset  # Leftmost pixel of the ROI
                 # (0 if the ROI includes the left edge of the image)
uint32 y_offset  # Topmost pixel of the ROI
                 # (0 if the ROI includes the top edge of the image)
uint32 height    # Height of ROI
uint32 width     # Width of ROI

# True if a distinct rectified ROI should be calculated from the "raw"
# ROI in this message. Typically this should be False if the full image
# is captured (ROI not used), and True if a subwindow is captured (ROI
# used).
bool do_rectify
```

## Metadata

- **Total metadata records**: 11

### Metadata record 1

- **Name**: `version`

| Key | Value |
| --- | --- |
| `collector` | `"0.6.9"` |
| `data_schema` | `"0.0.1"` |

### Metadata record 2

- **Name**: `task_info`

| Key | Value |
| --- | --- |
| `object` | `["white T-shirt with red prints"]` |
| `operator` | `"zhengding"` |
| `scene` | `"white desktop"` |
| `skill` | `["pick", "fold", "place"]` |
| `station` | `"ptk-001"` |
| `subtasks` | `[{"skill": "pick", "description": "Pick up the randomly placed white T-shirt with red prints using the gripper."}, {"skill": "fold", "description": "Fold the picked-up T-shirt neatly according to the standard process."}, {"skill": "place", "description": "Place the neatly folded T-shirt on the designated position on the right side."}]` |
| `task_description` | `"Fold a randomly placed white T-shirt with red prints and place it on the right side."` |
| `task_id` | `"1"` |
| `task_name` | `"Fold and Place T-shirt"` |

### Metadata record 3

- **Name**: `save_type`

| Key | Value |
| --- | --- |
| `color` | `"h264"` |
| `depth` | `"raw"` |

### Metadata record 4

- **Name**: `key_remap`

| Key | Value |
| --- | --- |
| `/env_camera/color/camera_info` | `"/robot/env_camera/image_raw/compressed/camera_info"` |
| `/left/follow/arm/joint_state` | `"/robot/arm_left_follow/joint_states"` |
| `/left/lead/arm/joint_state` | `"/robot/arm_left_lead/joint_states"` |
| `/left_camera/color/camera_info` | `"/robot/left_camera/image_raw/compressed/camera_info"` |
| `/right/follow/arm/joint_state` | `"/robot/arm_right_follow/joint_states"` |
| `/right/lead/arm/joint_state` | `"/robot/arm_right_lead/joint_states"` |
| `/right_camera/color/camera_info` | `"/robot/right_camera/image_raw/compressed/camera_info"` |

### Metadata record 5

- **Name**: `video_save_to`

| Key | Value |
| --- | --- |
| `value` | `"folder"` |

### Metadata record 6

- **Name**: `av_coder`

| Key | Value |
| --- | --- |
| `async_encode` | `false` |
| `frame_format` | `"bgr24"` |
| `log_level` | `null` |
| `non_monotonic_log` | `false` |
| `non_monotonic_mode` | `"drop"` |
| `time_base` | `1000000` |

### Metadata record 7

- **Name**: `product`

| Key | Value |
| --- | --- |
| `product_name` | `"82YA"` |

### Metadata record 8

- **Name**: `cpu`

| Key | Value |
| --- | --- |
| `cores_logical` | `"20"` |
| `cores_physical` | `"14"` |
| `model_name` | `"13th Gen Intel(R) Core(TM) i7-13700H"` |

### Metadata record 9

- **Name**: `memory`

| Key | Value |
| --- | --- |
| `mem_free` | `"8304144 kB"` |
| `mem_total` | `"16089764 kB"` |
| `swap_free` | `"2097148 kB"` |
| `swap_total` | `"2097148 kB"` |

### Metadata record 10

- **Name**: `gpu`

| Key | Value |
| --- | --- |
| `device1/device_type` | `"VGA compatible controller"` |
| `device1/model` | `"Corporation Device a720"` |
| `device1/pci_address` | `"00:02.0"` |
| `device1/revision` | `""` |
| `device1/vendor` | `"Intel"` |
| `device2/device_type` | `"VGA compatible controller"` |
| `device2/model` | `"Corporation Device 28e0"` |
| `device2/pci_address` | `"01:00.0"` |
| `device2/revision` | `""` |
| `device2/vendor` | `"NVIDIA"` |

### Metadata record 11

- **Name**: `platform`

| Key | Value |
| --- | --- |
| `machine` | `"x86_64"` |
| `node` | `"discover"` |
| `processor` | `"x86_64"` |
| `release` | `"6.8.0-90-generic"` |
| `system` | `"Linux"` |
| `version` | `"#91~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Nov 20 15:20:45 UTC 2"` |

### Merged metadata fields

| Key | Value |
| --- | --- |
| `/env_camera/color/camera_info` | `"/robot/env_camera/image_raw/compressed/camera_info"` |
| `/left/follow/arm/joint_state` | `"/robot/arm_left_follow/joint_states"` |
| `/left/lead/arm/joint_state` | `"/robot/arm_left_lead/joint_states"` |
| `/left_camera/color/camera_info` | `"/robot/left_camera/image_raw/compressed/camera_info"` |
| `/right/follow/arm/joint_state` | `"/robot/arm_right_follow/joint_states"` |
| `/right/lead/arm/joint_state` | `"/robot/arm_right_lead/joint_states"` |
| `/right_camera/color/camera_info` | `"/robot/right_camera/image_raw/compressed/camera_info"` |
| `async_encode` | `false` |
| `collector` | `"0.6.9"` |
| `color` | `"h264"` |
| `cores_logical` | `"20"` |
| `cores_physical` | `"14"` |
| `data_schema` | `"0.0.1"` |
| `depth` | `"raw"` |
| `device1/device_type` | `"VGA compatible controller"` |
| `device1/model` | `"Corporation Device a720"` |
| `device1/pci_address` | `"00:02.0"` |
| `device1/revision` | `""` |
| `device1/vendor` | `"Intel"` |
| `device2/device_type` | `"VGA compatible controller"` |
| `device2/model` | `"Corporation Device 28e0"` |
| `device2/pci_address` | `"01:00.0"` |
| `device2/revision` | `""` |
| `device2/vendor` | `"NVIDIA"` |
| `frame_format` | `"bgr24"` |
| `log_level` | `null` |
| `machine` | `"x86_64"` |
| `mem_free` | `"8304144 kB"` |
| `mem_total` | `"16089764 kB"` |
| `model_name` | `"13th Gen Intel(R) Core(TM) i7-13700H"` |
| `node` | `"discover"` |
| `non_monotonic_log` | `false` |
| `non_monotonic_mode` | `"drop"` |
| `object` | `["white T-shirt with red prints"]` |
| `operator` | `"zhengding"` |
| `processor` | `"x86_64"` |
| `product_name` | `"82YA"` |
| `release` | `"6.8.0-90-generic"` |
| `scene` | `"white desktop"` |
| `skill` | `["pick", "fold", "place"]` |
| `station` | `"ptk-001"` |
| `subtasks` | `[{"skill": "pick", "description": "Pick up the randomly placed white T-shirt with red prints using the gripper."}, {"skill": "fold", "description": "Fold the picked-up T-shirt neatly according to the standard process."}, {"skill": "place", "description": "Place the neatly folded T-shirt on the designated position on the right side."}]` |
| `swap_free` | `"2097148 kB"` |
| `swap_total` | `"2097148 kB"` |
| `system` | `"Linux"` |
| `task_description` | `"Fold a randomly placed white T-shirt with red prints and place it on the right side."` |
| `task_id` | `"1"` |
| `task_name` | `"Fold and Place T-shirt"` |
| `time_base` | `1000000` |
| `value` | `"folder"` |
| `version` | `"#91~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Nov 20 15:20:45 UTC 2"` |
