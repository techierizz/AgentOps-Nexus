import ast
import os
from typing import Dict, List, Any

class CodeASTParser:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.nodes = []
        self.edges = []

    def parse_repo(self) -> Dict[str, Any]:
        """Traverses the repository and parses all Python files."""
        self.nodes = []
        self.edges = []
        
        py_files = []
        for root, _, files in os.walk(self.repo_path):
            # Skip virtual environments and cache directories
            if any(part in root.replace('\\', '/').split('/') for part in ['.git', '__pycache__', '.venv', 'venv', 'env', '.pytest_cache']):
                continue
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.repo_path).replace('\\', '/')
                    py_files.append((rel_path, full_path))

        # 1. First Pass: Create all File, Class, and Function Nodes
        file_imports = {} # Store imports per file to build import edges later
        for rel_path, full_path in py_files:
            # File Node
            self.nodes.append({
                "id": rel_path,
                "label": rel_path,
                "type": "file",
                "properties": {
                    "path": rel_path,
                    "size": os.path.getsize(full_path)
                }
            })
            
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    source = f.read()
                
                tree = ast.parse(source, filename=full_path)
                imports, classes, functions = self._analyze_ast(tree, rel_path)
                
                file_imports[rel_path] = imports
                
                for cls in classes:
                    self.nodes.append({
                        "id": f"{rel_path}::{cls['name']}",
                        "label": cls['name'],
                        "type": "class",
                        "properties": {
                            "file": rel_path,
                            "bases": cls['bases']
                        }
                    })
                    # Edge from class to its containing file
                    self.edges.append({
                        "source": f"{rel_path}::{cls['name']}",
                        "target": rel_path,
                        "type": "declared_in"
                    })
                    # Base class inheritance edges
                    for base in cls['bases']:
                        # Try to resolve parent class in same file
                        matching_class = next((c for c in classes if c['name'] == base), None)
                        if matching_class:
                            self.edges.append({
                                "source": f"{rel_path}::{cls['name']}",
                                "target": f"{rel_path}::{base}",
                                "type": "extends"
                            })

                for func in functions:
                    parent_id = f"{rel_path}::{func['class_name']}" if func['class_name'] else rel_path
                    func_id = f"{parent_id}::{func['name']}"
                    
                    self.nodes.append({
                        "id": func_id,
                        "label": func['name'],
                        "type": "function",
                        "properties": {
                            "file": rel_path,
                            "class": func['class_name'],
                            "args": func['args']
                        }
                    })
                    
                    self.edges.append({
                        "source": func_id,
                        "target": parent_id,
                        "type": "declared_in" if func['class_name'] else "contains_function"
                    })
                    
                    # Function call references within this function
                    for called_name in func['calls']:
                        # Link function to other local functions in same file
                        matching_func = next((f for f in functions if f['name'] == called_name), None)
                        if matching_func:
                            target_parent = f"{rel_path}::{matching_func['class_name']}" if matching_func['class_name'] else rel_path
                            self.edges.append({
                                "source": func_id,
                                "target": f"{target_parent}::{called_name}",
                                "type": "calls"
                            })
                            
            except Exception as e:
                # Log parser error but continue
                print(f"Error parsing AST for {rel_path}: {e}")

        # 2. Second Pass: Link dependencies and cross-module imports
        for file_path, imports in file_imports.items():
            for imp in imports:
                # Find matching target files in project
                # e.g., if we import "payment_processor", look for "payment_processor.py"
                target_file = f"{imp}.py"
                if target_file in [n['id'] for n in self.nodes if n['type'] == 'file']:
                    self.edges.append({
                        "source": file_path,
                        "target": target_file,
                        "type": "imports"
                    })
                else:
                    # Look for relative imports or matching submodules
                    for node in self.nodes:
                        if node['type'] == 'file' and node['id'].endswith(f"/{target_file}"):
                            self.edges.append({
                                "source": file_path,
                                "target": node['id'],
                                "type": "imports"
                            })

        return {"nodes": self.nodes, "edges": self.edges}

    def _analyze_ast(self, tree: ast.AST, rel_path: str):
        imports = []
        classes = []
        functions = []

        class ASTVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None

            def visit_Import(self, node):
                for alias in node.names:
                    imports.append(alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    imports.append(node.module)
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                
                classes.append({
                    "name": node.name,
                    "bases": bases
                })
                
                prev_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = prev_class

            def visit_FunctionDef(self, node):
                args = [arg.arg for arg in node.args.args]
                calls = []
                
                # Nested visitor to find function calls inside this function body
                class CallVisitor(ast.NodeVisitor):
                    def visit_Call(self, node_call):
                        if isinstance(node_call.func, ast.Name):
                            calls.append(node_call.func.id)
                        elif isinstance(node_call.func, ast.Attribute):
                            calls.append(node_call.func.attr)
                        self.generic_visit(node_call)
                
                CallVisitor().visit(node)
                
                functions.append({
                    "name": node.name,
                    "class_name": self.current_class,
                    "args": args,
                    "calls": list(set(calls))
                })
                self.generic_visit(node)

        ASTVisitor().visit(tree)
        return imports, classes, functions

if __name__ == "__main__":
    # Test script
    parser = CodeASTParser(".")
    res = parser.parse_repo()
    print(f"Nodes: {len(res['nodes'])}")
    print(f"Edges: {len(res['edges'])}")
