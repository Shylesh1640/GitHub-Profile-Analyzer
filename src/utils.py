import os
import shutil
import subprocess
from datetime import datetime

def clone_repo(repo_url, target_dir):
    """
    Clones a repository to the target directory.
    Uses shallow clone (depth=1) to save bandwidth and time.
    """
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, target_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def cleanup_repo(target_dir):
    """Removes the cloned repository directory."""
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir, ignore_errors=True)

def get_file_extension(filename):
    return os.path.splitext(filename)[1]
