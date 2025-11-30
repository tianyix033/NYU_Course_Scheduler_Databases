from flask import Flask
from config import Config
import logging

logger = logging.getLogger(__name__)

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    try:
        from routes.home import home_bp
        app.register_blueprint(home_bp)
        
        from routes.auth import auth_bp
        app.register_blueprint(auth_bp)
        
        from routes.course import course_bp
        app.register_blueprint(course_bp)
        
        from routes.review import review_bp
        app.register_blueprint(review_bp)

        from routes.schedule import schedule_bp
        app.register_blueprint(schedule_bp)
    except Exception as e:
        logger.error(f"Error registering blueprints: {e}")
        raise

    return app

# Create app instance for Heroku/gunicorn
try:
    app = create_app()
except Exception as e:
    logger.error(f"Failed to create app: {e}")
    raise

if __name__ == "__main__":
    app.run(debug=True) # default to port 5000


