"""
Git operations and branch comparison logic
"""

from typing import List
from git import Repo, GitCommandError

from .models import BranchComparison, FileChange
from .analyzers import FileAnalyzerFactory


class GitComparator:
    """Main class for branch comparison"""
    
    def __init__(self, repo_path: str = '.', no_pull: bool = False):
        self.repo = Repo(repo_path)
        self.original_branch = self.repo.active_branch.name
        self.no_pull = no_pull
        
    def compare_branches(self, from_branch: str, to_branch: str) -> BranchComparison:
        """Compare two branches"""
        temp_branch = f"{from_branch}-to-{to_branch}"
        comparison = BranchComparison(
            from_branch=from_branch,
            to_branch=to_branch,
            temp_branch=temp_branch,
            status='success'
        )
        
        try:
            # Ensure we're up to date
            if not self.no_pull:
                print(f"Pulling latest changes...")
                try:
                    self.repo.git.switch(to_branch)
                    if self.repo.remotes.origin:
                        print(f"Pulling from remote {self.repo.remotes.origin.name}...")
                    self.repo.remotes.origin.pull()
                except Exception as e:
                    print(f"Warning: Could not pull from remote: {e}")
                try:
                    self.repo.git.switch(from_branch)
                    if self.repo.remotes.origin:
                        print(f"Pulling from remote {self.repo.remotes.origin.name}...")
                    self.repo.remotes.origin.pull()
                except Exception as e:
                    print(f"Warning: Could not pull from remote: {e}")

 
            # Validate branches exist
            if not self._branch_exists(from_branch):
                comparison.status = 'error'
                comparison.error_message = f"Branch '{from_branch}' does not exist"
                return comparison
                
            if not self._branch_exists(to_branch):
                comparison.status = 'error'
                comparison.error_message = f"Branch '{to_branch}' does not exist"
                return comparison
            
            # Create temporal branch
            print(f"Creating temporal branch {temp_branch}...")
            self.repo.git.checkout(to_branch)
            self.repo.git.checkout('-b', temp_branch)
            
            # Attempt merge
            print(f"Attempting merge from {from_branch}...")
            try:
                self.repo.git.merge(from_branch, no_commit=True, no_ff=True)
                
                # Get changed files
                changed_files = self._get_changed_files()
                
                # Analyze each file
                for file_path in changed_files:
                    print(f"  Analyzing {file_path}...")
                    analyzer = FileAnalyzerFactory.get_analyzer(file_path)
                    file_change = analyzer.analyze_differences(file_path, self.repo)
                    comparison.changes.append(file_change)
                    
            except GitCommandError as _:
                # Merge conflict
                comparison.status = 'conflict'
                print("Merge conflicts detected, analyzing...")
                
                # Get conflicted files
                conflicted_files = self._get_conflicted_files()
                
                for file_path in conflicted_files:
                    print(f"  Analyzing conflicts in {file_path}...")
                    analyzer = FileAnalyzerFactory.get_analyzer(file_path)
                    file_change = analyzer.analyze_differences(file_path, self.repo, merge_conflicts=True)
                    comparison.changes.append(file_change)
            
            # Abort merge
            print("Aborting merge...")
            try:
                self.repo.git.merge('--abort')
            except GitCommandError as _:
                self.repo.git.reset('--hard', 'HEAD')
            
        except Exception as e:
            comparison.status = 'error'
            comparison.error_message = str(e)
            
        finally:
            # Cleanup
            print("Cleaning up...")
            try:
                self.repo.git.checkout(self.original_branch)
                if temp_branch in [b.name for b in self.repo.branches]:
                    self.repo.git.branch('-D', temp_branch)
            except Exception as e:
                print(f"Warning during cleanup: {e}")
                
        return comparison
    
    def _branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists"""
        try:
            self.repo.git.rev_parse('--verify', branch_name)
            return True
        except GitCommandError:
            return False
    
    def _get_changed_files(self) -> List[str]:
        """Get list of changed files in current merge"""
        # Get files that would be changed in the merge
        diff = self.repo.index.diff(None)
        staged = self.repo.index.diff("HEAD")
        
        changed_files = set()
        for d in diff:
            changed_files.add(d.a_path)
        for d in staged:
            changed_files.add(d.a_path)
            
        # Also check for untracked files in merge
        status = self.repo.git.status('--porcelain')
        for line in status.splitlines():
            if line.startswith(('M ', 'A ', 'D ', 'R ')):
                changed_files.add(line[3:])
            
        return list(changed_files)
    
    def _get_conflicted_files(self) -> List[str]:
        """Get list of files with merge conflicts"""
        conflicted = []
        try:
            status = self.repo.git.status('--porcelain')
            for line in status.splitlines():
                if line.startswith('UU '):
                    conflicted.append(line[3:])
                elif line.startswith('AA '):
                    conflicted.append(line[3:])
                elif line.startswith('DD '):
                    conflicted.append(line[3:])
                elif line.startswith('AU '):
                    conflicted.append(line[3:])
                elif line.startswith('UA '):
                    conflicted.append(line[3:])
                elif line.startswith('DU '):
                    conflicted.append(line[3:])
                elif line.startswith('UD '):
                    conflicted.append(line[3:])
        except:
            pass
        return conflicted