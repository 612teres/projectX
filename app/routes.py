from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db, socketio, send_notification
from app.models import Project, Task, CalendarEvent, Notification, User
from datetime import datetime, timedelta
from app.google_calendar_integration import GoogleCalendarService
import json
from sqlalchemy.sql import func
import os
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO

main = Blueprint('main', __name__)

UPLOAD_FOLDER = 'app/static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter_by(owner_id=current_user.id).all()
    tasks = Task.query.filter_by(assignee_id=current_user.id).order_by(Task.due_date.asc()).all()
    events = CalendarEvent.query.filter_by(user_id=current_user.id).all()
    
    # Calculate project statistics
    for project in projects:
        total_tasks = len(project.tasks)
        completed_tasks = len([task for task in project.tasks if task.status == 'Completed'])
        project.progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Add current time and timedelta for deadline calculations
    now = datetime.utcnow()
    
    # Get upcoming deadlines (next 7 days)
    upcoming_tasks = [
        task for task in tasks 
        if task.due_date and task.due_date <= now + timedelta(days=7) and task.status != 'Completed'
    ]
    
    # Get completed tasks count
    completed_tasks = len([task for task in tasks if task.status == 'Completed'])
    
    return render_template(
        'dashboard.html',
        projects=projects,
        tasks=tasks,
        events=events,
        now=now,
        timedelta=timedelta,
        upcoming_tasks=len(upcoming_tasks),
        completed_tasks=completed_tasks
    )

@main.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id:
        flash('You do not have permission to view this project.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Calculate project statistics
    total_tasks = len(project.tasks)
    completed_tasks = len([task for task in project.tasks if task.status == 'Completed'])
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Group tasks by status
    tasks_by_status = {
        'Todo': [task for task in project.tasks if task.status == 'Todo'],
        'In Progress': [task for task in project.tasks if task.status == 'In Progress'],
        'Completed': [task for task in project.tasks if task.status == 'Completed']
    }
    
    return render_template(
        'project_detail.html',
        project=project,
        progress=progress,
        tasks_by_status=tasks_by_status,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks
    )

@main.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check if user has permission to delete the project
    if project.owner_id != current_user.id:
        flash('You do not have permission to delete this project.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Delete associated tasks and notifications
        Task.query.filter_by(project_id=project_id).delete()
        Notification.query.filter(
            db.and_(
                Notification.user_id == current_user.id,
                Notification.message.like(f"%{project.title}%")
            )
        ).delete()
        
        # Delete the project
        db.session.delete(project)
        db.session.commit()
        
        flash('Project deleted successfully!', 'success')
        return jsonify({'status': 'success', 'redirect': url_for('main.dashboard')})
    except Exception as e:
        db.session.rollback()
        flash('Error deleting project. Please try again.', 'error')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d')
        
        project = Project(
            title=title,
            description=description,
            deadline=deadline,
            owner_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        
        # Create notification for new project
        create_notification(
            current_user.id,
            f"New project created: {title}",
            notification_type='project'
        )
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('project_form.html')

@main.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        priority = request.form.get('priority')
        project_id = request.form.get('project_id')
        assignee_id = request.form.get('assignee_id')
        
        # Verify project exists
        project = Project.query.get_or_404(project_id)
        
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            project_id=project_id,
            assignee_id=assignee_id or current_user.id
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Create notification for task assignment
        if assignee_id and int(assignee_id) != current_user.id:
            create_notification(
                int(assignee_id),
                f"You've been assigned a new task: {title}",
                notification_type='task'
            )
        
        # Notify project owner if different from assignee
        if project.owner_id != current_user.id:
            create_notification(
                project.owner_id,
                f"New task added to your project {project.title}: {title}",
                notification_type='task'
            )
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('main.project_detail', project_id=project_id))
    
    # Get list of projects for the form
    projects = Project.query.filter_by(owner_id=current_user.id).all()
    return render_template('task_form.html', projects=projects)

@main.route('/task/<int:task_id>/update', methods=['POST'])
@login_required
def update_task(task_id):
    new_status = request.json.get('status')
    
    task = Task.query.get_or_404(task_id)
    old_status = task.status
    task.status = new_status
    db.session.commit()
    
    # Create notification for status change
    notification_message = f"Task '{task.title}' status updated to {new_status}"
    
    # Notify task assignee if different from current user
    if task.assignee_id and task.assignee_id != current_user.id:
        create_notification(
            task.assignee_id,
            notification_message,
            notification_type='task'
        )
    
    # Notify project owner if different from current user and assignee
    project = Project.query.get(task.project_id)
    if project.owner_id != current_user.id and project.owner_id != task.assignee_id:
        create_notification(
            project.owner_id,
            notification_message,
            notification_type='task'
        )
    
    return jsonify({
        'status': 'success',
        'message': notification_message,
        'task_status': new_status
    })

# Google Calendar Integration routes
@main.route('/calendar/authorize')
@login_required
def authorize_google_calendar():
    flow = GoogleCalendarService.create_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return redirect(authorization_url)

@main.route('/calendar/oauth2callback')
@login_required
def oauth2callback():
    flow = GoogleCalendarService.create_flow()
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    # Create calendar service and sync events
    service = GoogleCalendarService.create_service(credentials)
    GoogleCalendarService.sync_events(service, current_user.id)
    
    flash('Calendar synchronized successfully!', 'success')
    return redirect(url_for('main.dashboard')) 

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.bio = request.form.get('bio')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
            
    return redirect(url_for('main.profile'))

@main.route('/profile/preferences', methods=['POST'])
@login_required
def update_preferences():
    if request.method == 'POST':
        current_user.default_view = 'kanban' if request.form.get('default_view') else 'list'
        current_user.email_notifications = bool(request.form.get('email_notifications'))
        current_user.theme = request.form.get('theme', 'light')
        current_user.default_priority = request.form.get('default_priority', 'medium')
        
        try:
            db.session.commit()
            flash('Preferences updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating preferences. Please try again.', 'error')
            
    return redirect(url_for('main.profile', _anchor='preferences'))

@main.route('/profile/notifications', methods=['POST'])
@login_required
def update_notifications():
    if request.method == 'POST':
        current_user.due_date_reminder = int(request.form.get('due_date_reminder', 1))
        current_user.project_updates = bool(request.form.get('project_updates'))
        current_user.task_assignments = bool(request.form.get('task_assignments'))
        
        try:
            db.session.commit()
            flash('Notification settings updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating notification settings. Please try again.', 'error')
            
    return redirect(url_for('main.profile', _anchor='notifications')) 

@main.route('/api/notifications')
def get_notifications():
    if not current_user.is_authenticated:
        return jsonify([])
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.timestamp.desc())\
        .limit(10)\
        .all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'type': n.notification_type,
        'timestamp': n.timestamp.isoformat(),
        'read': n.read
    } for n in notifications])

@main.route('/api/notifications/unread-count')
def get_unread_count():
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify({'count': count})

@main.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    notification.read = True
    db.session.commit()
    return jsonify({'status': 'success'})

@main.route('/api/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    Notification.query.filter_by(user_id=current_user.id, read=False)\
        .update({Notification.read: True})
    db.session.commit()
    return jsonify({'status': 'success'})

def create_notification(user_id, message, notification_type='default'):
    """Helper function to create and send notifications"""
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type
    )
    db.session.add(notification)
    db.session.commit()
    
    # Emit real-time notification via WebSocket
    socketio.emit('notification', {
        'id': notification.id,
        'message': notification.message,
        'type': notification.notification_type,
        'timestamp': notification.timestamp.isoformat(),
        'read': notification.read
    }, room=str(user_id))
    return notification

# Example: Create notification when a task is assigned
@main.route('/api/tasks/<int:task_id>/assign', methods=['POST'])
@login_required
def assign_task(task_id):
    task = Task.query.get_or_404(task_id)
    assignee_id = request.json.get('assignee_id')
    
    if assignee_id:
        task.assignee_id = assignee_id
        db.session.commit()
        
        # Create notification for the assignee
        create_notification(
            user_id=assignee_id,
            message=f"You have been assigned to task: {task.title}",
            notification_type='task'
        )
        
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Assignee ID is required'}), 400

# Example: Create notification when a project deadline is approaching
def check_project_deadlines():
    """Scheduled task to check project deadlines and send notifications"""
    from datetime import timedelta
    
    upcoming_projects = Project.query.filter(
        Project.deadline >= datetime.utcnow(),
        Project.deadline <= datetime.utcnow() + timedelta(days=3)
    ).all()
    
    for project in upcoming_projects:
        create_notification(
            user_id=project.owner_id,
            message=f"Project deadline approaching: {project.title}",
            notification_type='project'
        ) 

@main.route('/api/projects/deadlines')
@login_required
def get_project_deadlines():
    """Get all project deadlines for the calendar"""
    # Get projects where the user is either the owner or assigned to any task
    user_projects = Project.query.filter(
        db.or_(
            Project.owner_id == current_user.id,
            Project.id.in_(
                db.session.query(Task.project_id)
                .filter(Task.assignee_id == current_user.id)
                .distinct()
            )
        )
    ).all()
    
    projects_data = []
    for project in user_projects:
        if project.deadline:  # Only include projects with deadlines
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'deadline': project.deadline.isoformat(),
                'status': project.status
            })
    
    return jsonify(projects_data) 

@main.route('/calendar')
@login_required
def calendar_view():
    """Full calendar page view"""
    return render_template('calendar.html')

@main.route('/api/calendar/date/<date>')
@login_required
def get_date_details(date):
    """Get all events for a specific date"""
    try:
        # Parse the date string (format: YYYY-MM-DD)
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get projects due on this date
        projects = Project.query.filter(
            db.or_(
                Project.owner_id == current_user.id,
                Project.id.in_(
                    db.session.query(Task.project_id)
                    .filter(Task.assignee_id == current_user.id)
                    .distinct()
                )
            ),
            func.date(Project.deadline) == target_date
        ).all()
        
        # Get tasks due on this date
        tasks = Task.query.filter(
            Task.assignee_id == current_user.id,
            func.date(Task.due_date) == target_date
        ).all()
        
        # Format the response
        response = {
            'date': date,
            'projects': [{
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'status': project.status,
                'owner': User.query.get(project.owner_id).username,
                'deadline': project.deadline.strftime('%Y-%m-%d %H:%M'),
                'task_count': len(project.tasks)
            } for project in projects],
            'tasks': [{
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'project': {
                    'id': task.project.id,
                    'title': task.project.title
                }
            } for task in tasks]
        }
        
        return jsonify(response)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400 

def check_approaching_deadlines():
    """Check for approaching deadlines and send notifications"""
    today = datetime.utcnow()
    
    # Check project deadlines
    projects = Project.query.filter(
        Project.status != 'Completed',
        Project.deadline > today,
        Project.deadline <= today + timedelta(days=7)
    ).all()
    
    for project in projects:
        days_until = (project.deadline - today).days
        if days_until in [7, 3, 1]:  # Notify at 7 days, 3 days, and 1 day before deadline
            create_notification(
                project.owner_id,
                f"Project '{project.title}' deadline approaching in {days_until} day{'s' if days_until != 1 else ''}!",
                notification_type='deadline'
            )
    
    # Check task deadlines
    tasks = Task.query.filter(
        Task.status != 'Completed',
        Task.due_date > today,
        Task.due_date <= today + timedelta(days=7)
    ).all()
    
    for task in tasks:
        days_until = (task.due_date - today).days
        if days_until in [7, 3, 1]:  # Notify at 7 days, 3 days, and 1 day before deadline
            create_notification(
                task.assignee_id,
                f"Task '{task.title}' due in {days_until} day{'s' if days_until != 1 else ''}!",
                notification_type='deadline'
            )

@main.before_request
def before_request():
    """Run deadline checks before each request"""
    if current_user.is_authenticated:
        check_approaching_deadlines() 

@main.route('/profile/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Process and save the image
        image = Image.open(file)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to a maximum size while maintaining aspect ratio
        max_size = (500, 500)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Generate unique filename
        filename = secure_filename(f"avatar_{current_user.id}_{int(datetime.utcnow().timestamp())}.jpg")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the processed image
        image.save(filepath, 'JPEG', quality=85)
        
        # Update user's avatar URL
        avatar_url = url_for('static', filename=f'uploads/avatars/{filename}')
        current_user.avatar_url = avatar_url
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'avatar_url': avatar_url
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main.route('/profile/set-default-avatar', methods=['POST'])
@login_required
def set_default_avatar():
    data = request.get_json()
    avatar_url = data.get('avatar_url')
    
    if not avatar_url:
        return jsonify({'status': 'error', 'message': 'No avatar URL provided'}), 400
    
    try:
        current_user.avatar_url = avatar_url
        db.session.commit()
        return jsonify({'status': 'success', 'avatar_url': avatar_url})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main.route('/profile/remove-avatar', methods=['POST'])
@login_required
def remove_avatar():
    try:
        # If user has a custom avatar, delete the file
        if current_user.avatar_url and '/uploads/avatars/' in current_user.avatar_url:
            filepath = os.path.join(app.root_path, 'static', 
                                  current_user.avatar_url.split('/static/')[1])
            if os.path.exists(filepath):
                os.remove(filepath)
        
        # Reset to default avatar
        current_user.avatar_url = None
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500 