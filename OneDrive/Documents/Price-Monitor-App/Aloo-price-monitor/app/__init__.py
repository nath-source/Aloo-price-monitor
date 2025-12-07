from flask import Flask
from .extensions import db, login_manager
from .models import User
from .celery_utils import celery_init_app # <--- Import this

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'dev-key-for-now'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CELERY CONFIGURATION (Redis Connection)
    # ... inside create_app() ...

    from celery.schedules import crontab # Import crontab

    # CELERY CONFIGURATION
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/0",
            task_ignore_result=True,
            # ADD THIS SECTION:
            beat_schedule={
                "update-all-products-every-5-minutes": {
                    "task": "app.tasks.update_all_products_task",
                    # Run every 5 minutes. 
                    # For testing now, let's do every 1 minute: schedule=60.0
                    "schedule": 60.0, 
                },
            },
        ),
    )
    
    
    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    celery_init_app(app) # <--- Initialize Celery here

    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

    from . import tasks

    return app