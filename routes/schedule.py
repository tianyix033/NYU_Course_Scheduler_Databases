from collections import OrderedDict
from datetime import time as datetime_time
from itertools import product

from flask import Blueprint, render_template, session

from auth_utils import login_required
from database import execute_query
from utils.meeting_utils import get_day_label

schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")

MAX_SCHEDULES_DISPLAY = 6
MAX_COURSE_DISPLAY = 8
FAR_FUTURE_TIME = datetime_time(hour=23, minute=59)

DAY_COLUMNS = [
    {"key": "M", "label": "Mon"},
    {"key": "T", "label": "Tue"},
    {"key": "W", "label": "Wed"},
    {"key": "TR", "label": "Thu"},
    {"key": "F", "label": "Fri"},
]
SECTION_TYPE_ORDER = ["Lecture", "Lab"]

SCHEDULE_QUERY = """
SELECT
    us.course_id,
    c.title AS course_title,
    us.instructor_id,
    i.first_name,
    i.last_name,
    s.section_id,
    s.section_type,
    s.campus,
    mt.day_of_week,
    mt.start_time,
    mt.end_time,
    mt.meeting_location
FROM User_Selection us
JOIN Course c ON c.course_id = us.course_id
JOIN Instructor i ON i.instructor_id = us.instructor_id
JOIN Section s ON s.course_id = us.course_id AND s.instructor_id = us.instructor_id
LEFT JOIN Meeting_Time mt ON mt.section_id = s.section_id
WHERE us.user_id = %s
ORDER BY c.course_id, i.last_name, i.first_name, s.section_type, s.section_id, mt.day_of_week NULLS LAST, mt.start_time NULLS LAST;
"""


@schedule_bp.route("/")
@login_required
def view_schedule():
    user_id = session["user_id"]
    rows = execute_query(SCHEDULE_QUERY, (user_id,), fetch=True)

    unique_courses = {row["course_id"] for row in rows}
    schedule_options = []
    stats_message = None
    status_message = None
    status_category = "info"
    limit_reached = False

    if not rows:
        status_message = "Add a few courses to your selections before generating a schedule."
        status_category = "info"
    elif len(unique_courses) > MAX_COURSE_DISPLAY:
        status_message = (
            f"You selected {len(unique_courses)} courses. The visual schedule only supports "
            f"up to {MAX_COURSE_DISPLAY} courses at a time."
        )
        status_category = "error"
    else:
        course_map = build_course_map(rows)
        course_groups = build_course_groups(course_map)

        if not course_groups:
            status_message = "We could not build any schedule variants for the selected courses."
            status_category = "error"
        else:
            combos, limit_reached = build_schedule_options(course_groups)
            if not combos:
                status_message = (
                    "No conflict-free schedule combinations could be generated. "
                    "Try different instructors or remove overlapping selections."
                )
                status_category = "error"
            else:
                schedule_options = [
                    {
                        "id": idx + 1,
                        "mapping": combo,
                        "events_by_day": build_events_by_day(combo),
                    }
                    for idx, combo in enumerate(combos)
                ]
                stats_message = (
                    f"Showing {len(schedule_options)} conflict-free option"
                    f"{'s' if len(schedule_options) != 1 else ''} (limited to {MAX_SCHEDULES_DISPLAY})."
                )

    return render_template(
        "schedule.html",
        day_columns=DAY_COLUMNS,
        schedule_options=schedule_options,
        stats_message=stats_message,
        status_message=status_message,
        status_category=status_category,
        limit_reached=limit_reached,
        max_schedules=MAX_SCHEDULES_DISPLAY,
        unique_course_count=len(unique_courses),
        max_course_limit=MAX_COURSE_DISPLAY,
    )


def build_course_map(rows):
    courses = OrderedDict()
    for row in rows:
        course_id = row["course_id"]
        course = courses.setdefault(
            course_id,
            {
                "course_id": course_id,
                "title": row["course_title"],
                "instructors": OrderedDict(),
            },
        )

        instructor_id = row["instructor_id"]
        instructor = course["instructors"].setdefault(
            instructor_id,
            {
                "instructor_id": instructor_id,
                "name": f"{row['first_name']} {row['last_name']}",
                "sections": OrderedDict(),
            },
        )

        section_id = row["section_id"]
        if section_id is None:
            continue

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

        meeting_key = (
            row["day_of_week"],
            row["start_time"],
            row["end_time"],
            row["meeting_location"],
        )

        if meeting_key in section["meeting_signatures"]:
            continue

        section["meeting_signatures"].add(meeting_key)

        section["meetings"].append(
            {
                "day_of_week": row["day_of_week"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "meeting_location": row["meeting_location"],
            }
        )

    return courses


def build_course_groups(course_map):
    course_groups = []
    for course in course_map.values():
        variants = []
        for instructor in course["instructors"].values():
            sections = list(instructor["sections"].values())
            if not sections:
                continue

            sections_by_type = OrderedDict()
            for section in sections:
                sections_by_type.setdefault(section["section_type"], []).append(section)

            ordered_types = order_section_types(sections_by_type.keys())
            type_combinations = product(
                *(sections_by_type[section_type] for section_type in ordered_types)
            )

            for combo in type_combinations:
                variant_sections = []
                raw_meetings = []

                for section in combo:
                    display_section, section_meetings = prepare_section(section)
                    variant_sections.append(display_section)
                    raw_meetings.extend(section_meetings)

                variants.append(
                    {
                        "course_id": course["course_id"],
                        "course_title": course["title"],
                        "instructor_name": instructor["name"],
                        "sections": variant_sections,
                        "meetings": raw_meetings,
                    }
                )

        if variants:
            course_groups.append(
                {"course_id": course["course_id"], "title": course["title"], "variants": variants}
            )

    return course_groups


def prepare_section(section):
    meetings = section["meetings"] or [
        {
            "day_of_week": "TBA",
            "start_time": None,
            "end_time": None,
            "meeting_location": None,
        }
    ]

    display_meetings = []
    raw_meetings = []
    for meeting in meetings:
        day_code = meeting["day_of_week"] or "TBA"
        start = meeting["start_time"]
        end = meeting["end_time"]
        location = meeting["meeting_location"] or section["campus"] or "TBA"

        display_meetings.append(
            {
                "day_of_week": day_code,
                "display_days": format_day_label(day_code),
                "time_range": format_time_range(start, end),
                "location": location,
                "start_time": start,
                "end_time": end,
            }
        )

        raw_meetings.append(
            {
                "day_of_week": day_code,
                "start_time": start,
                "end_time": end,
            }
        )

    return (
        {
            "section_type": section["section_type"],
            "campus": section["campus"],
            "meetings": display_meetings,
        },
        raw_meetings,
    )


def order_section_types(section_types):
    def sort_key(section_type):
        priority = (
            SECTION_TYPE_ORDER.index(section_type)
            if section_type in SECTION_TYPE_ORDER
            else len(SECTION_TYPE_ORDER)
        )
        return (priority, section_type)

    return sorted(section_types, key=sort_key)


def build_schedule_options(course_groups):
    results = []
    limit_reached = False

    def backtrack(index, current_schedule, taken_meetings):
        nonlocal limit_reached
        if len(results) >= MAX_SCHEDULES_DISPLAY:
            limit_reached = True
            return

        if index == len(course_groups):
            results.append(list(current_schedule))
            return

        for variant in course_groups[index]["variants"]:
            if has_conflict(variant["meetings"], taken_meetings):
                continue

            current_schedule.append(variant)
            taken_meetings.extend(variant["meetings"])
            backtrack(index + 1, current_schedule, taken_meetings)
            for _ in variant["meetings"]:
                taken_meetings.pop()
            current_schedule.pop()

            if limit_reached:
                return

    backtrack(0, [], [])
    return results[:MAX_SCHEDULES_DISPLAY], limit_reached


def has_conflict(new_meetings, existing_meetings):
    for meeting in new_meetings:
        day_codes = expand_days(meeting["day_of_week"])
        start = meeting["start_time"]
        end = meeting["end_time"]

        if not day_codes or not start or not end:
            continue

        for existing in existing_meetings:
            existing_days = expand_days(existing["day_of_week"])
            existing_start = existing["start_time"]
            existing_end = existing["end_time"]

            if (
                not existing_days
                or not existing_start
                or not existing_end
                or not set(day_codes) & set(existing_days)
            ):
                continue

            if start < existing_end and existing_start < end:
                return True

    return False


def expand_days(day_code):
    if not day_code or day_code == "TBA":
        return []
    if day_code == "TR":
        return ["TR"]
    return [day_code]


def build_events_by_day(schedule_mapping):
    events_by_day = {column["key"]: [] for column in DAY_COLUMNS}
    events_by_day["TBA"] = []

    for variant in schedule_mapping:
        for section in variant["sections"]:
            for meeting in section["meetings"]:
                event = {
                    "course_title": variant["course_title"],
                    "instructor_name": variant["instructor_name"],
                    "section_type": section["section_type"],
                    "campus": section["campus"],
                    "location": meeting["location"],
                    "day_of_week": meeting["day_of_week"],
                    "display_days": meeting["display_days"],
                    "time_range": meeting["time_range"],
                    "start_time": meeting["start_time"],
                }

                expanded = expand_days(meeting["day_of_week"])
                if expanded:
                    for day_key in expanded:
                        events_by_day[day_key].append(event)
                else:
                    events_by_day["TBA"].append(event)

    for day_key in DAY_COLUMNS:
        events_by_day[day_key["key"]].sort(
            key=lambda event: event["start_time"] or FAR_FUTURE_TIME
        )

    return events_by_day


def format_day_label(day_code):
    return get_day_label(day_code)


def format_time_range(start, end):
    if not start or not end:
        return "TBA"
    start_str = start.strftime("%I:%M %p").lstrip("0")
    end_str = end.strftime("%I:%M %p").lstrip("0")
    return f"{start_str} - {end_str}"

