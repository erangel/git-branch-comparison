"""
Git Branch Comparison Tool

An automated tool for comparing Git branches with intelligent file analysis
and comprehensive Jupyter notebook reporting.
"""

__version__ = "1.0.0"
__author__ = "Elias Rangel"
__email__ = "elias.rangel@gmail.com"

from .models import FileChange, BranchComparison
from .analyzers import FileAnalyzerFactory
from .git_comparator import GitComparator
from .report_generator import ReportGenerator

__all__ = [
    'FileChange',
    'BranchComparison', 
    'FileAnalyzerFactory',
    'GitComparator',
    'ReportGenerator',
]