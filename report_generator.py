"""
Jupyter notebook report generator - Markdown only version
"""

from datetime import datetime
from typing import List
import json

import nbformat as nbf

from models import BranchComparison, FileChange


class NotebookReportGenerator:
    """Generate Jupyter notebook reports using only Markdown"""
    
    def __init__(self):
        self.nb = nbf.v4.new_notebook()
        self.nb.metadata = {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            }
        }
    
    def generate_report(self, comparisons: List[BranchComparison], output_path: str):
        """Generate complete report notebook"""
        # Title cell
        self._add_markdown_cell(
            f"Git Branch Comparison Report\n\n"
            f"**Generated on:** {self._get_timestamp()}\n\n"
            "---"
        )
        
        # Table of Contents
        self._add_table_of_contents(comparisons)
        
        # Summary dashboard
        self._add_summary_dashboard(comparisons)
        
        # Add section for each comparison
        for idx, comparison in enumerate(comparisons):
            self._add_comparison_section(comparison, idx + 1)
        
        # Save notebook with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8') as f:
            nbf.write(self.nb, f)
        
        print(f"Report generated: {output_path}")
    
    def _add_markdown_cell(self, content: str):
        """Add markdown cell to notebook"""
        self.nb.cells.append(nbf.v4.new_markdown_cell(content))
    
    def _add_code_cell(self, code: str):
        """Add code cell to notebook"""
        cell = nbf.v4.new_code_cell(code)
        cell.metadata = {
            'collapsed': True,
            'jupyter': {
                'source_hidden': False
            },
            'tags': ['hide-input']
        }
        
        self.nb.cells.append(cell)
    
    def _add_table_of_contents(self, comparisons: List[BranchComparison]):
        """Add table of contents"""
        toc = "Table of Contents\n\n"
        toc += "1. [Summary Dashboard](#summary-dashboard)\n"
        
        for idx, comp in enumerate(comparisons):
            section_num = idx + 1
            toc += f"{section_num + 1}. [Comparison: {comp.from_branch} → {comp.to_branch}](#comparison-{section_num})\n"
        
        self._add_markdown_cell(toc)
    
    def _add_summary_dashboard(self, comparisons: List[BranchComparison]):
        """Add summary dashboard"""
        self._add_markdown_cell(
            "Summary Dashboard\n\n"
            "<a id='summary-dashboard'></a>"
        )
        
        # Overall statistics
        total_files = sum(len(c.changes) for c in comparisons)
        total_conflicts = sum(1 for c in comparisons if c.status == 'conflict')
        total_errors = sum(1 for c in comparisons if c.status == 'error')
        
        stats = f"Overall Statistics\n\n"
        stats += f"- **Total Comparisons:** {len(comparisons)}\n"
        stats += f"- **Total Files Changed:** {total_files}\n"
        stats += f"- **Comparisons with Conflicts:** {total_conflicts}\n"
        stats += f"- **Comparisons with Errors:** {total_errors}\n\n"
        
        self._add_markdown_cell(stats)
        
        # Comparison table
        table = "Comparison Overview\n\n"
        table += "| From Branch | To Branch | Status | Files | Semantic | Formatting | Conflicts |\n"
        table += "|-------------|-----------|--------|-------|----------|------------|----------|\n"
        
        for comp in comparisons:
            conflict_count = sum(1 for c in comp.changes if c.has_conflicts)
            semantic_count = sum(1 for c in comp.changes if c.has_semantic_changes)
            formatting_count = len(comp.changes) - semantic_count
            
            status_badge = "SUCCESS" if comp.status == 'success' else ("CONFLICT" if comp.status == 'conflict' else "ERROR")
            table += f"| {comp.from_branch} | {comp.to_branch} | {status_badge} | "
            table += f"{len(comp.changes)} | {semantic_count} | {formatting_count} | {conflict_count} |\n"
        
        self._add_markdown_cell(table)
    
    def _add_comparison_section(self, comparison: BranchComparison, section_num: int):
        """Add section for single branch comparison"""
        status_text = "[SUCCESS]" if comparison.status == 'success' else ("[CONFLICT]" if comparison.status == 'conflict' else "[ERROR]")
        
        self._add_markdown_cell(
            f"Comparison {section_num}: {comparison.from_branch} → {comparison.to_branch}\n\n"
            f"<a id='comparison-{section_num}'></a>\n\n"
            f"**Status:** {status_text} {comparison.status}\n\n"
            f"**Files Changed:** {len(comparison.changes)}\n\n"
            "---"
        )
        
        if comparison.error_message:
            self._add_markdown_cell(
                f"Error Details\n\n"
                f"```\n{comparison.error_message}\n```"
            )
            return
        
        # File type summary
        self._add_file_type_summary(comparison)
        
        # Summary of changes
        self._add_changes_summary(comparison)
        
        # Add analysis for each file
        for idx, change in enumerate(comparison.changes):
            self._add_file_analysis(change, idx)
    
    def _add_file_type_summary(self, comparison: BranchComparison):
        """Add file type summary"""
        by_type = {}
        for change in comparison.changes:
            file_type = change.file_type or 'other'
            if file_type not in by_type:
                by_type[file_type] = {
                    'count': 0,
                    'semantic': 0,
                    'formatting': 0,
                    'conflicts': 0,
                    'analyzer': ''
                }
            
            by_type[file_type]['count'] += 1
            by_type[file_type]['analyzer'] = change.analyzer_used
            if change.has_semantic_changes:
                by_type[file_type]['semantic'] += 1
            else:
                by_type[file_type]['formatting'] += 1
            if change.has_conflicts:
                by_type[file_type]['conflicts'] += 1
        
        summary = "Files by Type\n\n"
        for file_type, stats in sorted(by_type.items()):
            summary += f"{file_type} files ({stats['analyzer']})\n"
            summary += f"- Total: {stats['count']}\n"
            summary += f"- Semantic changes: {stats['semantic']}\n"
            summary += f"- Formatting only: {stats['formatting']}\n"
            if stats['conflicts'] > 0:
                summary += f"- With conflicts: {stats['conflicts']}\n"
            summary += "\n"
        
        self._add_markdown_cell(summary)
    
    def _add_changes_summary(self, comparison: BranchComparison):
        """Add a summary list of all changes"""
        summary = "Changes Summary\n\n"
        
        # Group files by change type
        semantic_changes = []
        formatting_changes = []
        conflicts = []
        
        for change in comparison.changes:
            if change.has_conflicts:
                conflicts.append(change)
            elif change.has_semantic_changes:
                semantic_changes.append(change)
            else:
                formatting_changes.append(change)
        
        if conflicts:
            summary += "Files with Conflicts\n\n"
            for change in conflicts:
                summary += f"- **{change.file_path}** - {change.analyzer_used}\n"
            summary += "\n"
        
        if semantic_changes:
            summary += "Files with Semantic Changes\n\n"
            for change in semantic_changes:
                additions = change.summary.get('additions', 0)
                deletions = change.summary.get('deletions', 0)
                summary += f"- **{change.file_path}** - {change.analyzer_used} (+{additions}/-{deletions})\n"
            summary += "\n"
        
        if formatting_changes:
            summary += "Files with Formatting Changes Only\n\n"
            for change in formatting_changes:
                summary += f"- **{change.file_path}** - {change.analyzer_used}\n"
            summary += "\n"
        
        self._add_markdown_cell(summary)
    
    def _add_file_analysis(self, change: FileChange, idx: int):
        """Add analysis for single file"""
        status = "[CONFLICT]" if change.has_conflicts else ("[SEMANTIC]" if change.has_semantic_changes else "[FORMATTING]")
        
        # File header
        header = f"{status} {change.file_path}\n\n"
        header += f"- **File Type:** {change.file_type}\n"
        header += f"- **Analyzer Used:** {change.analyzer_used}\n"
        header += f"- **Has Semantic Changes:** {'Yes' if change.has_semantic_changes else 'No'}\n"
        header += f"- **Has Conflicts:** {'Yes' if change.has_conflicts else 'No'}\n"
        
        if change.summary:
            header += f"- **Lines Added:** {change.summary.get('additions', 0)}\n"
            header += f"- **Lines Deleted:** {change.summary.get('deletions', 0)}\n"
        
        self._add_markdown_cell(header)
        
        # Format-specific insights
        if change.format_specific:
            insights = "Format-Specific Analysis\n\n"
            
            # Present insights in a readable way based on analyzer type
            if change.analyzer_used == 'XMLAnalyzer':
                insights += self._format_xml_insights(change.format_specific)
            elif change.analyzer_used == 'YAMLAnalyzer':
                insights += self._format_yaml_insights(change.format_specific)
            elif change.analyzer_used == 'PropertiesAnalyzer':
                insights += self._format_properties_insights(change.format_specific)
            else:
                # Generic format
                for key, value in sorted(change.format_specific.items()):
                    readable_key = key.replace('_', ' ').title()
                    insights += f"- {readable_key}: {value}\n"
            
            self._add_markdown_cell(insights)
        
        # Detailed analysis
        if change.detailed_analysis:
            details = "Detailed Analysis\n\n"
            
            if change.detailed_analysis.get('whitespace_only'):
                details += "- **This file contains only whitespace changes**\n"
            
            if 'moved_blocks' in change.detailed_analysis:
                moved = change.detailed_analysis['moved_blocks']
                details += f"- **Moved Blocks:** {len(moved)} code blocks were relocated\n"
                for i, block in enumerate(moved[:3]):  # Show first 3
                    details += f"  - Block {i+1}: {block['size']} lines moved from line {block['old_position']} to {block['new_position']}\n"
                if len(moved) > 3:
                    details += f"  - ... and {len(moved) - 3} more blocks\n"
            
            self._add_markdown_cell(details)
        
        # For conflicts, show the conflict details
        if change.has_conflicts and change.detailed_analysis.get('conflicts'):
            self._add_conflict_details(change)
        
        # Add a simple diff view using code blocks
        self._add_simple_diff(change, idx)
    
    def _format_xml_insights(self, insights: dict) -> str:
        """Format XML-specific insights"""
        result = ""
        if insights.get('elements_added', 0) > 0:
            result += f"- Elements added: {insights['elements_added']}\n"
        if insights.get('elements_removed', 0) > 0:
            result += f"- Elements removed: {insights['elements_removed']}\n"
        if insights.get('elements_reordered', 0) > 0:
            result += f"- Elements reordered: {insights['elements_reordered']}\n"
        if insights.get('attributes_reordered', 0) > 0:
            result += f"- Attributes reordered: {insights['attributes_reordered']}\n"
        if insights.get('attribute_changes', 0) > 0:
            result += f"- Attribute value changes: {insights['attribute_changes']}\n"
        if insights.get('text_changes', 0) > 0:
            result += f"- Text content changes: {insights['text_changes']}\n"
        if insights.get('namespace_changes', 0) > 0:
            result += f"- Namespace changes: {insights['namespace_changes']}\n"
        if 'parse_error' in insights:
            result += f"- **Parse Error:** {insights['parse_error']}\n"
        return result
    
    def _format_yaml_insights(self, insights: dict) -> str:
        """Format YAML-specific insights"""
        result = ""
        if insights.get('document_count_changed'):
            result += "- Document count changed\n"
        if insights.get('key_reordering', 0) > 0:
            result += f"- Keys reordered: {insights['key_reordering']}\n"
        if insights.get('semantic_differences', 0) > 0:
            result += f"- Semantic differences: {insights['semantic_differences']}\n"
        if insights.get('style_changes', 0) > 0:
            result += f"- Style changes: {insights['style_changes']}\n"
        if 'parse_error' in insights:
            result += f"- **Parse Error:** {insights['parse_error']}\n"
        return result
    
    def _format_properties_insights(self, insights: dict) -> str:
        """Format Properties file insights"""
        result = ""
        if insights.get('added_properties', 0) > 0:
            result += f"- Properties added: {insights['added_properties']}\n"
        if insights.get('removed_properties', 0) > 0:
            result += f"- Properties removed: {insights['removed_properties']}\n"
        if insights.get('value_changes', 0) > 0:
            result += f"- Property value changes: {insights['value_changes']}\n"
        if insights.get('reordered_properties', 0) > 0:
            result += f"- Properties reordered: {insights['reordered_properties']}\n"
        return result
    
    def _add_conflict_details(self, change: FileChange):
        """Add conflict details"""
        conflicts = change.detailed_analysis.get('conflicts', [])
        if not conflicts:
            return
        
        details = f"Conflict Details\n\n"
        details += f"This file has {len(conflicts)} merge conflict(s).\n\n"
        
        for i, conflict in enumerate(conflicts[:2]):  # Show first 2 conflicts
            details += f"**Conflict {i+1}:**\n\n"
            details += "```diff\n"
            details += "<<<<<<< OURS\n"
            details += conflict['ours'][:200] + ('...' if len(conflict['ours']) > 200 else '')
            details += "\n=======\n"
            details += conflict['theirs'][:200] + ('...' if len(conflict['theirs']) > 200 else '')
            details += "\n>>>>>>> THEIRS\n"
            details += "```\n\n"
        
        if len(conflicts) > 2:
            details += f"*... and {len(conflicts) - 2} more conflict(s)*\n\n"
        
        self._add_markdown_cell(details)
    
    def _add_simple_diff(self, change: FileChange, idx: int):
        """Add a simple diff view using code blocks"""
        if change.has_conflicts:
            # For conflicts, show the raw conflict file
            if change.conflict_content:
                self._add_markdown_cell("#### File Content (with conflicts)\n")
                
                # Show first 50 lines of conflict content
                lines = change.conflict_content.splitlines()
                preview = '\n'.join(lines[:50])
                if len(lines) > 50:
                    preview += f"\n\n... ({len(lines) - 50} more lines)"
                
                self._add_code_cell(f'''# Conflict content for {change.file_path}
conflict_content = """{repr(change.conflict_content)}"""

# Display first 50 lines
lines = conflict_content.splitlines()
for i, line in enumerate(lines[:50]):
    print(f"{{i+1:4d}}: {{line}}")

if len(lines) > 50:
    print(f"\\n... ({{len(lines) - 50}} more lines)")
''')
        else:
            # For non-conflicts, create a simple comparison
            self._add_markdown_cell("Change Preview\n")
            
            # Add a code cell that will show the differences
            self._add_code_cell(f'''#Simple diff for {change.file_path}
import difflib

content_before = {repr(change.content_before or '')}
content_after = {repr(change.content_after or '')}

# Create unified diff
content_before = content_before.replace(f"\\r\\n", f"\\n").replace(f"\\r", f"\\n")
content_after = content_after.replace(f"\\r\\n", f"\\n").replace(f"\\r", f"\\n")
lines_before = content_before.splitlines(keepends=True)
lines_after = content_after.splitlines(keepends=True)

diff = difflib.unified_diff(
    lines_before,
    lines_after,
    fromfile='Before',
    tofile='After',
    n=3  # Context lines
)

# Display diff (first 100 lines)
diff_lines = list(diff)
for i, line in enumerate(diff_lines[:100]):
    print(f"  {{line.rstrip()}}")

if len(diff_lines) > 100:
    print(f"\\n... ({{len(diff_lines) - 100}} more lines)")
''')
        
        self._add_markdown_cell("---")  # Separator between files
    
    def _get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")