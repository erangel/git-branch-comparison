"""
Allow the package to be run as a module with python -m git_branch_comparison
"""

from .cli import main

if __name__ == '__main__':
    main()