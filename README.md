# StudyIt - Campus Study Buddy Finder

A location-based study buddy matching platform for college students, built with Django and Django Channels.

## Overview

StudyIt helps college students find study buddies in real-time based on their location on campus and the classes they're studying for. The platform enables students to:

- Find other students studying the same subject in nearby campus locations
- Chat and call with potential study partners
- Join or create study sessions hosted by TAs or other students
- View real-time availability of study buddies across campus

## Features

### Student Users
- Create personalized profiles with name, year, classes, and expertise level
- View other students in the same class by campus location
- Privacy controls for location visibility
- Real-time chat and call functionality
- Request to join TA-hosted study sessions
- Browse student profiles to find suitable study partners

### TA/Session Users
- Post and manage study sessions
- Specify session location, time, and subject
- Approve student requests to join sessions
- Track attendance and engagement

## Tech Stack

- **Backend:** Django 4.2.7
- **Real-time Communication:** Django Channels (WebSockets)
- **Database:** SQLite3
- **ASGI Server:** Daphne/Uvicorn
- **API:** Django REST Framework

## Campus Locations (Georgia Tech)

The MVP includes the following Georgia Tech campus locations:
- Student Center
- Library (Crosland Tower, Price Gilbert)
- Instructional Center
- College of Computing
- Klaus Advanced Computing Building
- Other key study areas

## Project Structure

```
studyIt/
├── studyit_project/          # Main Django project
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/                  # User authentication and profiles
├── locations/                 # Campus location management
├── study_sessions/            # Study session management
├── chat/                      # Real-time chat and messaging
├── static/                    # Static files (CSS, JS, images)
├── media/                     # User-uploaded content
├── templates/                 # HTML templates
├── requirements.txt
└── manage.py
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd studyIt
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Access the application at `http://localhost:8000`

### Running with Channels (WebSocket Support)

For real-time features (chat, live updates):

```bash
daphne -p 8000 studyit_project.asgi:application
```

## Development

### Creating Migrations

After modifying models:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Running Tests

```bash
pytest
```

## User Stories

See [Team-1-documentation.md](Team-1-documentation.md) for detailed user stories and requirements.

## Contributing

This is a course project for CS2340 at Georgia Tech.

## License

Educational use only - CS2340 Project

## Team

Team 1 - CS2340

---

For questions or issues, please contact the development team.

