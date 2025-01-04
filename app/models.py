from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(200))  # Store URL for uploaded or default avatar
    
    # Preferences
    default_view = db.Column(db.String(20), default='list')  # 'list' or 'kanban'
    theme = db.Column(db.String(20), default='light')  # 'light', 'dark', or 'system'
    default_priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', or 'high'
    
    # Notification Settings
    email_notifications = db.Column(db.Boolean, default=True)
    due_date_reminder = db.Column(db.Integer, default=1)  # days before
    project_updates = db.Column(db.Boolean, default=True)
    task_assignments = db.Column(db.Boolean, default=True)

    # Relationships
    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    user_notifications = db.relationship('Notification', backref='user', lazy='dynamic')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='In Progress')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Todo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_event_id = db.Column(db.String(100), unique=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    notification_type = db.Column(db.String(50), default='default')  # project, task, deadline, default
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Notification {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'type': self.type,
            'read': self.read,
            'timestamp': self.timestamp.isoformat(),
            'related_id': self.related_id
        }