from flask import render_template, Blueprint, request, session, flash
from database import call_function, call_procedure, execute_query
from collections import OrderedDict
from urllib.parse import urlencode
from auth_utils import login_required
from utils.meeting_utils import format_time_range, get_day_label

COURSE_SEARCH_QUERY = """
SELECT
    c.course_id,
    i.instructor_id,
    s.section_id,
    c.title,
    c.credits,
    c.course_description,
    c.prerequisites,
    s.section_type,
    s.campus,
    m.day_of_week,
    m.start_time,
    m.end_time,
    m.meeting_location,
    i.first_name,
    i.last_name
FROM Course c
INNER JOIN Section s ON c.course_id = s.course_id
INNER JOIN Instructor i ON s.instructor_id = i.instructor_id
INNER JOIN Meeting_Time m ON s.section_id = m.section_id
WHERE (%(course_id)s IS NULL OR %(course_id)s = '' OR LOWER(c.course_id) LIKE '%%' || LOWER(%(course_id)s) || '%%')
    AND (%(course_title)s IS NULL OR %(course_title)s = '' OR LOWER(c.title) LIKE '%%' || LOWER(%(course_title)s) || '%%')
    AND (%(instructor_name)s IS NULL OR %(instructor_name)s = '' OR LOWER(i.first_name || ' ' || i.last_name) LIKE '%%' || LOWER(%(instructor_name)s) || '%%')
ORDER BY c.course_id, i.instructor_id, s.section_id, m.day_of_week;
"""

course_bp = Blueprint("course", __name__, url_prefix="/course")

@course_bp.route("/")
@login_required
def get_search_course():
    try:
        course_id = request.args.get("input_course_id", "")
        course_title = request.args.get("input_course_title", "")
        instructor_name = request.args.get("input_instructor_name", "")
        courses = execute_query(
            COURSE_SEARCH_QUERY,
            {
                "course_id": course_id,
                "course_title": course_title,
                "instructor_name": instructor_name,
            },
            fetch=True,
        )
        courses_for_template = group_courses(courses)
        
        # Get user's existing selections
        user_id = session["user_id"]
        user_selections = execute_query(
            "SELECT course_id, instructor_id FROM User_Selection WHERE user_id = %s",
            (user_id,),
            fetch=True
        )
        
        # Create a set of (course_id, instructor_id) tuples for quick lookup
        selected_set = {(row['course_id'], row['instructor_id']) for row in user_selections}
        
        # Mark which courses/instructors are already selected
        for course in courses_for_template:
            for instructor in course['instructors']:
                key = (course['course_id'], instructor['instructor_id'])
                instructor['is_selected'] = key in selected_set
        
        return render_template("course.html", courses=courses_for_template)
    except Exception as e:
        # Log the full exception (e) for server-side debugging
        print(f"Server Error during course search: {e}") 
        flash("An unexpected server error occurred. Please try again later.", "error")
        return render_template("course.html", courses=[])


def group_courses(courses):
    grouped_courses = OrderedDict()

    for row in courses:
        course_id = row["course_id"]
        instructor_id = row["instructor_id"]
        section_id = row["section_id"]

        if course_id not in grouped_courses:
            grouped_courses[course_id] = {
                "course_id": course_id,
                "title": row["title"],
                "credits": row["credits"],
                "course_description": row["course_description"],
                "prerequisites": row["prerequisites"],
                "instructors": OrderedDict(),
            }

        course = grouped_courses[course_id]

        if instructor_id not in course["instructors"]:
            course["instructors"][instructor_id] = {
                "instructor_id": instructor_id,
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "sections": OrderedDict(),
            }

        instructor = course["instructors"][instructor_id]

        section = instructor["sections"].setdefault(
            section_id,
            {
                "section_id": section_id,
                "section_type": row["section_type"],
                "campus": row["campus"],
                "meetings": [],
                "meeting_signatures": set(),
            },
        )

        meeting_location = row["meeting_location"] or row["campus"] or "TBA"
        meeting_key = (
            row["day_of_week"],
            row["start_time"],
            row["end_time"],
            meeting_location,
        )

        if meeting_key in section["meeting_signatures"]:
            continue

        section["meeting_signatures"].add(meeting_key)
        section["meetings"].append(
            {
                "day_of_week": row["day_of_week"],
                "day_label": get_day_label(row["day_of_week"]),
                "time_range": format_time_range(row["start_time"], row["end_time"]),
                "location": meeting_location,
            }
        )

    result = []
    for course in grouped_courses.values():
        course["instructors"] = list(course["instructors"].values())
        for instructor in course["instructors"]:
            instructor["sections"] = list(instructor["sections"].values())
        result.append(course)

    return result
 
# the added render do not alway exist, unless you use sessionto store the status
@course_bp.route("/add", methods=["POST"])
@login_required
def add_course():
    try:
        user_id = session["user_id"]
        data = request.get_json()
        course_id = data["course_id"]
        instructor_id = data["instructor_id"]
        call_procedure("AddUserSelection", (user_id, course_id, instructor_id), False)
        return {"status": "ok"}
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error adding course selection: {e}")
        flash("We could not remove the course selection due to a server error. Please try again.", "error")
        return render_template("course.html", courses=[])

