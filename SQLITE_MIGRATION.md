# SQLite Migration Summary

## Overview

The eCertificate application has been migrated from **MongoDB** to **SQLite** for simplified deployment and easier development setup.

## Why SQLite?

- **Zero Configuration**: No database server to install or manage
- **File-Based**: Database is a single file (ecertificate.db)
- **Perfect for Small/Medium Apps**: Handles thousands of certificates easily
- **Easy Backup**: Just copy the .db file
- **Development Friendly**: No Docker containers needed for local development
- **Production Ready**: Works great for single-server deployments

## What Changed?

### 1. Database Layer
**Before (MongoDB):**
- Required MongoDB server running
- Used Flask-PyMongo for database access
- Documents stored in collections
- Used ObjectId for IDs

**After (SQLite):**
- File-based database (ecertificate.db)
- Uses Flask-SQLAlchemy ORM
- Data stored in relational tables
- Uses auto-incrementing integer IDs

### 2. Model Access Patterns
**Before (MongoDB):**
```python
event = Event.find_by_id(event_id)
name = event['name']  # Dictionary access
```

**After (SQLite):**
```python
event = Event.find_by_id(event_id)
name = event.name  # Attribute access
```

### 3. Configuration
**Before (MongoDB):**
```env
MONGO_URI=mongodb://mongo:27017/eCertificate
```

**After (SQLite):**
```env
DATABASE_URL=sqlite:///ecertificate.db
```

### 4. Docker Compose
**Before (MongoDB):**
- App service + MongoDB service
- Health checks for MongoDB
- Network dependency management

**After (SQLite):**
- App service only
- Database file in volume
- Simpler configuration

## Files Changed

### New Files
1. `app/models/sqlite_models.py` - SQLAlchemy models for Event, Job, Participant
2. `app/config/db_config.py` - Database configuration helper

### Modified Files
1. `app/__init__.py` - Initialize SQLAlchemy instead of PyMongo
2. `app/routes/events.py` - Updated to use SQLAlchemy models
3. `app/routes/jobs.py` - Updated to use SQLAlchemy models  
4. `bot.py` - Updated to use SQLAlchemy models
5. `requirements.txt` - Flask-SQLAlchemy instead of Flask-PyMongo
6. `docker-compose.yml` - Removed MongoDB service
7. `.env.example` - SQLite as default database
8. `README.md` - Updated instructions
9. `.gitignore` - Added SQLite database files

### Removed Dependencies
- `Flask-PyMongo`
- `dnspython` (MongoDB dependency)
- `bson` / `ObjectId` usage

## Database Schema

### Events Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| name | String(255) | Event name |
| description | Text | Event description |
| template_path | String(500) | Path to certificate template |
| created_at | DateTime | Creation timestamp |

### Jobs Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| event_id | Integer (FK) | Reference to events.id |
| status | String(50) | Job status (pending/processing/completed/failed) |
| total_certificates | Integer | Total certificates to generate |
| generated_certificates | Integer | Certificates generated so far |
| created_at | DateTime | Creation timestamp |
| completed_at | DateTime | Completion timestamp |
| telegram_chat_id | String(100) | Telegram chat ID (optional) |
| error_message | Text | Error message if failed |

### Participants Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| job_id | Integer (FK) | Reference to jobs.id |
| name | String(255) | Participant name |
| email | String(255) | Participant email |
| certificate_path | String(500) | Path to generated certificate |
| email_sent | Boolean | Whether email was sent |
| created_at | DateTime | Creation timestamp |

## How to Use

### Development
```bash
# No database setup needed!
pip install -r requirements.txt
python app.py
```

### Docker
```bash
docker compose up --build
```

### Database Management

**View database:**
```bash
sqlite3 ecertificate.db
sqlite> .tables
sqlite> SELECT * FROM events;
sqlite> .quit
```

**Backup database:**
```bash
cp ecertificate.db ecertificate_backup.db
```

**Reset database:**
```bash
rm ecertificate.db
python app.py  # Creates fresh database
```

## Migrating to Other Databases

If you need MongoDB, PostgreSQL, or MySQL later, see [DATABASE_OPTIONS.md](DATABASE_OPTIONS.md) for:
- Migration scripts
- Docker Compose configurations
- Setup instructions
- Code changes needed

## Performance Considerations

**SQLite is great for:**
- Development and testing
- Small to medium production deployments (< 100,000 records)
- Single-server applications
- Applications with < 100 concurrent users

**Consider PostgreSQL/MySQL if you need:**
- Multiple application servers
- Very high concurrent writes
- Complex analytical queries
- Horizontal scaling

## Troubleshooting

**"Database is locked" error:**
- SQLite supports one writer at a time
- This is normal for heavy concurrent writes
- Solution: Use connection pooling or switch to PostgreSQL

**Database file not found:**
- The app creates it automatically on first run
- Check write permissions in the application directory

**Data persistence in Docker:**
- Database is in a named volume (`sqlite-data`)
- Use `docker compose down -v` to reset (removes data!)

## Backward Compatibility

The MongoDB code is preserved in git history. To revert:

```bash
git log --all --oneline | grep -i mongo
git checkout <commit-hash> -- app/models/mongo_models.py app/__init__.py
# Update requirements.txt and docker-compose.yml accordingly
```

## Security Notes

- SQLite database file permissions are important
- In production, ensure the .db file is not web-accessible
- Regular backups are easier (just copy the file)
- Consider encrypting the database file for sensitive data

## Conclusion

The migration to SQLite provides a simpler, more accessible development experience while maintaining all functionality. For most use cases, SQLite will perform excellently. As the application grows, migration paths to PostgreSQL or MySQL are well-documented in DATABASE_OPTIONS.md.
