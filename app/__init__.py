import os
from flask import Flask
from app.extensions import db, bcrypt, login_manager, migrate
from app.models import User
from sqlalchemy import text



class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mysecret')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    EMP_IMGS = os.path.join('app', 'static', 'emp_imgs')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
        # Set a default session cookie name
    SESSION_COOKIE_NAME = 'employee'

class ProductionConfig(Config):
    # Specific production configurations
    pass

class DevelopmentConfig(Config):
    # Specific development configurations
    DEBUG = True
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)



    # Register Blueprints
    from app.routes import main  # Import here to avoid circular import
    app.register_blueprint(main)

    return app
@login_manager.user_loader
def load_user(user_id):
    from app.models import User  # Import inside function to avoid circular import
    return User.query.get(int(user_id))
