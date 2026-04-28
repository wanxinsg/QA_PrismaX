#!/usr/bin/env python3
"""
Category B/C/D rules: time, frequency and synchronization (Hard + Soft Fail).
Corresponds to B1–B2, C1–C3 and D1–D2 checks in Instruction.md.
"""

from collections import defaultdict
from typing import Dict, List, Any
from ..config import (
    MIN_JOINT_HZ, MIN_CAMERA_FPS, MAX_TIME_GAP_MS,
    MAX_SYNC_MS, MAX_DESYNC_RATIO
)


def check_timestamps(reader: Any, report: Any) -> Dict[str, List[int]]:
    """
    B1: Timestamp validity check.
    - timestamp is not null.
    - Monotonically increasing within each topic.
    - No rollback / wrap.

    Returns:
        topic_ts dict for subsequent checks.
    """
    last_ts_per_channel = {}
    topic_ts = defaultdict(list)
    
    for _, channel, message in reader.iter_messages():
        ts = message.log_time
        
        # Check timestamp not null
        if ts is None or ts == 0:
            report.fail("B1: Null timestamp", f"{channel.topic}")
            return {}
        
        # Check monotonicity
        if channel.id in last_ts_per_channel:
            if ts < last_ts_per_channel[channel.id]:
                report.fail("B1: Timestamp rollback", 
                          f"{channel.topic} at {ts}")
                return {}
        
        last_ts_per_channel[channel.id] = ts
        topic_ts[channel.topic].append(ts)
    
    report.ok("B1: Timestamps monotonic", "All timestamps valid and ordered")
    return topic_ts


def check_episode_range(topic_ts: Dict[str, List[int]], summary: Any, report: Any) -> None:
    """
    B2: Episode time range check.
    - episode_start < episode_end.
    - All core topic timestamps within episode range.
    """
    if not topic_ts:
        return
    
    # Get episode time range from metadata (if available)
    metadata = summary.metadata if hasattr(summary, 'metadata') else {}
    
    episode_start = metadata.get('episode_start')
    episode_end = metadata.get('episode_end')
    
    if episode_start and episode_end:
        if episode_start >= episode_end:
            report.fail("B2: Invalid episode range", 
                       f"start={episode_start} >= end={episode_end}")
            return
        
        # Check whether core topics fall within the range
        for topic, ts_list in topic_ts.items():
            if 'joint_states' in topic or 'image' in topic:
                if ts_list[0] < episode_start or ts_list[-1] > episode_end:
                    report.warn("B2: Topic outside episode range", topic)
        
        report.ok("B2: Episode time range valid")
    else:
        report.warn("B2: No episode metadata", "Skip episode range check")


def check_frequencies(topic_ts: Dict[str, List[int]], report: Any) -> None:
    """
    C1–C3: Frequency and coverage checks.
    - C1: Joint state frequency ≥ 45 Hz.
    - C2: Camera frame rate ≥ 14.5 FPS.
    - C3: Action frequency check.
    """
    for topic, ts in topic_ts.items():
        if len(ts) < 2:
            continue
        
        # Compute frequency
        duration_sec = (ts[-1] - ts[0]) * 1e-9
        if duration_sec == 0:
            continue
        
        rate = len(ts) / duration_sec
        
        # C1: Joint states frequency check
        if "joint_states" in topic:
            if rate < MIN_JOINT_HZ:
                report.warn("C1: Low joint_states rate", 
                          f"{rate:.1f} Hz (min {MIN_JOINT_HZ} Hz)")
            else:
                report.ok("C1: Joint states frequency OK", f"{rate:.1f} Hz")
        
        # C2: Camera FPS check
        if "image" in topic:
            if rate < MIN_CAMERA_FPS:
                report.warn("C2: Low camera FPS", 
                          f"{topic}: {rate:.1f} FPS (min {MIN_CAMERA_FPS} FPS)")
            else:
                report.ok("C2: Camera FPS OK", f"{topic}: {rate:.1f} FPS")
        
        # C3: Action frequency check
        if "action" in topic or "command" in topic:
            if len(ts) < 10:
                report.warn("C3: Few action messages", 
                          f"{topic}: only {len(ts)} messages")
            else:
                report.ok("C3: Action frequency OK", 
                         f"{topic}: {rate:.1f} Hz, {len(ts)} messages")


def check_gaps(topic_ts: Dict[str, List[int]], report: Any) -> None:
    """
    C1: Drop-frame detection (time gap check).
    - No long gaps (> 200 ms).
    """
    gap_issues = []
    
    # Only check key topics (joint_states and image)
    for topic, ts in topic_ts.items():
        if len(ts) < 2:
            continue
        
        # Only check key topics
        if not ('joint_states' in topic.lower() or 'image' in topic.lower()):
            continue
        
        # Compute time gaps (convert to ms)
        gaps = [(ts[i+1] - ts[i]) * 1e-6 for i in range(len(ts) - 1)]
        max_gap = max(gaps)
        
        if max_gap > MAX_TIME_GAP_MS:
            gap_issues.append(f"{topic}: {max_gap:.1f} ms")
    
    if gap_issues:
        for issue in gap_issues[:5]:  # show only first 5
            report.warn("C1: Large time gap detected", issue)
    else:
        report.ok("C1: No large gaps in key topics", f"All gaps < {MAX_TIME_GAP_MS} ms")


def check_sync(topic_ts: Dict[str, List[int]], report: Any) -> None:
    """
    D1: Camera ↔ joint synchronization check.
    - Every image frame should match a nearest joint_state.
    - |Δt| ≤ 34 ms.
    """
    # Collect all joint_states timestamps
    joint_ts = []
    for topic, ts in topic_ts.items():
        if 'joint_states' in topic.lower():
            joint_ts.extend(ts)
    
    if not joint_ts:
        report.warn("D1: Skip sync check", "No joint_states topics found")
        return
    
    # Collect all camera timestamps
    cam_ts = []
    camera_topics = [t for t in topic_ts.keys() if "image" in t]
    for topic in camera_topics:
        cam_ts.extend(topic_ts[topic])
    
    if not cam_ts:
        report.warn("D1: Skip sync check", "No camera topics")
        return
    
    # Sort timestamps
    joint_ts = sorted(joint_ts)
    cam_ts = sorted(cam_ts)
    
    # Check synchronization
    desync_count = 0
    for img_t in cam_ts:
        # Find nearest joint_state timestamp
        nearest_joint_t = min(joint_ts, key=lambda x: abs(x - img_t))
        dt_ms = abs(nearest_joint_t - img_t) * 1e-6
        
        if dt_ms > MAX_SYNC_MS:
            desync_count += 1
    
    desync_ratio = desync_count / len(cam_ts)
    
    if desync_ratio > MAX_DESYNC_RATIO:
        report.warn("D1: Camera-joint desync", 
                   f"{desync_ratio*100:.1f}% frames > {MAX_SYNC_MS} ms")
    else:
        report.ok("D1: Camera-joint sync OK", 
                 f"{(1-desync_ratio)*100:.1f}% frames within {MAX_SYNC_MS} ms")


def check_action_alignment(topic_ts: Dict[str, List[int]], report: Any) -> None:
    """
    D2: Action ↔ state alignment check.
    - Action time ≤ state time (no future information).
    - States can respond to actions (non-static).
    """
    # Collect all joint_states timestamps
    joint_ts = []
    for topic, ts in topic_ts.items():
        if 'joint_states' in topic.lower():
            joint_ts.extend(ts)
    
    # Collect action/command timestamps
    action_ts = []
    for topic, ts in topic_ts.items():
        if "action" in topic or "command" in topic:
            action_ts.extend(ts)
    
    if not action_ts or not joint_ts:
        report.warn("D2: Skip action alignment", "Missing action or joint_states")
        return
    
    action_ts = sorted(action_ts)
    joint_ts = sorted(joint_ts)
    
    # Check if there are actions after the last joint state (future information)
    future_actions = sum(1 for at in action_ts if at > joint_ts[-1])
    
    if future_actions > len(action_ts) * 0.1:  # more than 10% of actions are in the future
        report.warn("D2: Action-state misalignment", 
                   f"{future_actions} actions after last joint state")
    else:
        report.ok("D2: Action-state alignment OK")
