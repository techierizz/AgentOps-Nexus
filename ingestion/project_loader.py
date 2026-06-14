import os
import zipfile
import tempfile
import shutil
from typing import Dict, Any, List

class ProjectArtifact:
    def __init__(self, run_id: str, files: List[Dict[str, Any]]):
        self.run_id = run_id
        self.files = files

def load_project(run_id: str, zip_path: str) -> ProjectArtifact:
    """
    Extracts ZIP file, scans the directory tree, and collects file contents and metadata.
    Does NOT execute any code.
    """
    files_data = []
    
    # Create an isolated temporary directory for extraction
    temp_dir = tempfile.mkdtemp(prefix=f"nexus_ingest_{run_id}_")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        for root, dirs, files in os.walk(temp_dir):
            # Skip hidden directories and common vendor/build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', 'env', 'dist', 'build', '__pycache__', 'out']]
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # Basic metadata
                size = os.path.getsize(file_path)
                ext = os.path.splitext(file_name)[1].lower()
                
                # Attempt to read text files securely
                content = ""
                if ext in ['.py', '.js', '.ts', '.json', '.md', '.txt', '.yml', '.yaml']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception:
                        content = "<binary or non-utf8 content>"
                        
                files_data.append({
                    "path": rel_path.replace("\\", "/"),
                    "size": size,
                    "extension": ext,
                    "content": content
                })
    finally:
        # Always cleanup the isolated extraction
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    return ProjectArtifact(run_id=run_id, files=files_data)
