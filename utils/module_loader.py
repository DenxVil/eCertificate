"""
Utility for dynamically loading modules without Flask dependencies.
"""
import os
import importlib.util


def load_module_direct(module_name, file_path):
    """Load a Python module directly from a file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Module file not found: {file_path}")
    
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


def get_app_module_path(module_relative_path, script_file):
    """Get the absolute path to an app module from a tool or test script."""
    script_dir = os.path.dirname(os.path.abspath(script_file))
    repo_root = script_dir
    
    if os.path.basename(script_dir) in ['tools', 'tests', 'scripts']:
        repo_root = os.path.dirname(script_dir)
    
    return os.path.join(repo_root, module_relative_path)
