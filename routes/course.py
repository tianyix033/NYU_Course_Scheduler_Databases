from flask import render_template, Blueprint, request, session
from database import call_function, call_procedure
from collections import OrderedDict
from urllib.parse import urlencode
from auth_utils import login_required

course_bp = Blueprint("course", __name__, url_prefix="/course")

@course_bp.route("/")
@login_required
def get_search_course():
    course_id = request.args.get("input_course_id", "")
    course_title = request.args.get("input_course_title", "")
    instructor_name = request.args.get("input_instructor_name", "")
    courses = call_function("SearchCourse",(course_id, course_title, instructor_name))
    courses_for_template = group_courses(courses)
    return render_template("course.html", courses= courses_for_template)


def group_courses(courses):
    grouped_courses = OrderedDict()  # maintain order from query

    for row in courses:
        course_id = row['course_id']
        instructor_id = row['instructor_id']
        section_key = row['section_type'] + str(row['start_time'])  # unique key for section
        
        # add course if not exists
        if course_id not in grouped_courses:
            grouped_courses[course_id] = {
                'course_id': course_id,
                'title': row['title'],
                'credits': row['credits'],
                'course_description': row['course_description'],
                'prerequisites': row['prerequisites'],
                'instructors': OrderedDict()
            }

        course = grouped_courses[course_id]

        # add instructor if not exists
        if instructor_id not in course['instructors']:
            course['instructors'][instructor_id] = {
                'instructor_id': instructor_id,
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'sections': OrderedDict()
            }

        instructor = course['instructors'][instructor_id]

        # add section if not exists
        if section_key not in instructor['sections']:
            instructor['sections'][section_key] = {
                'section_type': row['section_type'],
                'campus': row['campus'],
                'day_of_week': row['day_of_week'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'meeting_location': row['meeting_location']
            }

    # convert OrderedDicts to lists for Jinja
    result = []
    for course in grouped_courses.values():
        course['instructors'] = list(course['instructors'].values())
        for instructor in course['instructors']:
            instructor['sections'] = list(instructor['sections'].values())
        result.append(course)

    return result
 
# the added render do not alway exist, unless you use sessionto store the status
@course_bp.route("/add", methods=["POST"])
@login_required
def add_course():
    user_id = session["user_id"]
    data = request.get_json()
    course_id = data["course_id"]
    instructor_id = data["instructor_id"]
    call_procedure("AddUserSelection", (user_id, course_id, instructor_id), False)
    return {"status": "ok"}

