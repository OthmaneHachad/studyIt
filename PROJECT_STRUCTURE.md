# StudyIt - Project Structure Outline

## Overview
This document outlines the complete structure and organization of the StudyIt application, showing what functionality belongs in which Django app and how components interact.

---

## 📁 Project Structure

```
studyIt/
├── studyit_project/          # Main Django project configuration
│   ├── settings.py           # Django settings, middleware, apps configuration
│   ├── urls.py               # Main URL routing (includes app URLs)
│   ├── asgi.py               # ASGI config for WebSocket support (Channels)
│   └── wsgi.py               # WSGI config for HTTP requests
│
├── accounts/                 # User Authentication & Profiles
│   ├── models.py             # StudentProfile, TAProfile models
│   ├── views.py              # Login, Signup, Logout, Profile views
│   ├── forms.py              # User registration, profile edit forms
│   ├── urls.py               # /accounts/* URL routing
│   ├── admin.py              # Admin interface for user profiles
│   └── templates/accounts/   # Login, signup, profile templates
│
├── locations/                 # Campus Location Management
│   ├── models.py             # Location model (Student Center, Library, etc.)
│   ├── views.py              # Location list, detail views
│   ├── urls.py               # /locations/* URL routing
│   ├── admin.py              # Admin interface for locations
│   └── management/commands/  # Commands to populate initial locations
│
├── study_sessions/           # Study Session Management
│   ├── models.py             # StudySession, SessionRequest models
│   ├── views.py              # Create, list, detail, approve/reject sessions
│   ├── forms.py              # Session creation/edit forms
│   ├── urls.py               # /sessions/* URL routing
│   ├── admin.py              # Admin interface for sessions
│   └── templates/study_sessions/  # Session templates
│
├── chat/                     # Real-time Chat & Messaging
│   ├── models.py             # ChatRoom, Message models
│   ├── views.py              # Chat room list, chat interface views
│   ├── consumers.py          # WebSocket consumers (already implemented)
│   ├── routing.py            # WebSocket URL routing (already implemented)
│   ├── urls.py               # /chat/* URL routing
│   └── templates/chat/       # Chat interface templates
│
├── templates/                # Base templates
│   ├── base.html             # Base template with nav/footer
│   └── home.html             # Landing page
│
├── static/                   # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│
└── media/                    # User-uploaded files (if needed)
```

---

## 🔐 Accounts App (`accounts/`)

### Purpose
Handle user authentication, registration, and profile management.

### Models (`accounts/models.py`)
- **StudentProfile**
  - OneToOneField to User
  - Fields: name, year (Freshman/Sophomore/Junior/Senior/Graduate), classes (ManyToMany to Class model), expertise_level (Beginner/Intermediate/Advanced), location_privacy (Boolean), current_location (ForeignKey to Location), is_active (Boolean), created_at, updated_at
  
- **TAProfile**
  - OneToOneField to User
  - Fields: name, department, classes_teaching (ManyToMany to Class model), is_active, created_at, updated_at

- **Class** (optional helper model)
  - Fields: code (e.g., "CS2340"), name, department

### Views (`accounts/views.py`)
- `login_view()` - User login
- `signup_view()` - User registration (with user type selection)
- `logout_view()` - User logout
- `profile_view()` - View own profile
- `profile_edit()` - Edit own profile
- `profile_detail()` - View other user's profile
- `profile_list()` - Browse all student profiles

### URLs (`accounts/urls.py`)
- `/accounts/login/` - Login page
- `/accounts/signup/` - Registration page
- `/accounts/logout/` - Logout (redirects)
- `/accounts/profile/` - Own profile
- `/accounts/profile/edit/` - Edit profile
- `/accounts/profile/<user_id>/` - View other profile
- `/accounts/browse/` - Browse profiles

### Forms (`accounts/forms.py`)
- `UserRegistrationForm` - Create new user account
- `StudentProfileForm` - Create/edit student profile
- `TAProfileForm` - Create/edit TA profile

### Templates (`templates/accounts/`)
- `login.html` - Login form
- `signup.html` - Registration form with user type selection
- `profile.html` - Profile detail view
- `profile_edit.html` - Profile editing form
- `profile_list.html` - Browse profiles page

---

## 📍 Locations App (`locations/`)

### Purpose
Manage campus locations where students can study.

### Models (`locations/models.py`)
- **Location**
  - Fields: name (e.g., "Student Center"), building_name, description, is_active, created_at

### Views (`locations/views.py`)
- `location_list()` - List all active locations
- `location_detail()` - Location detail view
- `update_location()` - Student updates their current location

### URLs (`locations/urls.py`)
- `/locations/` - List all locations
- `/locations/<id>/` - Location detail
- `/locations/update/` - Update user's current location (AJAX)

### Management Commands (`locations/management/commands/`)
- `create_locations.py` - Populate initial campus locations

### Initial Locations (Georgia Tech)
- Student Center
- Library (Crosland Tower)
- Library (Price Gilbert)
- Instructional Center
- College of Computing
- Klaus Advanced Computing Building

---

## 📚 Study Sessions App (`study_sessions/`)

### Purpose
Manage TA-hosted and student-hosted study sessions.

### Models (`study_sessions/models.py`)
- **StudySession**
  - Fields: host (ForeignKey to User), title, description, location (ForeignKey to Location), class_subject (ForeignKey to Class), start_time, end_time, max_participants, current_participants (count), is_active, created_at, updated_at
  
- **SessionRequest**
  - Fields: session (ForeignKey to StudySession), student (ForeignKey to User), status (pending/approved/rejected), message (TextField), requested_at, reviewed_at

### Views (`study_sessions/views.py`)
- `session_list()` - List all upcoming sessions (filterable)
- `session_detail()` - Session detail view
- `session_create()` - Create new session (TA/Student)
- `session_edit()` - Edit own session
- `session_delete()` - Cancel session
- `request_join()` - Student requests to join session
- `approve_request()` - TA approves student request
- `reject_request()` - TA rejects student request
- `my_sessions()` - View sessions user is hosting/attending

### URLs (`study_sessions/urls.py`)
- `/sessions/` - List all sessions
- `/sessions/create/` - Create session
- `/sessions/<id>/` - Session detail
- `/sessions/<id>/edit/` - Edit session
- `/sessions/<id>/request/` - Request to join
- `/sessions/<id>/approve/<request_id>/` - Approve request
- `/sessions/<id>/reject/<request_id>/` - Reject request
- `/sessions/my/` - My sessions

### Forms (`study_sessions/forms.py`)
- `StudySessionForm` - Create/edit study session

### Templates (`templates/study_sessions/`)
- `session_list.html` - Browse sessions
- `session_detail.html` - Session details with request form
- `session_form.html` - Create/edit session
- `my_sessions.html` - User's sessions dashboard

---

## 💬 Chat App (`chat/`)

### Purpose
Real-time messaging between students.

### Models (`chat/models.py`)
- **ChatRoom**
  - Fields: room_name (unique), participants (ManyToMany to User), created_at, room_type (direct/group)
  
- **Message**
  - Fields: room (ForeignKey to ChatRoom), sender (ForeignKey to User), content (TextField), timestamp, is_read (Boolean)

### Views (`chat/views.py`)
- `chat_list()` - List user's chat rooms
- `chat_room()` - Chat interface (renders template with WebSocket connection)
- `create_chat()` - Create new chat room with another user

### URLs (`chat/urls.py`)
- `/chat/` - List chat rooms
- `/chat/<room_name>/` - Chat room interface
- `/chat/create/<user_id>/` - Create chat with user

### WebSocket (`chat/consumers.py` & `routing.py`)
- Already implemented: `ChatConsumer` for WebSocket connections
- WebSocket URL: `ws/chat/<room_name>/`

### Templates (`templates/chat/`)
- `chat_list.html` - List of chat rooms
- `chat_room.html` - Chat interface with WebSocket client

---

## 🔍 Matching & Discovery Logic

### Location-Based Matching
**Location:** `accounts/views.py` or new `matching/` app

- `find_students_by_location()` - Find students in same location
- `find_students_by_class()` - Find students in same class
- `find_students_by_location_and_class()` - Combined filter
- Privacy-aware: Only show students who have `location_privacy=False`

### Student Discovery
**Location:** `accounts/views.py`

- `browse_students()` - Browse all students with filters
- Filters: class, year, expertise_level, location, active status

---

## 🔗 Cross-App Relationships

### User Flow
1. **Registration** (`accounts/`) → Creates User + StudentProfile/TAProfile
2. **Location Selection** (`locations/`) → Updates StudentProfile.current_location
3. **Finding Students** (`accounts/`) → Queries StudentProfile by location/class
4. **Chat Initiation** (`chat/`) → Creates ChatRoom between matched students
5. **Session Discovery** (`study_sessions/`) → Browse sessions, request to join

### Key Relationships
- `StudentProfile.current_location` → `Location`
- `StudySession.location` → `Location`
- `StudySession.host` → `User` (can be TA or Student)
- `SessionRequest.session` → `StudySession`
- `SessionRequest.student` → `User`
- `ChatRoom.participants` → `User` (ManyToMany)
- `Message.room` → `ChatRoom`
- `Message.sender` → `User`

---

## 🎨 UI/UX Structure

### Templates Hierarchy
```
templates/
├── base.html                    # Base layout (nav, footer)
│   ├── home.html                # Landing page
│   ├── accounts/
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── profile.html
│   │   └── profile_list.html
│   ├── locations/
│   │   ├── location_list.html
│   │   └── location_detail.html
│   ├── study_sessions/
│   │   ├── session_list.html
│   │   ├── session_detail.html
│   │   └── session_form.html
│   └── chat/
│       ├── chat_list.html
│       └── chat_room.html
```

### Static Files
- `static/css/style.css` - Main stylesheet
- `static/js/main.js` - Common JavaScript
- `static/js/chat.js` - WebSocket client for chat
- `static/images/` - Images, logos

---

## 🔐 Authentication & Authorization

### Login Required Decorators
- Most views require `@login_required`
- Profile editing: Only own profile
- Session management: Only host can edit/delete
- Session approval: Only session host can approve/reject

### User Types
- **Student**: Can create study sessions, request to join sessions, chat
- **TA**: Can create study sessions, approve/reject requests, chat

---

## 📊 Database Schema Summary

```
User (Django built-in)
├── StudentProfile (OneToOne)
│   ├── classes (ManyToMany → Class)
│   └── current_location (ForeignKey → Location)
├── TAProfile (OneToOne)
│   └── classes_teaching (ManyToMany → Class)

Location
└── StudySession.location (ForeignKey)

StudySession
├── host (ForeignKey → User)
├── location (ForeignKey → Location)
├── class_subject (ForeignKey → Class)
└── SessionRequest.session (ForeignKey)

ChatRoom
├── participants (ManyToMany → User)
└── Message.room (ForeignKey)

Message
├── room (ForeignKey → ChatRoom)
└── sender (ForeignKey → User)
```

---

## 🚀 Implementation Priority

1. **Phase 1**: Accounts (Auth + Profiles) + Locations
2. **Phase 2**: Study Sessions (CRUD + Requests)
3. **Phase 3**: Chat (Models + Views + WebSocket integration)
4. **Phase 4**: Matching Logic (Location-based discovery)
5. **Phase 5**: UI Polish & Testing

---

## 📝 Notes

- All models should have `created_at` and `updated_at` timestamps
- Use Django's built-in User model (no custom user model needed)
- Privacy: `location_privacy=True` means location is hidden from others
- Sessions can be created by both Students and TAs
- Chat rooms are automatically created when students initiate conversation
- WebSocket chat is already implemented in `chat/consumers.py`

