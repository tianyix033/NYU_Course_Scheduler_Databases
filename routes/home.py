from flask import render_template, Blueprint, session, request, redirect
from database import call_procedure, execute_query
from auth_utils import login_required

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
@login_required
def get_selected_course():
    user_id = session["user_id"]
    print(user_id)
   
   #courseID and instructor ID selected too for delete purpose
    query = ("SELECT c.title, c.course_id, i.instructor_id, i.first_name, i.last_name " 
    "FROM User_Selection AS u "
    "INNER JOIN Course AS c "
    "ON c.course_id = u.course_id "
    "INNER JOIN INSTRUCTOR AS i "
    "ON i.instructor_id = u.instructor_id "
    "WHERE u.user_id = %s")
    
    selected_courses = execute_query(query, (user_id,), fetch = True)
    print(selected_courses)
    username = session.get("username") 
    return render_template("index.html", selected_courses=selected_courses, username = username)
    
@home_bp.route("/delete", methods=["POST"])
@login_required
def delete_item():
    user_id = session["user_id"]
    course_id = request.form["course_id"]
    instructor_id = request.form["instructor_id"]
    call_procedure("RemoveUserSelection", (user_id, course_id, instructor_id), False)
    return redirect("/")