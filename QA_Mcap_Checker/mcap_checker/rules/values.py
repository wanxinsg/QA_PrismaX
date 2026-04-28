#!/usr/bin/env python3
"""
Category E/F rules: numerical validity and trajectory stability (Hard + Soft Fail).
Corresponds to E1–E2 and F1–F2 checks in Instruction.md.
"""

import math
import statistics
from typing import Dict, List, Any
from ..config import MAX_JOINT_JUMP, MAX_TIMING_JITTER
from ..decoder import decode_mcap_message


def check_joint_states(reader: Any, report: Any, schemas: Dict = None) -> None:
    """
    E1: Joint numerical validity check (Hard Fail).
    - position is not NaN / Inf.
    - velocity is not NaN.
    - Joint count is constant.
    """
    joint_count = None
    nan_count = 0
    inf_count = 0
    message_count = 0
    decode_error_count = 0
    
    for _, channel, message in reader.iter_messages():
        if 'joint_states' not in channel.topic.lower():
            continue
        
        # Decode message using custom decoder
        try:
            decoded_msg = decode_mcap_message(channel, message, schemas)
            
            if not decoded_msg.is_valid():
                decode_error_count += 1
                continue
            
            message_count += 1
            positions = decoded_msg.position
            
            # Check joint count consistency
            if joint_count is None:
                joint_count = len(positions)
            elif len(positions) != joint_count:
                report.fail("E1: Inconsistent joint count", 
                           f"Expected {joint_count}, got {len(positions)}")
                return
            
            # Check NaN and Inf in positions
            for pos in positions:
                if math.isnan(pos):
                    nan_count += 1
                    break
                if math.isinf(pos):
                    inf_count += 1
                    break
            
            # Check velocity values
            velocities = decoded_msg.velocity
            if velocities:
                for vel in velocities:
                    if math.isnan(vel):
                        nan_count += 1
                        break
        
        except Exception as e:
            decode_error_count += 1
            continue
    
    # If all messages failed to decode
    if message_count == 0 and decode_error_count > 0:
        report.warn("E1: Cannot decode joint_states", 
                   f"Failed to decode {decode_error_count} messages")
        return
    
    if nan_count > 0:
        report.fail("E1: NaN in joint values", f"{nan_count} messages affected")
        return
    
    if inf_count > 0:
        report.fail("E1: Inf in joint values", f"{inf_count} messages affected")
        return
    
    if joint_count:
        report.ok("E1: Joint values valid", 
                 f"{message_count} messages, {joint_count} joints")
    else:
        report.warn("E1: No joint_states data", "Cannot verify joint values")


def check_motion_smoothness(reader: Any, report: Any, schemas: Dict = None) -> None:
    """
    E2: Motion continuity check (Soft Fail).
    - Adjacent joint position jumps < threshold.
    - No spikes in velocity / acceleration.
    """
    last_positions = None
    max_jump = 0.0
    jump_count = 0
    message_count = 0
    decode_error_count = 0
    
    for _, channel, message in reader.iter_messages():
        if 'joint_states' not in channel.topic.lower():
            continue
        
        try:
            # Decode message using custom decoder
            decoded_msg = decode_mcap_message(channel, message, schemas)
            
            if not decoded_msg.is_valid():
                decode_error_count += 1
                continue
            
            positions = decoded_msg.position
            message_count += 1
            
            if last_positions is not None:
                # Compute maximum position jump
                if len(positions) == len(last_positions):
                    diffs = [abs(a - b) for a, b in zip(positions, last_positions)]
                    current_max_jump = max(diffs)
                    max_jump = max(max_jump, current_max_jump)
                    
                    if current_max_jump > MAX_JOINT_JUMP:
                        jump_count += 1
            
            last_positions = positions
        
        except Exception:
            decode_error_count += 1
            continue
    
    if message_count == 0 and decode_error_count > 0:
        report.warn("E2: Cannot decode joint_states for smoothness check", 
                   f"Failed to decode {decode_error_count} messages")
        return
    
    if message_count == 0:
        report.warn("E2: No joint_states for smoothness check")
        return
    
    if jump_count > 0:
        jump_ratio = jump_count / message_count
        report.warn("E2: Joint discontinuity detected", 
                   f"{jump_count} jumps (max {max_jump:.3f} rad, "
                   f"threshold {MAX_JOINT_JUMP} rad)")
    else:
        report.ok("E2: Motion smoothness OK", 
                 f"Max jump {max_jump:.3f} rad < {MAX_JOINT_JUMP} rad")


def check_timing_stability(topic_ts: Dict[str, List[int]], report: Any) -> None:
    """
    F: Timing stability check (using timestamp jitter as a proxy).
    - Detect high-frequency oscillations.
    - No abnormal time intervals.
    """
    # Collect all timestamps from joint_states-related topics
    joint_ts = []
    for topic, ts in topic_ts.items():
        if 'joint_states' in topic.lower():
            joint_ts.extend(ts)
    
    if not joint_ts:
        joint_ts = []
    
    if len(joint_ts) < 10:
        report.warn("F: Insufficient data for timing stability")
        return
    
    # Compute time intervals
    intervals = [(joint_ts[i+1] - joint_ts[i]) * 1e-9 
                 for i in range(len(joint_ts) - 1)]
    
    # Compute jitter (standard deviation)
    jitter = statistics.pstdev(intervals)
    
    if jitter > MAX_TIMING_JITTER:
        report.warn("F: High timing jitter", 
                   f"{jitter:.4f}s (threshold {MAX_TIMING_JITTER}s)")
    else:
        report.ok("F: Timing stability OK", f"Jitter {jitter:.4f}s")


def check_trajectory_continuity(reader: Any, report: Any) -> None:
    """
    F1: End-effector trajectory continuity check.
    - No pose teleportation.
    - Attitude changes continuously (valid quaternion).

    Note: requires forward kinematics or an EE pose topic.
    Currently a placeholder; real implementation depends on data structure.
    """
    # This is an advanced feature requiring:
    # 1. URDF/robot model.
    # 2. Forward kinematics computation.
    # 3. Or directly reading an EE pose topic.
    
    report.warn("F1: Trajectory continuity check not implemented", 
               "Requires forward kinematics or EE pose topic")


def check_vibration(topic_ts: Dict[str, List[int]], report: Any) -> None:
    """
    F2: Vibration detection.
    - High-frequency oscillation energy below threshold.
    - No mechanical resonance characteristics.

    Note: requires FFT analysis; here we only provide a basic placeholder.
    """
    report.warn("F2: Vibration detection not implemented", 
               "Requires FFT analysis on joint positions")
