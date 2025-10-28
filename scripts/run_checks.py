#!/usr/bin/env python
"""Run diagnostics for the eCertificate app.

Usage:
  python scripts\run_checks.py
"""
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.utils.error_checker import run_all_checks

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    print('Running diagnostics...')
    report = run_all_checks(app, auto_fix=True)
    import json
    print(json.dumps(report, indent=2))
