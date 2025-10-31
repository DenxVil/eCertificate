"""Developer dashboard routes for system monitoring and configuration."""
from flask import Blueprint, render_template, jsonify, request, current_app
import os
import logging
from datetime import datetime
import sys
from collections import OrderedDict

developer_bp = Blueprint('developer', __name__)
logger = logging.getLogger(__name__)


def get_env_configuration():
    """Get current environment configuration status."""
    # Define expected environment variables
    expected_vars = OrderedDict([
        # Flask Configuration
        ('FLASK_APP', {'category': 'Flask', 'required': False, 'description': 'Flask application entry point'}),
        ('FLASK_ENV', {'category': 'Flask', 'required': False, 'description': 'Flask environment (development/production)'}),
        ('FLASK_DEBUG', {'category': 'Flask', 'required': False, 'description': 'Enable debug mode'}),
        ('SECRET_KEY', {'category': 'Flask', 'required': True, 'description': 'Flask secret key for sessions'}),
        ('PORT', {'category': 'Flask', 'required': False, 'description': 'Application port'}),
        
        # Database Configuration
        ('DATABASE_URL', {'category': 'Database', 'required': False, 'description': 'Database connection string'}),
        ('MONGO_URI', {'category': 'Database', 'required': False, 'description': 'MongoDB connection URI'}),
        
        # Mail Configuration
        ('MAIL_SERVER', {'category': 'Mail', 'required': True, 'description': 'SMTP server address'}),
        ('MAIL_PORT', {'category': 'Mail', 'required': True, 'description': 'SMTP server port'}),
        ('MAIL_USE_TLS', {'category': 'Mail', 'required': True, 'description': 'Use TLS for SMTP'}),
        ('MAIL_USERNAME', {'category': 'Mail', 'required': True, 'description': 'SMTP username/email'}),
        ('MAIL_PASSWORD', {'category': 'Mail', 'required': True, 'description': 'SMTP password/app password'}),
        ('MAIL_DEFAULT_SENDER', {'category': 'Mail', 'required': True, 'description': 'Default sender email'}),
        
        # Telegram Configuration
        ('TELEGRAM_BOT_TOKEN', {'category': 'Telegram', 'required': False, 'description': 'Telegram bot token'}),
        
        # Upload Configuration
        ('UPLOAD_FOLDER', {'category': 'Upload', 'required': False, 'description': 'Upload directory'}),
        ('OUTPUT_FOLDER', {'category': 'Upload', 'required': False, 'description': 'Generated certificates directory'}),
        ('MAX_CONTENT_LENGTH', {'category': 'Upload', 'required': False, 'description': 'Maximum upload size'}),
        ('ALLOWED_EXTENSIONS', {'category': 'Upload', 'required': False, 'description': 'Allowed file extensions'}),
        
        # Alignment Configuration
        ('ENABLE_ALIGNMENT_CHECK', {'category': 'Alignment', 'required': False, 'description': 'Enable alignment verification'}),
        ('ALIGNMENT_TOLERANCE_PX', {'category': 'Alignment', 'required': False, 'description': 'Alignment tolerance in pixels'}),
        ('ALIGNMENT_MAX_ATTEMPTS', {'category': 'Alignment', 'required': False, 'description': 'Maximum alignment verification attempts'}),
        ('EMAIL_MAX_RETRIES', {'category': 'Alignment', 'required': False, 'description': 'Maximum email send retries'}),
        ('FIELD_POSITION_TOLERANCE_PX', {'category': 'Alignment', 'required': False, 'description': 'Field position tolerance in pixels'}),
    ])
    
    config_status = OrderedDict()
    
    for var_name, var_info in expected_vars.items():
        # Check environment variable
        env_value = os.getenv(var_name)
        
        # Also check Flask config
        flask_value = current_app.config.get(var_name)
        
        is_set = env_value is not None or flask_value is not None
        
        # Mask sensitive values
        if is_set and any(keyword in var_name.lower() for keyword in ['password', 'secret', 'token', 'key']):
            display_value = '***HIDDEN***'
        elif is_set:
            # Handle sets and other non-JSON-serializable types
            value = env_value or flask_value
            if isinstance(value, set):
                display_value = ', '.join(sorted(value))
            elif isinstance(value, (list, tuple)):
                display_value = ', '.join(str(v) for v in value)
            else:
                display_value = str(value)
        else:
            display_value = None
        
        config_status[var_name] = {
            'category': var_info['category'],
            'required': var_info['required'],
            'description': var_info['description'],
            'is_set': is_set,
            'value': display_value,
            'source': 'environment' if env_value is not None else ('config' if flask_value is not None else 'not set')
        }
    
    return config_status


def get_mail_configuration_details():
    """Get detailed mail configuration status."""
    mail_config = {
        'MAIL_SERVER': {
            'env': os.getenv('MAIL_SERVER'),
            'config': current_app.config.get('MAIL_SERVER'),
            'is_set': bool(os.getenv('MAIL_SERVER') or current_app.config.get('MAIL_SERVER'))
        },
        'MAIL_PORT': {
            'env': os.getenv('MAIL_PORT'),
            'config': current_app.config.get('MAIL_PORT'),
            'is_set': bool(os.getenv('MAIL_PORT') or current_app.config.get('MAIL_PORT'))
        },
        'MAIL_USE_TLS': {
            'env': os.getenv('MAIL_USE_TLS'),
            'config': current_app.config.get('MAIL_USE_TLS'),
            'is_set': bool(os.getenv('MAIL_USE_TLS') or current_app.config.get('MAIL_USE_TLS'))
        },
        'MAIL_USERNAME': {
            'env': os.getenv('MAIL_USERNAME'),
            'config': current_app.config.get('MAIL_USERNAME'),
            'is_set': bool(os.getenv('MAIL_USERNAME') or current_app.config.get('MAIL_USERNAME'))
        },
        'MAIL_PASSWORD': {
            'env': '***HIDDEN***' if os.getenv('MAIL_PASSWORD') else None,
            'config': '***HIDDEN***' if current_app.config.get('MAIL_PASSWORD') else None,
            'is_set': bool(os.getenv('MAIL_PASSWORD') or current_app.config.get('MAIL_PASSWORD'))
        },
        'MAIL_DEFAULT_SENDER': {
            'env': os.getenv('MAIL_DEFAULT_SENDER'),
            'config': current_app.config.get('MAIL_DEFAULT_SENDER'),
            'is_set': bool(os.getenv('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_DEFAULT_SENDER'))
        }
    }
    
    # Check if all required mail configs are set
    all_set = all(mail_config[key]['is_set'] for key in mail_config.keys())
    
    # Check specific issue: MAIL_USERNAME
    mail_username_issue = not mail_config['MAIL_USERNAME']['is_set']
    
    return {
        'config': mail_config,
        'all_configured': all_set,
        'mail_username_issue': mail_username_issue,
        'missing': [key for key, val in mail_config.items() if not val['is_set']]
    }


def get_system_info():
    """Get system information."""
    return {
        'python_version': sys.version,
        'python_executable': sys.executable,
        'flask_version': current_app.__class__.__module__,
        'app_config': current_app.config['ENV'] if 'ENV' in current_app.config else 'unknown',
        'debug_mode': current_app.debug,
        'testing_mode': current_app.testing,
    }


@developer_bp.route('/')
def dashboard():
    """Render the developer dashboard."""
    return render_template('developer/dashboard.html')


@developer_bp.route('/api/env-config')
def api_env_config():
    """Get environment configuration as JSON."""
    try:
        config_status = get_env_configuration()
        
        # Group by category
        grouped = {}
        for var_name, var_data in config_status.items():
            category = var_data['category']
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                'name': var_name,
                **var_data
            })
        
        return jsonify({
            'success': True,
            'grouped': grouped,
            'all_vars': config_status
        })
    except Exception as e:
        logger.exception("Error getting environment configuration")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@developer_bp.route('/api/mail-config')
def api_mail_config():
    """Get detailed mail configuration status."""
    try:
        mail_details = get_mail_configuration_details()
        return jsonify({
            'success': True,
            **mail_details
        })
    except Exception as e:
        logger.exception("Error getting mail configuration")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@developer_bp.route('/api/system-info')
def api_system_info():
    """Get system information."""
    try:
        info = get_system_info()
        return jsonify({
            'success': True,
            **info
        })
    except Exception as e:
        logger.exception("Error getting system information")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@developer_bp.route('/api/logs')
def api_logs():
    """Get application logs."""
    try:
        # Get log file path (if configured)
        log_file = current_app.config.get('LOG_FILE')
        
        if not log_file or not os.path.exists(log_file):
            # Return in-memory logs if available
            return jsonify({
                'success': True,
                'logs': [],
                'message': 'No log file configured or file not found'
            })
        
        # Read last N lines
        lines_to_read = int(request.args.get('lines', 100))
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-lines_to_read:] if len(lines) > lines_to_read else lines
        
        return jsonify({
            'success': True,
            'logs': [line.strip() for line in recent_lines],
            'total_lines': len(lines),
            'returned_lines': len(recent_lines)
        })
    except Exception as e:
        logger.exception("Error reading logs")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@developer_bp.route('/api/azure-logs')
def api_azure_logs():
    """Get Azure Application Insights configuration and status."""
    try:
        # Check if Azure is configured
        instrumentation_key = os.getenv('APPINSIGHTS_INSTRUMENTATION_KEY')
        connection_string = os.getenv('APPINSIGHTS_CONNECTION_STRING')
        
        is_configured = bool(instrumentation_key or connection_string)
        
        # Get configuration details (mask sensitive data)
        azure_config = {
            'configured': is_configured,
            'has_instrumentation_key': bool(instrumentation_key),
            'has_connection_string': bool(connection_string),
            'instrumentation_key_preview': (
                instrumentation_key[:8] + '...' + instrumentation_key[-4:] 
                if instrumentation_key and len(instrumentation_key) > 12 
                else None
            ),
            'status': 'enabled' if is_configured else 'not_configured'
        }
        
        # If configured, try to get the logger status
        if is_configured:
            try:
                import logging
                root_logger = logging.getLogger()
                azure_handlers = [
                    h for h in root_logger.handlers 
                    if 'AzureLogHandler' in str(type(h))
                ]
                azure_config['handler_active'] = len(azure_handlers) > 0
                azure_config['handler_count'] = len(azure_handlers)
            except Exception as e:
                azure_config['handler_error'] = str(e)
        
        return jsonify({
            'success': True,
            'azure_config': azure_config,
            'message': 'Azure logs can be viewed in Azure Portal Application Insights' if is_configured else 'Azure Application Insights not configured'
        })
    except Exception as e:
        logger.exception("Error checking Azure logs configuration")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@developer_bp.route('/api/live-activity')
def api_live_activity():
    """Get live bot/system activity."""
    # This would typically connect to a message queue or event stream
    # For now, return recent activity from logs or database
    try:
        # Placeholder for live activity monitoring
        # In a real implementation, this would connect to:
        # - Message queue (Redis, RabbitMQ)
        # - Event stream (SSE, WebSocket)
        # - Database activity log
        
        activities = [
            {
                'timestamp': datetime.now().isoformat(),
                'type': 'info',
                'message': 'Developer dashboard loaded',
                'component': 'web_ui'
            }
        ]
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        logger.exception("Error getting live activity")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@developer_bp.route('/logs')
def logs_viewer():
    """Render the logs viewer page."""
    return render_template('developer/logs.html')


@developer_bp.route('/live-monitor')
def live_monitor():
    """Render the live activity monitor page."""
    return render_template('developer/live_monitor.html')
