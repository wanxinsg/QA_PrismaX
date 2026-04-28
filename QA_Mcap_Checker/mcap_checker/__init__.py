#!/usr/bin/env python3
"""
MCAP Robot Arm Data Checker.
Modular validation system for robot arm MCAP data, designed according to Instruction.md.
"""

__version__ = "1.0.0"
__author__ = "PrismaX QA Team"

from .checker import run_checks
from .report import CheckReport

__all__ = ['run_checks', 'CheckReport']
