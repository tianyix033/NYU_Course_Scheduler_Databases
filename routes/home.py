from collections import OrderedDict

from flask import render_template, Blueprint, session, request, redirect
from database import call_procedure, execute_query
from auth_utils import login_required
from utils.meeting_utils import format_time_range, get_day_label

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
@login_required
def get_selected_course():
    user_id = session["user_id"]

    query = """
    SELECT
        c.title,
        c.course_id,
        i.instructor_id,
        i.first_name,
        i.last_name,
        s.section_id,
        s.section_type,
        s.campus,
        mt.day_of_week,
        mt.start_time,
        mt.end_time,
        mt.meeting_location
    FROM User_Selection u
    INNER JOIN Course c ON c.course_id = u.course_id
    INNER JOIN Instructor i ON i.instructor_id = u.instructor_id
    LEFT JOIN Section s ON s.course_id = u.course_id AND s.instructor_id = u.instructor_id
    LEFT JOIN Meeting_Time mt ON mt.section_id = s.section_id
    WHERE u.user_id = %s
    ORDER BY
        c.course_id,
        i.last_name,
        i.first_name,
        s.section_type,
        s.section_id,
        mt.day_of_week NULLS LAST,
        mt.start_time NULLS LAST;
    """

    rows = execute_query(query, (user_id,), fetch=True)

    grouped = OrderedDict()
    for row in rows:
        key = (row["course_id"], row["instructor_id"])
        entry = grouped.setdefault(
            key,
            {
                "course_id": row["course_id"],
                "title": row["title"],
                "instructor_id": row["instructor_id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "sections_by_id": OrderedDict(),
            },
        )

        section_id = row["section_id"]
        section = entry["sections_by_id"].setdefault(
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

    selected_courses = []
    for entry in grouped.values():
        sections = []
        for section in entry["sections_by_id"].values():
            sections.append(
                {
                    "section_type": section["section_type"],
                    "campus": section["campus"],
                    "meetings": section["meetings"],
                }
            )

        selected_courses.append(
            {
                "course_id": entry["course_id"],
                "title": entry["title"],
                "instructor_id": entry["instructor_id"],
                "first_name": entry["first_name"],
                "last_name": entry["last_name"],
                "sections": sections,
            }
        )

    username = session.get("username")
    return render_template("index.html", selected_courses=selected_courses, username=username)

@home_bp.route("/delete", methods=["POST"])
@login_required
def delete_item():
    user_id = session["user_id"]
    course_id = request.form["course_id"]
    instructor_id = request.form["instructor_id"]
    call_procedure("RemoveUserSelection", (user_id, course_id, instructor_id), False)
    return redirect("/")