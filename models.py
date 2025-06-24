"""
Data models for Git Branch Comparison Tool
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class FileChange:
    """Represents changes in a single file"""
    file_path: str
    file_type: str
    analyzer_used: str
    has_semantic_changes: bool
    has_conflicts: bool
    summary: Dict[str, int] = field(default_factory=dict)
    detailed_analysis: Dict[str, List] = field(default_factory=dict)
    format_specific: Dict[str, Any] = field(default_factory=dict)
    content_before: Optional[str] = None
    content_after: Optional[str] = None
    conflict_content: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class BranchComparison:
    """Results of comparing two branches"""
    from_branch: str
    to_branch: str
    temp_branch: str
    status: str  # 'success', 'conflict', 'error'
    changes: List[FileChange] = field(default_factory=list)
    error_message: Optional[str] = None