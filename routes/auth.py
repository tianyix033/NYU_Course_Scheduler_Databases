from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import execute_query, execute_query_single

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    try:
        if request.method == "GET":
            return render_template("register.html")

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        # Basic validation
        if not username or not password:
            flash("Please check your input. Username and password are required.", "error")
            return render_template("register.html", username=username)
        if password != confirm_password:
            flash("Please check your input. Passwords do not match.", "error")
            return render_template("register.html", username=username)

        # Check if username exists
        existing = execute_query_single("SELECT user_id FROM Users WHERE username = %s LIMIT 1", (username,))
        if existing:
            flash("Registration failed. Please check your input and try again.", "error")
            return render_template("register.html", username=username)

        # Hash password and insert user
        password_hash = generate_password_hash(password)
        row = execute_query_single(
            "INSERT INTO Users (username, password_hash) VALUES (%s, %s) RETURNING user_id",
            (username, password_hash),
        )
        user_id = row["user_id"] if row else None
        if not user_id:
            flash("Registration failed. Please check your input and try again.", "error")
            return render_template("register.html", username=username)

        # Log user in
        session["user_id"] = user_id
        session["username"] = username
        flash("Registration successful.", "success")
        return redirect(url_for("home.get_selected_course"))
    
    except Exception as e:
        # Log the full exception (e) for server-side debugging
        print(f"Server Error during registration: {e}") 
        flash("Registration failed. Please check your input and try again.", "error")
        return render_template("register.html", username=username)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "GET":
            return render_template("login.html")

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            flash("Please check your input. Username and password are required.", "error")
            return render_template("login.html", username=username)

        # Fetch stored password hash
        user = execute_query_single(
            "SELECT user_id, password_hash FROM Users WHERE username = %s LIMIT 1",
            (username,),
        )
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Login failed. Please check your username and password and try again.", "error")
            return render_template("login.html", username=username)

        # Set session
        session["user_id"] = user["user_id"]
        session["username"] = username
        flash("Logged in successfully.", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("home.get_selected_course"))
    except Exception as e:
        # Log the full exception (e) for server-side debugging
        print(f"Server Error during login: {e}") 
        flash("Login failed. Please check your input and try again.", "error")
        return render_template("login.html", username=username)


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home.get_selected_course"))


