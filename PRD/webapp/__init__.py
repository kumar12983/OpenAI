"""
School Catchment Search Web Application Package
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from flask import Flask

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object('config.settings')
    
    # Register blueprints and extensions here
    return app
