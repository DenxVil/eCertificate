#!/usr/bin/env python
"""Inspect and optionally process jobs.

Usage:
  python scripts\inspect_jobs.py           # list jobs
  python scripts\inspect_jobs.py --process <job_id>   # run process_job for job_id
"""
import sys
import os
# Ensure project root is on sys.path so we can import app package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.models import db, Job
from app.routes.jobs import process_job

app = create_app(os.getenv('FLASK_ENV', 'development'))

def list_jobs():
    with app.app_context():
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        if not jobs:
            print('No jobs found')
            return
        for j in jobs:
            print(f'ID: {j.id} | Status: {j.status} | Total: {j.total_certificates} | Generated: {j.generated_certificates} | Error: {j.error_message}')


def list_events():
    from app.models import Event
    with app.app_context():
        events = Event.query.all()
        if not events:
            print('No events found')
            return
        for e in events:
            tpl = e.template_path or '<none>'
            exists = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], tpl)) if e.template_path else False
            print(f'Event ID: {e.id} | Name: {e.name} | template_path: {tpl} | exists: {exists}')


def run_job(job_id):
    with app.app_context():
        job = Job.query.get(job_id)
        if not job:
            print('Job not found')
            return
        print('Before processing:', job.id, job.status, job.error_message)
        try:
            process_job(app, job_id)
            job = Job.query.get(job_id)
            print('After processing:', job.id, job.status, job.error_message)
        except Exception as e:
            print('Exception while processing job:', e)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        list_jobs()
    elif sys.argv[1] == '--events':
        list_events()
    elif sys.argv[1] in ('--process', '-p') and len(sys.argv) == 3:
        try:
            jid = int(sys.argv[2])
        except ValueError:
            print('Invalid job id')
            sys.exit(1)
        run_job(jid)
    else:
        print('Usage: scripts\\inspect_jobs.py [--process <job_id>]')
