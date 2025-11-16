from functools import wraps
from flask import session, redirect, url_for, request, flash

def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            next_url = request.path
            return redirect(url_for("auth.login", next=next_url))
        return view_func(*args, **kwargs)
    return wrapped_view


