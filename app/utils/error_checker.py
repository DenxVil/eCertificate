"""Diagnostics and auto-fix utilities for the application and bot.

Provides checks for environment, uploads/templates, and SMTP.
Some safe auto-fixes are attempted (for example, fixing template paths that reference
files existing in the uploads folder but stored with different paths).
"""
import os
import traceback
from app.models import Event, db


def _resolve_uploads(app):
    return app.config.get('UPLOAD_FOLDER', 'uploads')


def check_env(app):
    """Check required environment variables and basic config.

    Returns a dict with keys 'ok' (bool) and 'details' (list).
    """
    issues = []
    cfg = app.config

    # Basic checks
    if not cfg.get('SECRET_KEY') or cfg.get('SECRET_KEY').startswith('dev-'):
        issues.append('SECRET_KEY is not set or uses a development default.')

    if not cfg.get('MAIL_USERNAME') or not cfg.get('MAIL_PASSWORD'):
        issues.append('MAIL_USERNAME or MAIL_PASSWORD not set - email sending will fail.')

    return {'ok': len(issues) == 0, 'details': issues}


def check_uploads_and_templates(app, auto_fix=True):
    """Check uploads folder and Event.template_path values.

    If auto_fix is True, attempt to fix template_path values by searching the uploads
    folder for matching basenames and updating the database.

    Returns a dict with results and a list of fixes performed.
    """
    results = []
    fixes = []
    upload_folder = _resolve_uploads(app)
    upload_abs = os.path.abspath(upload_folder)

    # Ensure upload folder exists
    if not os.path.exists(upload_abs):
        results.append({'level': 'error', 'message': f'Upload folder not found: {upload_abs}'})
        return {'ok': False, 'results': results, 'fixes': fixes}

    events = Event.query.all()
    for e in events:
        tpl = e.template_path
        if not tpl:
            results.append({'event': e.id, 'status': 'missing', 'message': 'No template_path set'})
            continue

        # Resolve candidate path
        if os.path.isabs(tpl):
            candidate = tpl
        elif tpl.startswith(upload_folder + os.sep) or tpl.startswith(upload_folder + '/'):
            candidate = os.path.abspath(tpl)
        else:
            candidate = os.path.join(upload_abs, tpl)

        if os.path.exists(candidate):
            results.append({'event': e.id, 'status': 'ok', 'path': candidate})
            continue

        # Attempt to auto-fix by finding a file with the same basename in uploads
        base = os.path.basename(tpl)
        found = None
        for root, _, files in os.walk(upload_abs):
            if base in files:
                found = os.path.join(root, base)
                break

        if found:
            results.append({'event': e.id, 'status': 'fixed', 'old': tpl, 'new': found})
            if auto_fix:
                # Save the fixed path as relative to upload folder where possible
                rel = os.path.relpath(found, upload_abs)
                e.template_path = os.path.join(upload_folder, rel).replace('\\', '/')
                db.session.add(e)
                db.session.commit()
                fixes.append({'event': e.id, 'old': tpl, 'new': e.template_path})
        else:
            results.append({'event': e.id, 'status': 'missing_file', 'message': f'Template not found for {tpl}'})

    ok = all(r.get('status') in ('ok', 'fixed') for r in results if 'status' in r)
    return {'ok': ok, 'results': results, 'fixes': fixes}


def check_smtp(app, timeout=10):
    """Attempt to connect to the SMTP server with provided credentials.

    Returns {'ok': bool, 'message': str}.
    """
    import smtplib

    server = app.config.get('MAIL_SERVER')
    port = app.config.get('MAIL_PORT') or 587
    username = app.config.get('MAIL_USERNAME')
    password = app.config.get('MAIL_PASSWORD')

    if not username or not password:
        return {'ok': False, 'message': 'MAIL_USERNAME or MAIL_PASSWORD not set; skipping SMTP test.'}

    try:
        smtp = smtplib.SMTP(server, port, timeout=timeout)
        smtp.ehlo()
        if app.config.get('MAIL_USE_TLS'):
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.quit()
        return {'ok': True, 'message': 'SMTP login successful'}
    except Exception as e:
        return {'ok': False, 'message': f'SMTP check failed: {str(e)}', 'trace': traceback.format_exc()}


def run_all_checks(app, auto_fix=True):
    """Run all checks and return a combined report."""
    report = {}
    report['env'] = check_env(app)
    report['uploads'] = check_uploads_and_templates(app, auto_fix=auto_fix)
    report['smtp'] = check_smtp(app)
    return report
