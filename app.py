from flask import Flask
from config import Config
from flask import render_template, session
from auth_utils import login_required

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints

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

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True) # default to port 5000


