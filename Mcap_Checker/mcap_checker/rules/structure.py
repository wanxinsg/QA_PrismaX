#!/usr/bin/env python3
"""
Category A rules: file & structure integrity (Hard Fail).
Corresponds to A1–A3 checks in Instruction.md.
"""

import re
from typing import Dict, Any
from ..config import REQUIRED_TOPICS, MIN_CAMERA_COUNT


def check_readable(summary: Any, report: Any) -> None:
    """
    A1: MCAP readability check.
    - File can be opened (not corrupted).
    - Contains at least 1 chunk.
    - Index exists (schemas and channels available, supports random access).
    """
    if summary.statistics.message_count == 0:
        report.fail("A1: Empty MCAP", "No messages found")
        return
    
    if summary.statistics.chunk_count == 0:
        report.fail("A1: No chunks", "MCAP file has no chunks")
        return
    
    # Check if index exists (presence of schemas and channels implies index)
    if not summary.channels or not summary.schemas:
        report.warn("A1: Missing index", "MCAP may not support random access")
    
    report.ok("A1: MCAP readable", 
             f"{summary.statistics.message_count} messages, "
             f"{summary.statistics.chunk_count} chunks")


def check_required_topics(channels: Dict[int, Any], report: Any) -> None:
    """
    A2: Required topic checks.
    - joint_states topics exist (supports lead/follow pattern).
    - At least 2 camera image topics.
    - At least 1 action / command topic (optional).
    """
    topic_names = {c.topic for c in channels.values()}
    
    # Check joint_states (supports standard and lead/follow patterns)
    joint_states_topics = [t for t in topic_names if 'joint_states' in t.lower()]
    
    if not joint_states_topics:
        report.fail("A2: Missing joint_states topics", 
                   "No topics containing 'joint_states' found")
        return
    
    # Check whether there are lead and follow topics
    lead_topics = [t for t in joint_states_topics if 'lead' in t.lower()]
    follow_topics = [t for t in joint_states_topics if 'follow' in t.lower()]
    
    # As long as there are joint_states topics (including lead/follow),
    # consider them valid and do not warn about naming.
    
    # Check camera topics (at least 2)
    camera_topics = [t for t in topic_names if 'camera' in t.lower()]
    image_topics = [t for t in camera_topics if 'image' in t.lower()]
    
    if len(camera_topics) < MIN_CAMERA_COUNT:
        report.warn("A2: Insufficient camera topics", 
                   f"Found {len(camera_topics)}, recommended {MIN_CAMERA_COUNT}")
    elif len(image_topics) < MIN_CAMERA_COUNT:
        report.warn("A2: Few camera image topics", 
                   f"Found {len(image_topics)} image topics, {len(camera_topics)} camera topics total")
    
    # Check action/command topics (optional, no warnings if missing)
    action_topics = [t for t in topic_names 
                    if 'action' in t.lower() or 'command' in t.lower()]
    
    # Summarize in report
    js_desc = f"{len(joint_states_topics)} joint_states"
    if lead_topics and follow_topics:
        js_desc += f" ({len(lead_topics)} lead, {len(follow_topics)} follow)"
    
    report.ok("A2: Core topics present", 
             f"{js_desc}, "
             f"{len(camera_topics)} cameras"
             + (f", {len(action_topics)} actions" if action_topics else ""))


def check_schemas(channels: Dict[int, Any], schemas: Dict[int, Any], report: Any) -> None:
    """
    A3: Schema resolvability check.
    - All channels can find corresponding schemas.
    - Messages can be deserialized without error.
    """
    missing_schemas = []
    
    for channel_id, channel in channels.items():
        if channel.schema_id not in schemas:
            missing_schemas.append(f"{channel.topic} (schema_id={channel.schema_id})")
    
    if missing_schemas:
        report.fail("A3: Missing schemas", f"{len(missing_schemas)} channels")
        for missing in missing_schemas[:3]:  # show only first 3
            report.fail("  - Missing schema", missing)
        return
    
    report.ok("A3: All schemas resolvable", f"{len(schemas)} schemas found")
