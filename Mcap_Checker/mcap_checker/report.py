#!/usr/bin/env python3
"""
Unified report object.
Corresponds to section J (automatic grading) in Instruction.md.
"""

from enum import Enum
from typing import Optional, List, Tuple
import json


class Level(Enum):
    """Check result level."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class CheckReport:
    """MCAP check report."""
    
    def __init__(self, file: str):
        self.file = file
        self.items: List[Tuple[str, str, Optional[str]]] = []
        self.hard_fail = False
        self.level = None
    
    def ok(self, name: str, info: Optional[str] = None):
        """Add a passed item."""
        self.items.append(("PASS", name, info))
    
    def warn(self, name: str, info: Optional[str] = None):
        """Add a warning item (Soft Fail)."""
        self.items.append(("WARN", name, info))
    
    def fail(self, name: str, info: Optional[str] = None):
        """Add a failed item (Hard Fail)."""
        self.items.append(("FAIL", name, info))
        self.hard_fail = True
    
    def finalize(self):
        """Finalize the report and compute overall level."""
        if self.hard_fail:
            self.level = "FAIL"
        elif any(i[0] == "WARN" for i in self.items):
            self.level = "WARN"
        else:
            self.level = "PASS"
    
    def print_summary(self):
        """Print a human-readable summary to stdout."""
        print(f"\n{'='*60}")
        print(f"MCAP CHECK RESULT: {self.level}")
        print(f"{'='*60}")
        print(f"File: {self.file}\n")
        
        for lvl, name, info in self.items:
            icon = "✓" if lvl == "PASS" else "⚠" if lvl == "WARN" else "✗"
            line = f"  {icon} [{lvl}] {name}"
            if info:
                line += f" | {info}"
            print(line)
        
        print(f"\n{'='*60}")
        print(f"Summary: {len([i for i in self.items if i[0] == 'PASS'])} passed, "
              f"{len([i for i in self.items if i[0] == 'WARN'])} warnings, "
              f"{len([i for i in self.items if i[0] == 'FAIL'])} failed")
        print(f"{'='*60}\n")
    
    def to_dict(self) -> dict:
        """Convert report to a dictionary (for JSON output)."""
        return {
            "file": self.file,
            "level": self.level,
            "summary": {
                "passed": len([i for i in self.items if i[0] == "PASS"]),
                "warnings": len([i for i in self.items if i[0] == "WARN"]),
                "failed": len([i for i in self.items if i[0] == "FAIL"])
            },
            "items": [
                {
                    "level": lvl,
                    "name": name,
                    "info": info
                }
                for lvl, name, info in self.items
            ]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export report as a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def save_json(self, output_path: str):
        """Save report as a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
