"""Tests for analyzers module."""

import pytest
from git_branch_comparison.analyzers import FileAnalyzerFactory, BaseAnalyzer, XMLAnalyzer, YAMLAnalyzer, PropertiesAnalyzer
from git_branch_comparison.models import FileChange


def test_analyzer_factory_base():
    """Test FileAnalyzerFactory returns BaseAnalyzer for unknown extensions."""
    analyzer = FileAnalyzerFactory.get_analyzer("test.py")
    assert isinstance(analyzer, BaseAnalyzer)
    assert analyzer.__class__.__name__ == "BaseAnalyzer"


def test_analyzer_factory_xml():
    """Test FileAnalyzerFactory returns XMLAnalyzer for XML files."""
    analyzer = FileAnalyzerFactory.get_analyzer("test.xml")
    assert isinstance(analyzer, XMLAnalyzer)
    assert analyzer.__class__.__name__ == "XMLAnalyzer"


def test_analyzer_factory_yaml():
    """Test FileAnalyzerFactory returns YAMLAnalyzer for YAML files."""
    analyzer_yml = FileAnalyzerFactory.get_analyzer("test.yml")
    analyzer_yaml = FileAnalyzerFactory.get_analyzer("test.yaml")
    
    assert isinstance(analyzer_yml, YAMLAnalyzer)
    assert isinstance(analyzer_yaml, YAMLAnalyzer)
    assert analyzer_yml.__class__.__name__ == "YAMLAnalyzer"
    assert analyzer_yaml.__class__.__name__ == "YAMLAnalyzer"


def test_analyzer_factory_properties():
    """Test FileAnalyzerFactory returns PropertiesAnalyzer for properties files."""
    analyzer_props = FileAnalyzerFactory.get_analyzer("test.properties")
    analyzer_config = FileAnalyzerFactory.get_analyzer("test.props")
    
    assert isinstance(analyzer_props, PropertiesAnalyzer)
    assert isinstance(analyzer_config, PropertiesAnalyzer)
    assert analyzer_props.__class__.__name__ == "PropertiesAnalyzer"


def test_analyzer_factory_case_insensitive():
    """Test FileAnalyzerFactory handles case insensitive extensions."""
    analyzer_xml = FileAnalyzerFactory.get_analyzer("test.XML")
    analyzer_yaml = FileAnalyzerFactory.get_analyzer("test.YAML")
    
    assert isinstance(analyzer_xml, XMLAnalyzer)
    assert isinstance(analyzer_yaml, YAMLAnalyzer)


def test_xml_analyzer_element_signature():
    """Test XMLAnalyzer element signature generation."""
    analyzer = XMLAnalyzer()
    
    # This would require creating actual XML elements for testing
    # For now, just test that the analyzer can be instantiated
    assert analyzer is not None
    assert hasattr(analyzer, '_element_signature')


def test_yaml_analyzer_structures_equal():
    """Test YAMLAnalyzer structure comparison."""
    analyzer = YAMLAnalyzer()
    
    # Test basic equality
    assert analyzer._yaml_structures_equal({'a': 1, 'b': 2}, {'a': 1, 'b': 2})
    assert analyzer._yaml_structures_equal([1, 2, 3], [1, 2, 3])
    assert analyzer._yaml_structures_equal("hello", "hello")
    
    # Test inequality
    assert not analyzer._yaml_structures_equal({'a': 1}, {'a': 2})
    assert not analyzer._yaml_structures_equal([1, 2], [1, 2, 3])
    assert not analyzer._yaml_structures_equal("hello", "world")


def test_properties_analyzer_parse():
    """Test PropertiesAnalyzer parsing functionality."""
    analyzer = PropertiesAnalyzer()
    
    content = """
# This is a comment
key1=value1
key2 = value2
key3:value3

# Another comment
key4=value4
"""
    
    props = analyzer._parse_properties(content)
    
    assert 'key1' in props
    assert props['key1'] == 'value1'
    assert 'key2' in props
    assert props['key2'] == 'value2'
    assert 'key3' in props
    assert props['key3'] == 'value3'
    assert 'key4' in props
    assert props['key4'] == 'value4'


def test_properties_analyzer_compare():
    """Test PropertiesAnalyzer comparison functionality."""
    analyzer = PropertiesAnalyzer()
    
    props1 = {'a': '1', 'b': '2', 'c': '3'}
    props2 = {'a': '1', 'b': '2', 'c': '3', 'd': '4'}  # Added property
    
    stats = analyzer._compare_properties(props1, props2)
    
    assert stats['added_properties'] == 1
    assert stats['removed_properties'] == 0
    assert stats['value_changes'] == 0


def test_base_analyzer_read_file_error_handling():
    """Test BaseAnalyzer file reading error handling."""
    analyzer = BaseAnalyzer()
    
    # Test with non-existent file
    content = analyzer._read_file_content("nonexistent_file.txt")
    # Should handle the error gracefully (implementation dependent)
    # This test mainly ensures the method exists and doesn't crash
    assert content is not None or content == ""