"""
File analyzers for different file types
"""

import re
import difflib
from pathlib import Path
from typing import Dict, List, Any
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
import yaml

from .models import FileChange


class BaseAnalyzer(ABC):
    """Base analyzer for generic file comparison"""
    
    def analyze_differences(self, file_path: str, repo, merge_conflicts: bool = False) -> FileChange:
        """Analyze differences in a file"""
        change = FileChange(
            file_path=file_path,
            file_type=Path(file_path).suffix.lower(),
            analyzer_used=self.__class__.__name__,
            has_semantic_changes=True,  # Assume true for base analyzer
            has_conflicts=merge_conflicts
        )
        
        try:
            # Get file content in different states
            if merge_conflicts:
                change.conflict_content = self._read_file_content(file_path, repo.working_dir)
                conflicts = self._parse_conflicts(change.conflict_content)
                change.detailed_analysis['conflicts'] = conflicts
            else:
                # Get content from HEAD and working tree
                try:
                    change.content_before = repo.git.show(f'HEAD:{file_path}')
                except:
                    change.content_before = ""
                
                change.content_after = self._read_file_content(file_path, repo.working_dir)
            
            # Perform base analysis
            self._analyze_whitespace_changes(change)
            # TODO: Fix move block analysis
            #self._analyze_moved_blocks(change)
            self._calculate_summary(change)
            
            # Let subclasses add their specific analysis
            self._format_specific_analysis(change)
            
        except Exception as e:
            change.error_message = str(e)
            
        return change
    
    def _read_file_content(self, file_path: str, repo_working_dir: str = None) -> str:
        """Read file content safely"""
        # If we have a repo working directory, create absolute path
        if repo_working_dir:
            abs_path = Path(repo_working_dir) / file_path
        else:
            abs_path = Path(file_path)
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(abs_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _parse_conflicts(self, content: str) -> List[Dict]:
        """Parse git conflict markers"""
        conflicts = []
        conflict_pattern = r'<<<<<<< .*?\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n'
        
        for match in re.finditer(conflict_pattern, content, re.DOTALL):
            conflicts.append({
                'ours': match.group(1),
                'theirs': match.group(2),
                'start_pos': match.start(),
                'end_pos': match.end()
            })
        
        return conflicts
    
    def _analyze_whitespace_changes(self, change: FileChange):
        """Detect whitespace-only changes"""
        if not change.content_before or not change.content_after:
            return
            
        # Normalize whitespace
        normalized_before = re.sub(r'\s+', ' ', change.content_before.strip())
        normalized_after = re.sub(r'\s+', ' ', change.content_after.strip())
        
        if normalized_before == normalized_after:
            change.detailed_analysis['whitespace_only'] = True
            change.has_semantic_changes = False
        else:
            change.detailed_analysis['whitespace_only'] = False
    
    def _analyze_moved_blocks(self, change: FileChange):
        """Detect moved code blocks"""
        if not change.content_before or not change.content_after:
            return
            
        lines_before = change.content_before.splitlines()
        lines_after = change.content_after.splitlines()
        
        # Use sequence matcher to find moved blocks
        matcher = difflib.SequenceMatcher(None, lines_before, lines_after)
        moved_blocks = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal' and (i2 - i1) > 3:  # Block of at least 4 lines
                # Check if this block appears elsewhere
                block = lines_before[i1:i2]
                block_str = '\n'.join(block)
                
                # Look for this block in different positions
                if i1 != j1:  # Position changed
                    moved_blocks.append({
                        'content': block_str[:100] + '...' if len(block_str) > 100 else block_str,
                        'old_position': i1,
                        'new_position': j1,
                        'size': i2 - i1
                    })
        
        if moved_blocks:
            change.detailed_analysis['moved_blocks'] = moved_blocks
    
    def _calculate_summary(self, change: FileChange):
        """Calculate change summary statistics"""
        if not change.content_before or not change.content_after:
            return
            
        lines_before = change.content_before.splitlines()
        lines_after = change.content_after.splitlines()
        
        differ = difflib.unified_diff(lines_before, lines_after, lineterm='')
        additions = 0
        deletions = 0
        
        for line in differ:
            if line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        
        change.summary = {
            'additions': additions,
            'deletions': deletions,
            'total_changes': additions + deletions
        }
    
    def _format_specific_analysis(self, change: FileChange):
        """Override in subclasses for format-specific analysis"""
        pass


class XMLAnalyzer(BaseAnalyzer):
    """Specialized analyzer for XML files"""
    
    def _format_specific_analysis(self, change: FileChange):
        """XML-specific analysis"""
        if not change.content_before or not change.content_after:
            return
            
        try:
            # Parse XML trees
            tree_before = ET.fromstring(change.content_before)
            tree_after = ET.fromstring(change.content_after)
            
            # Compare structure
            structure_changes = self._compare_xml_structure(tree_before, tree_after)
            change.format_specific.update(structure_changes)
            
            # If only formatting/order changed, not semantic
            if (structure_changes['elements_added'] == 0 and 
                structure_changes['elements_removed'] == 0 and
                structure_changes['text_changes'] == 0 and
                structure_changes['attribute_changes'] == 0):
                change.has_semantic_changes = False
                
        except (ET.ParseError, ExpatError) as e:
            change.format_specific['parse_error'] = str(e)
    
    def _compare_xml_structure(self, tree1: ET.Element, tree2: ET.Element) -> Dict:
        """Compare two XML trees structurally"""
        stats = {
            'elements_added': 0,
            'elements_removed': 0,
            'elements_reordered': 0,
            'attributes_reordered': 0,
            'attribute_changes': 0,
            'text_changes': 0,
            'namespace_changes': 0
        }
        
        # Get all elements from both trees
        elements1 = {self._element_signature(e): e for e in tree1.iter()}
        elements2 = {self._element_signature(e): e for e in tree2.iter()}
        
        # Find added/removed elements
        added = set(elements2.keys()) - set(elements1.keys())
        removed = set(elements1.keys()) - set(elements2.keys())
        
        stats['elements_added'] = len(added)
        stats['elements_removed'] = len(removed)
        
        # Check for reordering and attribute changes
        for sig in set(elements1.keys()) & set(elements2.keys()):
            elem1 = elements1[sig]
            elem2 = elements2[sig]
            
            # Check attribute order
            if (list(elem1.attrib.keys()) != list(elem2.attrib.keys()) and
                set(elem1.attrib.keys()) == set(elem2.attrib.keys())):
                stats['attributes_reordered'] += 1
            
            # Check attribute values
            for attr in elem1.attrib:
                if elem1.attrib.get(attr) != elem2.attrib.get(attr, None):
                    stats['attribute_changes'] += 1
            
            # Check text content
            text1 = (elem1.text or '').strip()
            text2 = (elem2.text or '').strip()
            if text1 != text2:
                stats['text_changes'] += 1
        
        return stats
    
    def _element_signature(self, elem: ET.Element) -> str:
        """Create a signature for an XML element for comparison"""
        # Use tag name and attributes (sorted) as signature
        attrs = ','.join(f"{k}={v}" for k, v in sorted(elem.attrib.items()))
        return f"{elem.tag}[{attrs}]"


class YAMLAnalyzer(BaseAnalyzer):
    """Specialized analyzer for YAML files"""
    
    def _format_specific_analysis(self, change: FileChange):
        """YAML-specific analysis"""
        if not change.content_before or not change.content_after:
            return
            
        try:
            # Parse YAML documents
            docs_before = list(yaml.safe_load_all(change.content_before))
            docs_after = list(yaml.safe_load_all(change.content_after))
            
            # Compare documents
            yaml_changes = self._compare_yaml_documents(docs_before, docs_after)
            change.format_specific.update(yaml_changes)
            
            # Check if only formatting changed
            if (yaml_changes['semantic_differences'] == 0 and
                not yaml_changes['document_count_changed']):
                change.has_semantic_changes = False
                
        except yaml.YAMLError as e:
            change.format_specific['parse_error'] = str(e)
    
    def _compare_yaml_documents(self, docs1: List, docs2: List) -> Dict:
        """Compare YAML documents"""
        stats = {
            'document_count_changed': len(docs1) != len(docs2),
            'key_reordering': 0,
            'semantic_differences': 0,
            'style_changes': 0
        }
        
        # Compare each document pair
        for i, (doc1, doc2) in enumerate(zip(docs1, docs2)):
            if self._yaml_structures_equal(doc1, doc2):
                # Check if it's just reordering
                if isinstance(doc1, dict) and isinstance(doc2, dict):
                    if list(doc1.keys()) != list(doc2.keys()):
                        stats['key_reordering'] += 1
            else:
                stats['semantic_differences'] += 1
        
        return stats
    
    def _yaml_structures_equal(self, obj1: Any, obj2: Any) -> bool:
        """Deep comparison of YAML structures"""
        if type(obj1) != type(obj2):
            return False
            
        if isinstance(obj1, dict):
            if set(obj1.keys()) != set(obj2.keys()):
                return False
            return all(self._yaml_structures_equal(obj1[k], obj2[k]) for k in obj1)
        
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                return False
            return all(self._yaml_structures_equal(a, b) for a, b in zip(obj1, obj2))
        
        else:
            return obj1 == obj2


class PropertiesAnalyzer(BaseAnalyzer):
    """Specialized analyzer for Properties files"""
    
    def _format_specific_analysis(self, change: FileChange):
        """Properties file specific analysis"""
        if not change.content_before or not change.content_after:
            return
            
        # Parse properties
        props_before = self._parse_properties(change.content_before)
        props_after = self._parse_properties(change.content_after)
        
        # Compare properties
        prop_changes = self._compare_properties(props_before, props_after)
        change.format_specific.update(prop_changes)
        
        # Check if only formatting changed
        if (prop_changes['added_properties'] == 0 and
            prop_changes['removed_properties'] == 0 and
            prop_changes['value_changes'] == 0):
            change.has_semantic_changes = False
    
    def _parse_properties(self, content: str) -> Dict[str, str]:
        """Parse properties file content"""
        properties = {}
        current_key = None
        current_value = []
        
        for line in content.splitlines():
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            
            # Handle line continuation
            if line.endswith('\\'):
                if current_key:
                    current_value.append(line[:-1])
                continue
            
            # Parse key=value
            if '=' in line or ':' in line:
                if current_key:
                    properties[current_key] = ''.join(current_value)
                
                # Split on first = or :
                for sep in ['=', ':']:
                    if sep in line:
                        key, value = line.split(sep, 1)
                        current_key = key.strip()
                        current_value = [value.strip()]
                        break
            elif current_key:
                current_value.append(line)
        
        # Don't forget the last property
        if current_key:
            properties[current_key] = ''.join(current_value)
        
        return properties
    
    def _compare_properties(self, props1: Dict, props2: Dict) -> Dict:
        """Compare two property dictionaries"""
        keys1 = set(props1.keys())
        keys2 = set(props2.keys())
        
        stats = {
            'added_properties': len(keys2 - keys1),
            'removed_properties': len(keys1 - keys2),
            'value_changes': 0,
            'reordered_properties': 0
        }
        
        # Check for value changes
        for key in keys1 & keys2:
            if props1[key] != props2[key]:
                stats['value_changes'] += 1
        
        # If same properties but different order in file
        if keys1 == keys2 and list(props1.keys()) != list(props2.keys()):
            stats['reordered_properties'] = len(keys1)
        
        return stats


class FileAnalyzerFactory:
    """Factory to create appropriate analyzer for file type"""
    
    analyzers = {
        '.xml': XMLAnalyzer,
        '.yml': YAMLAnalyzer,
        '.yaml': YAMLAnalyzer,
        '.properties': PropertiesAnalyzer,
        '.props': PropertiesAnalyzer
    }
    
    @classmethod
    def get_analyzer(cls, file_path: str) -> BaseAnalyzer:
        """Get appropriate analyzer for file type"""
        ext = Path(file_path).suffix.lower()
        analyzer_class = cls.analyzers.get(ext, BaseAnalyzer)
        return analyzer_class()