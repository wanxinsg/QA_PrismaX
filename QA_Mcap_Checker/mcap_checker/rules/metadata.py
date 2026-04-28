#!/usr/bin/env python3
"""
Category I rules: metadata integrity (data governance).
Corresponds to the I1 checks in Instruction.md.
"""

from typing import Any
from ..config import REQUIRED_METADATA_FIELDS


def check_metadata(reader: Any, report: Any) -> None:
    """
    I1: Metadata field checks.
    - Required fields present.
    - episode_id uniqueness (needs external database support).
    """
    # Collect all metadata
    all_metadata = {}
    metadata_count = 0
    
    try:
        for record in reader.iter_metadata():
            metadata_count += 1
            # Merge all metadata records
            if record.metadata:
                all_metadata.update(record.metadata)
            # Record metadata name as a special field
            if record.name:
                all_metadata[f'_metadata_name_{metadata_count}'] = record.name
    except Exception as e:
        report.warn("I1: Cannot read metadata", str(e))
        return
    
    if not all_metadata:
        report.warn("I1: No metadata found", "MCAP has no metadata section")
        return
    
    # Report how many metadata records were found
    report.ok("I1: Metadata found", f"{metadata_count} metadata records, {len(all_metadata)} fields")
    
    # Check required fields
    missing_fields = []
    found_fields = []
    
    # Check if task_id exists (if so, episode_id is optional)
    has_task_id = 'task_id' in all_metadata
    
    for field in REQUIRED_METADATA_FIELDS:
        # If task_id exists, skip episode_id requirement
        if field == 'episode_id' and has_task_id:
            continue
        
        # Check whether field exists (supports quoted values)
        if field in all_metadata:
            found_fields.append(field)
        else:
            missing_fields.append(field)
    
    if missing_fields:
        report.warn("I1: Missing required metadata fields", f"{', '.join(missing_fields)}")
    
    if found_fields:
        report.ok("I1: Found metadata fields", f"{', '.join(found_fields)}")
    
    # Check common useful fields
    task_name = all_metadata.get('task_name', '').strip('"')
    if task_name:
        report.ok("I1: Task name", task_name)
    
    task_id = all_metadata.get('task_id', '').strip('"')
    if task_id:
        report.ok("I1: Task ID", task_id)
    
    operator = all_metadata.get('operator', '').strip('"')
    if operator:
        report.ok("I1: Operator", operator)
    
    station = all_metadata.get('station', '').strip('"')
    if station:
        report.ok("I1: Station", station)
    
    # Check episode_id (if present)
    episode_id = all_metadata.get('episode_id', '').strip('"')
    if episode_id:
        report.ok("I1: Episode ID", episode_id)


def check_metadata_consistency(metadata: dict, report: Any) -> None:
    """
    Additional metadata consistency checks.
    - Data types correct.
    - Values within reasonable ranges.
    """
    # arm_dof should be numeric
    arm_dof = metadata.get('arm_dof')
    if arm_dof:
        try:
            dof = int(arm_dof)
            if dof < 3 or dof > 10:
                report.warn("I1: Unusual arm_dof", 
                           f"{dof} DOF (typical range: 3-10)")
        except (ValueError, TypeError):
            report.warn("I1: Invalid arm_dof type", f"Expected int, got {type(arm_dof)}")
    
    # control_mode should be one of known types
    control_mode = metadata.get('control_mode')
    if control_mode:
        valid_modes = ['position', 'velocity', 'torque', 'impedance', 'cartesian']
        if control_mode.lower() not in valid_modes:
            report.warn("I1: Unknown control_mode", 
                       f"{control_mode} (expected: {', '.join(valid_modes)})")
