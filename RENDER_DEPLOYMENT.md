# Render Deployment Guide

## Environment Variables

Set these in your Render dashboard under "Environment":

1. **SECRET_KEY**: Generate a new secret key for production
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **DEBUG**: Set to `False` for production

3. **ALLOWED_HOSTS**: Set to your Render domain (e.g., `studyit.onrender.com`)

4. **REDIS_URL** (Optional): If you add a Redis instance for Channels, set this to the Redis connection URL

## Start Command

For Render, use this as your **Start Command**:

```bash
daphne -b 0.0.0.0 -p $PORT studyit_project.asgi:application
```

Or if you prefer using uvicorn:

```bash
uvicorn studyit_project.asgi:application --host 0.0.0.0 --port $PORT
```

## Build Command

The `build.sh` script will automatically:
- Install dependencies
- Run migrations
- Collect static files

## Notes

- Python version is specified in `runtime.txt` (Python 3.11.9)
- Static files are collected to `staticfiles/` directory
- For WebSocket support, consider adding a Redis instance for production (optional but recommended)

