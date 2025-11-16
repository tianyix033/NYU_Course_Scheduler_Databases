from flask import Flask
from config import Config
from flask import render_template, session
from auth_utils import login_required

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/")
    @login_required # include this on routes that require authentication
    def index():
        username = session.get("username")
        return render_template("index.html", username=username)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True) # default to port 5000


