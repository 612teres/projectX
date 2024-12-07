# Project Management Dashboard

A modern web-based project management dashboard built with Flask, SQLAlchemy, and Google Calendar integration. This application helps web developers organize, track, and update their tasks efficiently.

## Features

- Project creation and management
- Task tracking with priorities and deadlines
- Google Calendar integration for events and meetings
- Modern, responsive UI built with Tailwind CSS
- Real-time task status updates
- Project deadline tracking
- Priority-based task organization

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Cloud Platform account (for Calendar API)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd project-management-dashboard
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///project.db
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

5. Set up Google Calendar API:
- Go to the Google Cloud Console
- Create a new project
- Enable the Google Calendar API
- Create OAuth 2.0 credentials
- Download the client configuration file and save it as `client_secrets.json` in the root directory

## Running the Application

1. Initialize the database:
```bash
flask db upgrade
```

2. Run the development server:
```bash
flask run
```

3. Access the application at `http://localhost:5000`

## Usage

1. Register a new account or log in
2. Create projects and set their deadlines
3. Add tasks to projects and assign priorities
4. Update task status in real-time
5. Connect your Google Calendar to sync events
6. Track project progress and deadlines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 