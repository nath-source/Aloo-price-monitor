import os
import ssl # Required for secure Upstash connection
from flask import Flask
from .extensions import db, login_manager
from .models import User
from .celery_utils import celery_init_app 

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-now')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Get Redis URL from Environment (Render) or default to local
    redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

    # SSL configuration for secure Upstash connection (rediss://)
    if redis_url.startswith("rediss://"):
        ssl_options = {"ssl_cert_reqs": ssl.CERT_NONE}
    else:
        ssl_options = None

    # CELERY CONFIGURATION
    app.config.from_mapping(
        CELERY=dict(
            broker_url=redis_url,
            result_backend=redis_url,
            task_ignore_result=True,
            # Critical for Upstash security
            broker_use_ssl=ssl_options,
            redis_backend_use_ssl=ssl_options,
            beat_schedule={
                "update-all-products-every-5-minutes": {
                    "task": "app.tasks.update_all_products_task",
                    "schedule": 300.0, # 5 minutes for production
                },
            },
        ),
    )
    
    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    celery_init_app(app) 

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

    # Force task registration
    from . import tasks

    return app