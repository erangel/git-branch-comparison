# Git Branch Comparison Tool

An automated tool for comparing git branches with intelligent file analysis and interactive Jupyter notebook reports.

## Features

- **Automated Git Operations**: Handles branch updates, temporary branch creation, test merges, and cleanup
- **Smart File Analysis**: 
  - XML files: Detects element/attribute reordering vs actual changes
  - YAML files: Identifies key reordering and formatting changes
  - Properties files: Recognizes property reordering and comment changes
  - Other files: Generic text comparison with whitespace and moved block detection
- **Interactive Reports**: Generates Jupyter notebooks with filtering, syntax highlighting, and side-by-side diffs
- **Conflict Detection**: Identifies and displays merge conflicts clearly
- **Bidirectional Comparison**: Compare branches in both directions automatically

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Compare default branch pairs:
```bash
python main.py
```

### Specify Branch Pairs

Compare specific branches:
```bash
python main.py --pairs development:master feature/new-ui:development
```

### Use Configuration File

Create a `branch_pairs.txt` file (see example provided) and run:
```bash
python main.py --config branch_pairs.txt
```

### Bidirectional Comparison

Compare branches in both directions:
```bash
python main.py --pairs development:master --bidirectional
```

### Advanced Options

```bash
# Specify repository path
python main.py --repo /path/to/repo --pairs main:develop

# Custom output location
python main.py --output reports/comparison_$(date +%Y%m%d).ipynb

# Skip pulling latest changes
python main.py --no-pull --pairs development:master
```

## Project Structure

```
git-branch-comparison/
├── main.py              # Entry point and CLI
├── models.py            # Data models
├── analyzers.py         # File analyzers (XML, YAML, Properties, Base)
├── git_comparator.py    # Git operations and branch comparison
├── report_generator.py  # Jupyter notebook generation
├── requirements.txt     # Python dependencies
├── branch_pairs.txt     # Example configuration
└── README.md           # This file
```

## How It Works

1. **Branch Validation**: Checks that both branches exist
2. **Temporary Branch Creation**: Creates a temporary branch from the "to" branch
3. **Test Merge**: Attempts a no-commit merge from the "from" branch
4. **File Analysis**: 
   - Detects changed files and conflicts
   - Applies appropriate analyzer based on file type
   - Identifies semantic vs formatting changes
5. **Report Generation**: Creates an interactive Jupyter notebook
6. **Cleanup**: Aborts the merge and removes temporary branch

## Report Features

The generated Jupyter notebook includes:

- **Summary Dashboard**: Overview of all comparisons with statistics
- **Interactive Navigation**: Quick jump buttons to each comparison
- **File Type Analysis**: Breakdown by file type with appropriate analyzers
- **Filtering Controls**: Show/hide files by change type
- **Detailed File Views**:
  - Side-by-side diffs with syntax highlighting
  - Format-specific insights (XML structure, YAML keys, etc.)
  - Conflict highlighting
  - Raw content toggle

## File Analyzers

### XMLAnalyzer
- Detects element and attribute reordering
- Identifies namespace changes
- Distinguishes structural vs cosmetic changes

### YAMLAnalyzer
- Recognizes key reordering in mappings
- Detects style changes (flow vs block)
- Handles multi-document files

### PropertiesAnalyzer
- Identifies property reordering
- Separates comment changes from value changes
- Handles line continuations

### BaseAnalyzer (Default)
- Generic text comparison
- Whitespace change detection
- Moved block identification

## Extending the Tool

To add a new file type analyzer:

1. Create a new analyzer class in `analyzers.py` inheriting from `BaseAnalyzer`
2. Override `_format_specific_analysis()` method
3. Register it in `FileAnalyzerFactory.analyzers` dictionary

Example:
```python
class JSONAnalyzer(BaseAnalyzer):
    def _format_specific_analysis(self, change: FileChange):
        # Add JSON-specific logic here
        pass

# In FileAnalyzerFactory
analyzers = {
    '.json': JSONAnalyzer,
    # ... other analyzers
}
```

## Troubleshooting

### "Branch does not exist" Error
- Ensure you've pulled the latest changes: `git pull`
- Check branch names are spelled correctly
- Verify branches exist: `git branch -a`

### Permission Errors
- Ensure you have write permissions in the repository
- Check that no files are locked by other processes

### Large Repositories
- Use `--no-pull` if you've already updated
- Consider comparing fewer branch pairs at once

## License

This tool is provided as-is for automating git branch comparisons. Adapt as needed for your workflow.