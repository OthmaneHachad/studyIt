# PythonAnywhere Deployment Guide

## Initial Setup Steps

### 1. Run Database Migrations
This is **critical** - you must run migrations to create all database tables:

```bash
cd /home/ykharrat/studyIt
python3.10 manage.py migrate
```

This will create all necessary tables including:
- `django_session` (for user sessions)
- `auth_user` (for user accounts)
- All your app tables (accounts, chat, locations, etc.)

### 2. Create a Superuser (Optional but Recommended)
To access the Django admin panel:

```bash
python3.10 manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 3. Collect Static Files
If you're serving static files through Django:

```bash
python3.10 manage.py collectstatic --noinput
```

### 4. Verify Database File Location
Make sure the `db.sqlite3` file is in the correct location:
- The database path in `settings.py` is: `BASE_DIR / "db.sqlite3"`
- This should be at: `/home/ykharrat/studyIt/db.sqlite3`

### 5. Check File Permissions
Ensure Django can read/write the database file:

```bash
chmod 664 /home/ykharrat/studyIt/db.sqlite3
```

## Common Issues

### Issue: "no such table: django_session"
**Solution:** Run `python3.10 manage.py migrate`

### Issue: Database locked errors
**Solution:** Make sure only one process is accessing the database at a time. Restart your web app.

### Issue: Static files not loading
**Solution:** 
1. Run `python3.10 manage.py collectstatic`
2. Check your static files configuration in the PythonAnywhere web app settings

## Web App Configuration

### WSGI Configuration
For PythonAnywhere, you typically use WSGI (not ASGI) unless you specifically need WebSocket support.

If you need WebSocket support, you'll need to:
1. Use ASGI with Daphne
2. Configure a separate WebSocket server
3. Or use a different hosting platform that supports WebSockets better (like Render)

For basic HTTP requests, use WSGI:
- Point to: `studyit_project.wsgi.application`

### Environment Variables
Set these in your PythonAnywhere web app configuration:
- `SECRET_KEY` (if you want to override the default)
- `DEBUG=False` (for production)
- `ALLOWED_HOSTS` (set to your PythonAnywhere domain)

## Quick Fix for Current Error

Run these commands in your PythonAnywhere Bash console:

```bash
cd /home/ykharrat/studyIt
python3.10 manage.py migrate
python3.10 manage.py collectstatic --noinput
```

Then reload your web app from the PythonAnywhere dashboard.



