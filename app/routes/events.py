"""Event management routes."""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from app.models import db, Event
from app.utils import allowed_file, save_uploaded_file
import os

events_bp = Blueprint('events', __name__)


@events_bp.route('/')
def list_events():
    """List all events."""
    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template('events/list.html', events=events)


@events_bp.route('/create', methods=['GET', 'POST'])
def create_event():
    """Create a new event."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Event name is required', 'error')
            return redirect(url_for('events.create_event'))
        
        # Handle template upload
        template_path = None
        if 'template' in request.files:
            template_file = request.files['template']
            if template_file and template_file.filename and \
               allowed_file(template_file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                template_path = save_uploaded_file(template_file, current_app.config['UPLOAD_FOLDER'])
        
        # Create event
        event = Event(
            name=name,
            description=description,
            template_path=template_path
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('events.list_events'))
    
    return render_template('events/create.html')


@events_bp.route('/<int:event_id>')
def view_event(event_id):
    """View event details."""
    event = Event.query.get_or_404(event_id)
    return render_template('events/view.html', event=event)


@events_bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    """Edit an event."""
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        event.name = request.form.get('name', event.name)
        event.description = request.form.get('description', event.description)
        
        # Handle template upload
        if 'template' in request.files:
            template_file = request.files['template']
            if template_file and template_file.filename and \
               allowed_file(template_file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                # Delete old template if exists
                if event.template_path and os.path.exists(event.template_path):
                    os.remove(event.template_path)
                
                event.template_path = save_uploaded_file(template_file, current_app.config['UPLOAD_FOLDER'])
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    return render_template('events/edit.html', event=event)


@events_bp.route('/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete an event."""
    event = Event.query.get_or_404(event_id)
    
    # Delete template file if exists
    if event.template_path and os.path.exists(event.template_path):
        os.remove(event.template_path)
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events.list_events'))


# API endpoints
@events_bp.route('/api', methods=['GET'])
def api_list_events():
    """API endpoint to list all events."""
    events = Event.query.all()
    return jsonify([event.to_dict() for event in events])


@events_bp.route('/api/<int:event_id>', methods=['GET'])
def api_get_event(event_id):
    """API endpoint to get a specific event."""
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())
