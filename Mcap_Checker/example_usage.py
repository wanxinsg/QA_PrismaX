#!/usr/bin/env python3
"""
MCAP Checker usage examples.
Demonstrates how to use mcap_checker programmatically.
"""

import sys
from pathlib import Path

# Add current directory to sys.path (for local development)
sys.path.insert(0, str(Path(__file__).parent))

from mcap_checker import run_checks, CheckReport


def example_basic_usage():
    """Example 1: basic usage"""
    print("=" * 60)
    print("Example 1: basic usage")
    print("=" * 60)
    
    # Run checks
    report = run_checks("demo.mcap")
    
    # Print report
    report.print_summary()
    
    # Access results
    print(f"\nFinal level: {report.level}")
    print(f"File path: {report.file}")


def example_json_export():
    """Example 2: export JSON report"""
    print("\n" + "=" * 60)
    print("Example 2: export JSON report")
    print("=" * 60)
    
    report = run_checks("demo.mcap")
    
    # Save as JSON
    report.save_json("report.json")
    print("\n✓ JSON report saved to: report.json")
    
    # Or get JSON string directly
    json_str = report.to_json()
    print(f"\nJSON preview (first 200 chars):\n{json_str[:200]}...")


def example_programmatic_check():
    """Example 3: programmatic result handling"""
    print("\n" + "=" * 60)
    print("Example 3: programmatic result handling")
    print("=" * 60)
    
    report = run_checks("demo.mcap")
    
    # Count items by status
    passed = [item for item in report.items if item[0] == "PASS"]
    warnings = [item for item in report.items if item[0] == "WARN"]
    failed = [item for item in report.items if item[0] == "FAIL"]
    
    print(f"\n✓ Passed: {len(passed)} items")
    print(f"⚠ Warnings: {len(warnings)} items")
    print(f"✗ Failed: {len(failed)} items")
    
    # Show warning details
    if warnings:
        print("\nWarning details:")
        for _, name, info in warnings:
            print(f"  - {name}: {info or 'N/A'}")
    
    # Decide next actions based on overall level
    if report.level == "PASS":
        print("\n✓ Data quality is excellent, safe for training")
    elif report.level == "WARN":
        print("\n⚠ Data quality has issues, recommended to review before use")
    else:
        print("\n✗ Data quality is unacceptable, not recommended for use")


def example_batch_processing():
    """Example 4: batch processing multiple files"""
    print("\n" + "=" * 60)
    print("Example 4: batch processing")
    print("=" * 60)
    
    # Suppose we have multiple MCAP files
    mcap_files = [
        "demo.mcap",
        # "demo2.mcap",
        # "demo3.mcap",
    ]
    
    results = []
    
    for mcap_file in mcap_files:
        try:
            report = run_checks(mcap_file)
            results.append({
                'file': mcap_file,
                'level': report.level,
                'report': report
            })
        except Exception as e:
            print(f"✗ Check failed: {mcap_file} - {e}")
    
    # Summarize results
    print(f"\nBatch checking finished, processed {len(results)} files:\n")
    
    for result in results:
        icon = "✓" if result['level'] == "PASS" else "⚠" if result['level'] == "WARN" else "✗"
        print(f"{icon} {result['file']}: {result['level']}")


def example_custom_config():
    """Example 5: custom configuration"""
    print("\n" + "=" * 60)
    print("Example 5: custom configuration")
    print("=" * 60)
    
    # Change config (before running checks)
    from mcap_checker import config
    
    print("\nConfig before modification:")
    print(f"  MIN_JOINT_HZ = {config.MIN_JOINT_HZ}")
    print(f"  MIN_CAMERA_FPS = {config.MIN_CAMERA_FPS}")
    print(f"  MAX_SYNC_MS = {config.MAX_SYNC_MS}")
    
    # Temporarily change thresholds
    original_joint_hz = config.MIN_JOINT_HZ
    config.MIN_JOINT_HZ = 50.0  # tighten requirement
    
    print("\nConfig after modification:")
    print(f"  MIN_JOINT_HZ = {config.MIN_JOINT_HZ}")
    
    # Run checks
    report = run_checks("demo.mcap")
    
    # Restore original config
    config.MIN_JOINT_HZ = original_joint_hz
    
    print(f"\nCheck result: {report.level}")


if __name__ == "__main__":
    # Check if demo.mcap exists
    if not Path("demo.mcap").exists():
        print("⚠ Warning: demo.mcap does not exist")
        print("Please place an MCAP file in the current directory, or update the file path in the examples.\n")
    
    # Run examples (uncomment the ones you want to execute)
    
    try:
        example_basic_usage()
        # example_json_export()
        # example_programmatic_check()
        # example_batch_processing()
        # example_custom_config()
    except FileNotFoundError as e:
        print(f"\n✗ Error: file not found - {e}")
        print("Please make sure demo.mcap exists.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
