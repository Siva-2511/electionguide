"""
wsgi.py — Production WSGI entry point for Render.com / gunicorn.
Usage: gunicorn wsgi:application
"""

from app import app as application

if __name__ == "__main__":
    application.run()
