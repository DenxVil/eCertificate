"""Event management routes."""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from app.models.mongo_models import Event
from app.utils import allowed_file, save_uploaded_file
from bson.objectid import ObjectId
import os
import logging

events_bp = Blueprint('events', __name__)
logger = logging.getLogger(__name__)


@events_bp.route('/')
def list_events():
    """List all events."""
    try:
        events = Event.find_all()
        return render_template('events/list.html', events=events)
    except RuntimeError as e:
        flash(str(e), 'error')
        return render_template('events/list.html', events=[])
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        flash('An error occurred while loading events', 'error')
        return render_template('events/list.html', events=[])


@events_bp.route('/create', methods=['GET', 'POST'])
def create_event():
    """Create a new event."""
    if request.method == 'POST':
        try:
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
            Event.create(
                name=name,
                description=description,
                template_path=template_path
            )
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('events.list_events'))
        except RuntimeError as e:
            flash(str(e), 'error')
            return redirect(url_for('events.create_event'))
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            flash('An error occurred while creating the event', 'error')
            return redirect(url_for('events.create_event'))
    
    return render_template('events/create.html')


@events_bp.route('/<event_id>')
def view_event(event_id):
    """View event details."""
    try:
        event = Event.find_by_id(event_id)
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('events.list_events'))
        return render_template('events/view.html', event=event)
    except RuntimeError as e:
        flash(str(e), 'error')
        return redirect(url_for('events.list_events'))
    except Exception as e:
        logger.error(f"Error viewing event: {e}")
        flash('An error occurred while loading the event', 'error')
        return redirect(url_for('events.list_events'))


@events_bp.route('/<event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    """Edit an event."""
    event = Event.find_by_id(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events.list_events'))
    
    if request.method == 'POST':
        name = request.form.get('name', event['name'])
        description = request.form.get('description', event['description'])
        template_path = event['template_path']

        # Handle template upload
        if 'template' in request.files:
            template_file = request.files['template']
            if template_file and template_file.filename and \
               allowed_file(template_file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                # Delete old template if exists
                if template_path and os.path.exists(template_path):
                    os.remove(template_path)
                
                template_path = save_uploaded_file(template_file, current_app.config['UPLOAD_FOLDER'])
        
        Event.update(event_id, name, description, template_path)
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    return render_template('events/edit.html', event=event)


@events_bp.route('/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete an event."""
    event = Event.find_by_id(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events.list_events'))
    
    # Delete template file if exists
    if event.get('template_path') and os.path.exists(event['template_path']):
        os.remove(event['template_path'])
    
    Event.delete(event_id)
    
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
