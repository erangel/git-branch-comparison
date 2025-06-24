#!/usr/bin/env python3
"""
Main entry point for Git Branch Comparison Tool
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from git_comparator import GitBranchComparator
from report_generator import NotebookReportGenerator


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Automated Git Branch Comparison Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare specific branch pairs
  python main.py --pairs development:build development:master
  
  # Use a configuration file
  python main.py --config branch_pairs.txt
  
  # Specify output location
  python main.py --pairs development:master --output ./reports/comparison.ipynb
  
  # Compare in both directions
  python main.py --pairs development:master --bidirectional
        """
    )
    
    parser.add_argument(
        '--repo', '-r',
        default='.',
        help='Path to git repository (default: current directory)'
    )
    
    parser.add_argument(
        '--pairs', '-p',
        nargs='+',
        help='Branch pairs to compare (format: from:to)'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file with branch pairs (one per line)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='',
        help='Output notebook file path (default: repo working directory name)'
    )
    
    parser.add_argument(
        '--bidirectional', '-b',
        action='store_true',
        help='Compare branches in both directions'
    )
    
    parser.add_argument(
        '--no-pull', '-n',
        action='store_true',
        help='Skip pulling latest changes from remote'
    )
    
    return parser.parse_args()


def load_branch_pairs(config_file: str) -> List[Tuple[str, str]]:
    """Load branch pairs from configuration file"""
    pairs = []
    
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    from_branch, to_branch = line.split(':', 1)
                    pairs.append((from_branch.strip(), to_branch.strip()))
                elif '-' in line:
                    from_branch, to_branch = line.split('-', 1)
                    pairs.append((from_branch.strip(), to_branch.strip()))
    
    return pairs


def expand_pairs_bidirectional(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Expand pairs to include both directions"""
    expanded = []
    for from_branch, to_branch in pairs:
        expanded.append((from_branch, to_branch))
        expanded.append((to_branch, from_branch))
    return expanded


def main():
    """Main execution function"""
    args = parse_arguments()
    
    # Determine branch pairs
    branch_pairs = []
    
    if args.config:
        print(f"Loading branch pairs from {args.config}")
        branch_pairs = load_branch_pairs(args.config)
    elif args.pairs:
        for pair in args.pairs:
            if ':' in pair:
                from_branch, to_branch = pair.split(':', 1)
                branch_pairs.append((from_branch, to_branch))
            else:
                print(f"Invalid pair format: {pair} (expected 'from:to')")
                sys.exit(1)
    else:
        # Default pairs if none specified
        print("No branch pairs specified, using defaults")
        branch_pairs = [
            ('development', 'build'),
            ('development', 'master'),
            ('development', 'preprod'),
            ('preprod', 'master')
        ]
    
    # Expand bidirectional if requested
    if args.bidirectional:
        branch_pairs = expand_pairs_bidirectional(branch_pairs)
    
    print(f"\nBranch pairs to compare: {len(branch_pairs)}")
    for from_branch, to_branch in branch_pairs:
        print(f"  {from_branch} → {to_branch}")
    
    # Initialize comparator
    try:
        comparator = GitBranchComparator(args.repo, no_pull=args.no_pull)
    except Exception as e:
        print(f"Error initializing repository: {e}")
        sys.exit(1)
    
    # Run comparisons
    comparisons = []
    print("\nRunning comparisons...")
    
    for from_branch, to_branch in branch_pairs:
        print(f"\n{'='*60}")
        print(f"Comparing: {from_branch} → {to_branch}")
        print('='*60)
        
        comparison = comparator.compare_branches(from_branch, to_branch)
        comparisons.append(comparison)
        
        # Print summary
        if comparison.status == 'error':
            print(f"ERROR: {comparison.error_message}")
        else:
            print(f"Status: {comparison.status}")
            print(f"Files changed: {len(comparison.changes)}")
            
            if comparison.changes:
                semantic_changes = sum(1 for c in comparison.changes if c.has_semantic_changes)
                conflicts = sum(1 for c in comparison.changes if c.has_conflicts)
                print(f"  - Semantic changes: {semantic_changes}")
                print(f"  - Formatting only: {len(comparison.changes) - semantic_changes}")
                print(f"  - Conflicts: {conflicts}")
    
    # Generate report
    print(f"\n{'='*60}")
    print("Generating report...")

    # Ensure output directory exists
    if (args.output == ''):
        output_path = Path(f"{Path(args.repo).name}_comparison_report.ipynb")
    else:
        output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate notebook
    generator = NotebookReportGenerator()
    generator.generate_report(comparisons, str(output_path))
    
    print(f"\nReport successfully generated: {output_path}")
    print("\nTo view the report:")
    print(f"  jupyter notebook {output_path}")


if __name__ == '__main__':
    main()