"""Tests for models module."""

import pytest
from git_branch_comparison.models import FileChange, BranchComparison


def test_file_change_creation():
    """Test FileChange model creation."""
    change = FileChange(
        file_path="test.py",
        file_type=".py",
        analyzer_used="BaseAnalyzer",
        has_semantic_changes=True,
        has_conflicts=False
    )
    
    assert change.file_path == "test.py"
    assert change.file_type == ".py"
    assert change.analyzer_used == "BaseAnalyzer"
    assert change.has_semantic_changes is True
    assert change.has_conflicts is False
    assert change.summary == {}
    assert change.detailed_analysis == {}
    assert change.format_specific == {}


def test_file_change_with_content():
    """Test FileChange with content."""
    change = FileChange(
        file_path="example.txt",
        file_type=".txt",
        analyzer_used="BaseAnalyzer",
        has_semantic_changes=True,
        has_conflicts=False,
        content_before="old content",
        content_after="new content"
    )
    
    assert change.content_before == "old content"
    assert change.content_after == "new content"
    assert change.conflict_content is None
    assert change.error_message is None


def test_file_change_with_conflicts():
    """Test FileChange with conflicts."""
    change = FileChange(
        file_path="conflict.txt",
        file_type=".txt",
        analyzer_used="BaseAnalyzer",
        has_semantic_changes=True,
        has_conflicts=True,
        conflict_content="<<<<<<< HEAD\nour content\n=======\ntheir content\n>>>>>>> branch"
    )
    
    assert change.has_conflicts is True
    assert change.conflict_content is not None
    assert "<<<<<<< HEAD" in change.conflict_content


def test_branch_comparison_creation():
    """Test BranchComparison model creation."""
    comparison = BranchComparison(
        from_branch="feature",
        to_branch="main",
        temp_branch="feature-to-main",
        status="success"
    )
    
    assert comparison.from_branch == "feature"
    assert comparison.to_branch == "main"
    assert comparison.temp_branch == "feature-to-main"
    assert comparison.status == "success"
    assert comparison.changes == []
    assert comparison.error_message is None


def test_branch_comparison_with_changes():
    """Test BranchComparison with changes."""
    change1 = FileChange(
        file_path="file1.py",
        file_type=".py",
        analyzer_used="BaseAnalyzer",
        has_semantic_changes=True,
        has_conflicts=False
    )
    
    change2 = FileChange(
        file_path="file2.xml",
        file_type=".xml",
        analyzer_used="XMLAnalyzer",
        has_semantic_changes=False,
        has_conflicts=False
    )
    
    comparison = BranchComparison(
        from_branch="feature",
        to_branch="main",
        temp_branch="feature-to-main",
        status="success",
        changes=[change1, change2]
    )
    
    assert len(comparison.changes) == 2
    assert comparison.changes[0].file_path == "file1.py"
    assert comparison.changes[1].file_path == "file2.xml"


def test_branch_comparison_error_status():
    """Test BranchComparison with error status."""
    comparison = BranchComparison(
        from_branch="nonexistent",
        to_branch="main",
        temp_branch="nonexistent-to-main",
        status="error",
        error_message="Branch 'nonexistent' does not exist"
    )
    
    assert comparison.status == "error"
    assert comparison.error_message == "Branch 'nonexistent' does not exist"