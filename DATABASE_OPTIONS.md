# Database Options for eCertificate

This document describes alternative database options that can be used with the eCertificate application instead of MongoDB.

## Current Implementation: MongoDB

The application currently uses **MongoDB** with Flask-PyMongo. The data model consists of three collections:
- **Events**: Certificate templates and event information
- **Jobs**: Certificate generation job tracking
- **Participants**: Individual participant data for each job

## Alternative Database Options

### 1. PostgreSQL (Recommended Alternative)

PostgreSQL is a powerful, open-source relational database with excellent Python support.

**Pros:**
- ACID compliant (better data integrity)
- Excellent JSON support (can store document-like data)
- Strong community and enterprise support
- Better for complex queries and relationships
- Free and open-source

**Cons:**
- Requires schema definition upfront
- More complex setup than MongoDB

**Implementation Steps:**

1. **Install dependencies:**
```bash
pip install Flask-SQLAlchemy psycopg2-binary
```

2. **Update requirements.txt:**
```
Flask-SQLAlchemy
psycopg2-binary
```

3. **Environment variable:**
```env
# For local PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/ecertificate

# For Docker Compose
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ecertificate
```

4. **Docker Compose service:**
```yaml
postgres:
  image: postgres:15
  restart: unless-stopped
  environment:
    POSTGRES_DB: ecertificate
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  ports:
    - "5432:5432"
  volumes:
    - postgres-data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 2. MySQL/MariaDB

MySQL is one of the most popular relational databases, and MariaDB is its open-source fork.

**Pros:**
- Very popular and well-documented
- Good performance for read-heavy workloads
- Wide hosting support
- MariaDB is fully open-source

**Cons:**
- Less feature-rich than PostgreSQL
- JSON support is more limited

**Implementation:**

1. **Install dependencies:**
```bash
pip install Flask-SQLAlchemy pymysql
```

2. **Environment variable:**
```env
# For local MySQL
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/ecertificate

# For Docker Compose
DATABASE_URL=mysql+pymysql://root:rootpassword@mysql:3306/ecertificate
```

3. **Docker Compose service:**
```yaml
mysql:
  image: mysql:8.0
  restart: unless-stopped
  environment:
    MYSQL_DATABASE: ecertificate
    MYSQL_ROOT_PASSWORD: rootpassword
  ports:
    - "3306:3306"
  volumes:
    - mysql-data:/var/lib/mysql
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 3. SQLite (Development Only)

SQLite is a file-based database, perfect for development and testing.

**Pros:**
- No server required (file-based)
- Zero configuration
- Perfect for development/testing
- Included with Python

**Cons:**
- **NOT recommended for production**
- No concurrent writes
- Limited scalability
- No network access

**Implementation:**

1. **Install dependencies:**
```bash
pip install Flask-SQLAlchemy
```

2. **Environment variable:**
```env
DATABASE_URL=sqlite:///ecertificate.db
```

**Note:** SQLite should only be used for local development and testing, never in production.

### 4. Azure Cosmos DB (MongoDB API)

If you're already using MongoDB and deploying to Azure, Cosmos DB with MongoDB API is a drop-in replacement.

**Pros:**
- Fully managed cloud database
- Global distribution
- Auto-scaling
- MongoDB wire protocol compatible (minimal code changes)
- SLA guarantees

**Cons:**
- Azure-specific (vendor lock-in)
- More expensive than other options
- Requires Azure account

**Implementation:**

1. **Keep existing Flask-PyMongo setup**

2. **Connection string:**
```env
MONGO_URI=mongodb://your-cosmosdb-account:your-key@your-cosmosdb-account.mongo.cosmos.azure.com:10255/ecertificate?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@your-cosmosdb-account@
```

**Note:** Already supported! Just change the MONGO_URI to your Cosmos DB connection string.

### 5. MongoDB Atlas (Cloud MongoDB)

MongoDB's official cloud-hosted database service.

**Pros:**
- Fully managed MongoDB
- Free tier available
- Easy to set up
- Automatic backups
- Global clusters

**Cons:**
- Requires internet connection
- Free tier has limitations
- Data stored in cloud (privacy considerations)

**Implementation:**

1. **Keep existing Flask-PyMongo setup**

2. **Connection string:**
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/ecertificate?retryWrites=true&w=majority
```

**Note:** Already supported! Just change the MONGO_URI to your Atlas connection string.

### 6. Redis + PostgreSQL (Hybrid)

Use Redis for session/cache and PostgreSQL for persistent data.

**Pros:**
- Extremely fast read/write (Redis)
- Reliable persistence (PostgreSQL)
- Good for high-traffic applications
- Caching built-in

**Cons:**
- More complex setup
- Requires managing two databases
- Higher resource usage

**Implementation:**

1. **Install dependencies:**
```bash
pip install Flask-SQLAlchemy Flask-Redis psycopg2-binary redis
```

2. **Environment variables:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/ecertificate
REDIS_URL=redis://localhost:6379/0
```

## Migration Guide: MongoDB to SQL

If you want to migrate from MongoDB to a SQL database (PostgreSQL/MySQL), you'll need to:

### Step 1: Create SQL Schema

Create a new file `app/models/sql_models.py`:

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    template_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    jobs = db.relationship('Job', backref='event', lazy=True, cascade='all, delete-orphan')

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    total_certificates = db.Column(db.Integer, default=0)
    generated_certificates = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    telegram_chat_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    
    participants = db.relationship('Participant', backref='job', lazy=True, cascade='all, delete-orphan')

class Participant(db.Model):
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    certificate_path = db.Column(db.String(500))
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Step 2: Update Configuration

Update `app/config/db_config.py`:

```python
import os

def get_database_uri() -> str:
    """Read DATABASE_URL from environment."""
    uri = os.getenv("DATABASE_URL")
    if not uri:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set.\n"
            "For PostgreSQL: postgresql://user:pass@host:5432/ecertificate\n"
            "For MySQL: mysql+pymysql://user:pass@host:3306/ecertificate\n"
            "For SQLite (dev only): sqlite:///ecertificate.db"
        )
    return uri
```

### Step 3: Update app/__init__.py

Replace MongoDB initialization with SQLAlchemy:

```python
from flask import Flask
from app.models.sql_models import db
from app.config.db_config import get_database_uri

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # Create tables
    
    # ... rest of configuration
    
    return app
```

### Step 4: Data Migration Script

Create `scripts/migrate_mongo_to_sql.py`:

```python
"""Migrate data from MongoDB to SQL database."""
from app import create_app, mongo
from app.models.sql_models import db, Event, Job, Participant
from bson.objectid import ObjectId

def migrate():
    app = create_app()
    with app.app_context():
        # Migrate Events
        mongo_events = mongo.db.events.find()
        event_map = {}
        
        for mongo_event in mongo_events:
            event = Event(
                name=mongo_event['name'],
                description=mongo_event['description'],
                template_path=mongo_event['template_path'],
                created_at=mongo_event.get('created_at')
            )
            db.session.add(event)
            db.session.flush()
            event_map[str(mongo_event['_id'])] = event.id
        
        # Migrate Jobs
        mongo_jobs = mongo.db.jobs.find()
        job_map = {}
        
        for mongo_job in mongo_jobs:
            job = Job(
                event_id=event_map[str(mongo_job['event_id'])],
                status=mongo_job['status'],
                total_certificates=mongo_job.get('total_certificates', 0),
                generated_certificates=mongo_job.get('generated_certificates', 0),
                created_at=mongo_job.get('created_at'),
                completed_at=mongo_job.get('completed_at'),
                telegram_chat_id=mongo_job.get('telegram_chat_id'),
                error_message=mongo_job.get('error_message')
            )
            db.session.add(job)
            db.session.flush()
            job_map[str(mongo_job['_id'])] = job.id
        
        # Migrate Participants
        mongo_participants = mongo.db.participants.find()
        
        for mongo_participant in mongo_participants:
            participant = Participant(
                job_id=job_map[str(mongo_participant['job_id'])],
                name=mongo_participant['name'],
                email=mongo_participant['email'],
                certificate_path=mongo_participant.get('certificate_path'),
                email_sent=mongo_participant.get('email_sent', False)
            )
            db.session.add(participant)
        
        db.session.commit()
        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
```

## Recommendation Matrix

| Use Case | Recommended Database | Reason |
|----------|---------------------|---------|
| Small projects, simple data | **MongoDB** (current) | Easy setup, flexible schema |
| Production app, complex queries | **PostgreSQL** | Best balance of features and reliability |
| Enterprise, existing MySQL infrastructure | **MySQL/MariaDB** | Compatibility, widespread support |
| Local development/testing | **SQLite** | Zero configuration, no server needed |
| Azure cloud deployment | **Azure Cosmos DB** | Managed service, global distribution |
| High traffic, caching needs | **Redis + PostgreSQL** | Performance + reliability |
| Existing MongoDB code, cloud needed | **MongoDB Atlas** | Drop-in replacement, fully managed |

## Summary

**Current Setup (MongoDB):** Good choice for this application due to flexible schema and document storage.

**Best Alternative:** **PostgreSQL** - if you need ACID compliance, complex queries, or prefer SQL. It offers the best combination of features, performance, and reliability.

**For Cloud Deployment:** Use **MongoDB Atlas** (easiest) or **Azure Cosmos DB** (if on Azure).

**For Development:** Use **SQLite** for quick local testing, **MongoDB** with Docker Compose for full-stack development.

**Not Recommended:** Switching databases just for the sake of it. MongoDB works well for this use case. Only switch if you have specific requirements (ACID compliance, complex joins, existing SQL infrastructure, etc.).
