#!/usr/bin/env python3
"""
MCAP robot arm data checker - main entry point.
Implements the overall design described in Instruction.md.

Usage:
    python checker.py <mcap_file> [--json output.json] [--strict]
"""

import sys
import argparse
from pathlib import Path

from mcap.reader import make_reader

from .report import CheckReport
from .rules import structure, timing, values, metadata
from . import config


def run_checks(mcap_path: str, strict_mode: bool = False) -> CheckReport:
    """
    Run all MCAP checks.

    Args:
        mcap_path: Path to MCAP file.
        strict_mode: Whether to enable strict mode.

    Returns:
        CheckReport instance.
    """
    report = CheckReport(mcap_path)
    
    # Try to open file
    try:
        f = open(mcap_path, "rb")
    except FileNotFoundError:
        report.fail("File not found", mcap_path)
        report.finalize()
        return report
    except Exception as e:
        report.fail("Cannot open file", str(e))
        report.finalize()
        return report
    
    with f:
        try:
            reader = make_reader(f)
            summary = reader.get_summary()
        except Exception as e:
            report.fail("Cannot read MCAP", str(e))
            report.finalize()
            return report
        
        channels = summary.channels
        schemas = summary.schemas
        
        # ============================================
        # A. File & structural integrity (Hard Fail)
        # ============================================
        structure.check_readable(summary, report)
        
        # If file is not readable, return immediately
        if report.hard_fail:
            report.finalize()
            return report
        
        structure.check_required_topics(channels, report)
        structure.check_schemas(channels, schemas, report)
        
        # Remember whether structural checks failed (but continue with other checks)
        structure_failed = report.hard_fail
        
        # ============================================
        # B/C/D. Time, frequency & synchronization (Hard + Soft)
        # ============================================
        # B1: Timestamp checks (also collect topic_ts)
        topic_ts = {}
        try:
            topic_ts = timing.check_timestamps(reader, report)
        except Exception as e:
            report.warn("B1: Timestamp check error", str(e))
        
        # B2: Episode range check
        if topic_ts:
            try:
                timing.check_episode_range(topic_ts, summary, report)
            except Exception as e:
                report.warn("B2: Episode range check error", str(e))
        
        # C1-C3: Frequency checks
        if topic_ts:
            try:
                timing.check_frequencies(topic_ts, report)
                timing.check_gaps(topic_ts, report)
            except Exception as e:
                report.warn("C: Frequency check error", str(e))
        
        # D1-D2: Synchronization checks
        if topic_ts:
            try:
                timing.check_sync(topic_ts, report)
                timing.check_action_alignment(topic_ts, report)
            except Exception as e:
                report.warn("D: Sync check error", str(e))
        
        # ============================================
        # E/F. Numerical values & trajectory (Hard + Soft)
        # ============================================
        # E1-E2: Joint numerical checks (needs schemas)
        try:
            with open(mcap_path, "rb") as f2:
                reader2 = make_reader(f2)
                summary2 = reader2.get_summary()
                values.check_joint_states(reader2, report, summary2.schemas)
        except Exception as e:
            report.warn("E1: Joint states check error", str(e))
        
        # Motion continuity check
        try:
            with open(mcap_path, "rb") as f3:
                reader3 = make_reader(f3)
                summary3 = reader3.get_summary()
                values.check_motion_smoothness(reader3, report, summary3.schemas)
        except Exception as e:
            report.warn("E2: Motion smoothness check error", str(e))
        
        # F: Timing stability
        if topic_ts:
            try:
                values.check_timing_stability(topic_ts, report)
            except Exception as e:
                report.warn("F: Timing stability check error", str(e))
        
        # F1-F2: Advanced checks (if enabled)
        if config.ENABLE_ADVANCED_CHECKS:
            try:
                with open(mcap_path, "rb") as f4:
                    reader4 = make_reader(f4)
                    values.check_trajectory_continuity(reader4, report)
                values.check_vibration(topic_ts, report)
            except Exception as e:
                report.warn("F: Advanced check error", str(e))
        
        # ============================================
        # G. Vision quality (if enabled)
        # ============================================
        if config.ENABLE_VISION_CHECKS:
            try:
                from .rules import vision
                with open(mcap_path, "rb") as f5:
                    reader5 = make_reader(f5)
                    vision.check_image_integrity(reader5, report)
                    vision.check_illumination(reader5, report)
            except Exception as e:
                report.warn("G: Vision check error", str(e))
        
        # ============================================
        # I. Metadata integrity
        # ============================================
        try:
            with open(mcap_path, "rb") as f6:
                reader6 = make_reader(f6)
                metadata.check_metadata(reader6, report)
        except Exception as e:
            report.warn("I: Metadata check error", str(e))
    
    # ============================================
    # J. Final grading
    # ============================================
    report.finalize()
    return report


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="MCAP Robot Arm Data Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mcap_checker.checker demo.mcap
  python -m mcap_checker.checker demo.mcap --json report.json
  python -m mcap_checker.checker demo.mcap --strict
        """
    )
    
    parser.add_argument("mcap_file", help="Path to MCAP file")
    parser.add_argument("--json", "-j", 
                       help="Output JSON report to file")
    parser.add_argument("--strict", "-s", action="store_true",
                       help="Enable strict mode (more checks as Hard Fail)")
    parser.add_argument("--enable-vision", action="store_true",
                       help="Enable vision quality checks (slow)")
    parser.add_argument("--enable-advanced", action="store_true",
                       help="Enable advanced checks (trajectory, vibration)")
    
    args = parser.parse_args()
    
    # Update config flags
    if args.strict:
        config.ENABLE_STRICT_MODE = True
    if args.enable_vision:
        config.ENABLE_VISION_CHECKS = True
    if args.enable_advanced:
        config.ENABLE_ADVANCED_CHECKS = True
    
    # Check file exists
    mcap_path = Path(args.mcap_file)
    if not mcap_path.exists():
        print(f"Error: File not found: {mcap_path}")
        sys.exit(1)
    
    # Run checks
    report = run_checks(str(mcap_path), strict_mode=args.strict)
    
    # Print summary
    report.print_summary()
    
    # Save JSON report
    if args.json:
        # User specified an explicit output path
        json_output = args.json
    else:
        # Auto-save into Reports folder
        # Use project root (parent of this file's directory)
        project_root = Path(__file__).parent.parent
        reports_dir = project_root / "Reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Generate JSON file name (based on input file name)
        mcap_filename = mcap_path.stem  # file name without extension
        json_output = reports_dir / f"{mcap_filename}_report.json"
    
    report.save_json(str(json_output))
    print(f"\n✓ JSON report saved to: {json_output}")
    
    # Set exit code based on result level
    exit_code = 0
    if report.level == "FAIL":
        exit_code = 1
    elif report.level == "WARN":
        exit_code = 2
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
