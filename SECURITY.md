# Security Guidelines

## Overview

This document outlines security practices and configurations for the eCertificate application.

## Environment Variables & Secrets Management

### Required Environment Variables

All sensitive credentials MUST be stored in environment variables, never hardcoded:

- `SECRET_KEY` - Flask session encryption key (change from default in production)
- `MONGO_URI` - MongoDB/Cosmos DB connection string
- `MAIL_USERNAME` - SMTP username for email delivery
- `MAIL_PASSWORD` - SMTP password (use app-specific passwords)
- `TELEGRAM_BOT_TOKEN` - Telegram bot authentication token

### Azure & Telegram Integration

The application supports monitoring and management through Telegram bot integration:

1. **Telegram Bot Token**: Stored in `TELEGRAM_BOT_TOKEN` environment variable
   - Never hardcoded in source code
   - Retrieved using `os.getenv('TELEGRAM_BOT_TOKEN')`
   - Used for bot authentication with Telegram API

2. **Azure Monitoring Integration**: 
   - Users can access Azure logs and system information via `@NexusAiProbot` on Telegram
   - Access tokens and credentials are managed through Azure's secure credential storage
   - No access tokens are stored in the application codebase

### Best Practices

1. **Never commit sensitive data**:
   - `.env` files are in `.gitignore`
   - No tokens, passwords, or keys in source code
   - Use environment-specific configuration

2. **Production Deployment**:
   - Set `FLASK_ENV=production`
   - Set `FLASK_DEBUG=False`
   - Use strong, randomly generated `SECRET_KEY`
   - Enable HTTPS/TLS for all connections
   - Use Azure Key Vault or similar for production secrets

3. **Database Security**:
   - Use connection strings with authentication
   - Enable SSL/TLS for MongoDB connections
   - For Azure Cosmos DB, use the secure connection string format:
     ```
     mongodb://[username]:[password]@[host]:10255/[database]?ssl=true&replicaSet=globaldb
     ```

4. **Email Security**:
   - Use app-specific passwords for Gmail/Outlook
   - Enable 2FA on email accounts
   - Use TLS for SMTP connections (port 587)

5. **File Upload Security**:
   - File type validation enforced (`ALLOWED_EXTENSIONS`)
   - File size limits configured (`MAX_CONTENT_LENGTH`)
   - Uploaded files saved with secure filenames (using `werkzeug.secure_filename`)
   - Path traversal attacks prevented in download endpoints

## Access Control

### Telegram Bot
- Commands are available to all users who have the bot token
- For production, implement user authentication/authorization
- Consider restricting bot access to specific Telegram user IDs

### Web Interface
- Currently no authentication (suitable for internal/trusted networks)
- For production, implement authentication middleware
- Consider OAuth2/OIDC integration with Azure AD

## Data Protection

1. **Participant Data**:
   - Participant emails and names stored in MongoDB
   - Consider encrypting PII at rest
   - Implement data retention policies

2. **Generated Certificates**:
   - Stored in `OUTPUT_FOLDER` directory
   - Consider Azure Blob Storage for production
   - Implement access controls for certificate downloads

## Monitoring & Incident Response

1. **Logging**:
   - Application logs errors and warnings
   - Monitor logs for suspicious activity
   - Azure Application Insights integration recommended

2. **Azure Monitoring** (via @NexusAiProbot):
   - Authorized users can query system status
   - Access controlled through Telegram user verification
   - Logs all monitoring access attempts

## Security Checklist for Deployment

- [ ] All environment variables configured
- [ ] `SECRET_KEY` changed from default
- [ ] `FLASK_DEBUG` set to False
- [ ] HTTPS/TLS enabled
- [ ] Database connections use SSL
- [ ] Email uses TLS
- [ ] File upload limits configured
- [ ] Access control implemented
- [ ] Logging and monitoring configured
- [ ] Backup strategy in place
- [ ] Incident response plan documented

## Vulnerability Reporting

If you discover a security vulnerability, please report it to the maintainers privately.

## Compliance Notes

- GDPR: Ensure participant consent for data processing and email communications
- Data Retention: Implement policies for deleting old certificates and participant data
- Audit Trail: Consider logging all certificate generation and email activities
