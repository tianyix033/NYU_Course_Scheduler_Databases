# NYU Course Planner

**Team Members:** Youwen Chen, Sally Qiao, Tianyi Xu, Ruimeng Yang; Name ordered alphabetically

---

## Project Overview

A student-centric planner that complements official registration. Students select course–instructor pairs; the app auto‑generates a conflict‑free weekly schedule and supports course/instructor reviews.

---

## Core Functionalities

| Feature | Description |
|---------|-------------|
| **Advanced Course Catalog** | Find courses with powerful search and filtering tools for campus, meeting times, and instructors. |
| **Automatic Schedule Generation** | The system automatically generates a weekly schedule based on the courses and instructors you select. |
| **Automatic Conflict Detection** | The system automatically flags any overlapping class times when selecting courses, preventing scheduling conflicts before they occur. |
| **Visual Schedule Display** | View your automatically generated schedule in an interactive weekly calendar format. |
| **Course Reviews** | Read and write anonymous reviews for courses and instructors, sharing insights on difficulty, teaching style, and workload with fellow students. |

---

## Database Schema

Key tables (condensed):
- `Course(course_id PK, title, credits, course_description, prerequisites)`
- `Instructor(instructor_id PK, first_name, last_name)`
- `Section(section_id PK, course_id FK, instructor_id FK, section_type, campus)`
- `Meeting_Time(meeting_id PK, section_id FK, day_of_week, start_time, end_time, meeting_location)`
- `Users(user_id PK, username, password_hash)`
- `User_Selection(user_id PK, course_id PK, instructor_id PK)` — selections drive the auto-schedule
- `Review(user_id PK, course_id PK, instructor_id PK, rating, comment, created_at)`
- `Course_Instructor(course_id PK, instructor_id PK, review_sum, review_count)` — aggregated ratings

---

## Relationships

This section describes how the entities in the database interact with each other based on one-to-one, one-to-many, and many-to-many relationships.

| Relationship | Type | Description |
|-------------|------|-------------|
| **Course → Section** | One-to-Many | A Course can have many Sections, but each Section belongs to exactly one Course. |
| **Instructor → Section** | One-to-Many | An Instructor can teach many Sections, but each Section is taught by one Instructor. |
| **Section → Meeting_Time** | One-to-Many | A Section can have multiple MeetingTimes (e.g., a separate lecture and lab), but each MeetingTime belongs to only one Section. |
| **User → User_Selection** | One-to-Many | A User can make many User_Selections, but each User_Selection belongs to exactly one User. |
| **User → Review** | One-to-Many | A User can write many Reviews, but each Review is written by a single User. |
| **Course-Instructor → Review** | One-to-Many | A Course-Instructor combination can have many Reviews written about them, handled by the composite primary key in the Review table. |
| **Course-Instructor Aggregation** | N/A | The relationship between Course and Instructor through reviews is tracked in the Course_Instructor table, which maintains aggregated review statistics (average rating, total count). |

---

## Business Rules

### User & Authentication

- A User must have a **unique username** to register.
- A User must be **logged in** to make User_Selections or write a Review.

### Scheduling Logic

- A User_Selection cannot exist without being linked to a User.
- A specific **Course-Instructor combination can only be selected once per User**. This is enforced by the database's composite primary key in User_Selection.
- The system **automatically generates a schedule** based on all courses and instructors in the user's User_Selection table.
- The application must **prevent a User from adding a Course-Instructor combination** if its MeetingTimes create a time conflict with another selection already made by that user.
- Users modify their schedule by **adding or removing course-instructor selections**, not by directly editing the schedule itself.

### Review System

- A Review must be associated with a valid User, Course, and Instructor.
- To maintain fairness and prevent spam, a User can only submit **one Review** for the same Course taught by the same Instructor. This is enforced by the composite primary key in the Review table.
- Review ratings must be between **0 and 5** (inclusive), enforced by a CHECK constraint.
- The Course_Instructor table automatically maintains review statistics (sum and count) via a trigger when reviews are inserted.

### Data Integrity

- A Section cannot be created without being assigned to a valid Course and Instructor.
- A MeetingTime cannot be created without being assigned to a valid Section.

---

## Schema Statements

```
Course(course_id (PK), title, credits, course_description, prerequisites)
Instructor(instructor_id (PK), first_name, last_name)
Section(section_id (PK), @course_id, @instructor_id, section_type, campus)
Meeting_Time(meeting_id (PK), @section_id, day_of_week, start_time, end_time, meeting_location)
Users(user_id (PK), username, password_hash)
User_Selection(@user_id (PK), @course_id (PK), @instructor_id (PK))
Review(@user_id (PK), @course_id (PK), @instructor_id (PK), rating, comment, created_at)
Course_Instructor(@course_id (PK), @instructor_id (PK), review_sum, review_count)
```

> **Normalization:** We checked the 1NF, 2NF, and 3NF - it's perfectly normalized based on the Albert logic.

---

## Database Components

### PostgreSQL Stored Procedures/Functions

The database includes the following PostgreSQL stored procedures or functions (converted from MySQL stored procedures) to support application functionality:

| Function | Purpose |
|-----------|---------|
| `RegisterNewUser` | Registers a new user with username and password hash |
| `CheckUserLogin` | Validates user credentials and returns user_id |
| `SearchCourse` | Searches for courses with optional filters for course_id, course_title, and instructor_name |
| `PostReview` | Inserts a new review for a course-instructor combination |
| `SearchReview` | Retrieves reviews for a specific course-instructor combination |
| `AddUserSelection` | Adds a course-instructor selection for a user (prevents duplicates) |
| `RemoveUserSelection` | Removes a course-instructor selection for a user |

> **Important:** These procedures/functions need to be converted from MySQL stored procedure syntax to PostgreSQL syntax. PostgreSQL 11+ supports stored procedures, but you can also use functions if you prefer. See `IMPLEMENTATION.md` for conversion examples.

### Database Triggers

| Trigger | Function |
|---------|----------|
| `review_insert_upsert_trigger` | Automatically updates Course_Instructor statistics when a new review is inserted |

> PostgreSQL triggers execute functions; details in `IMPLEMENTATION.md`.

---

## Assumptions and Justifications

### Prerequisite as Plain Text

**Assumption:** We assume that the application does not need to programmatically validate if a student meets the prerequisites for a course.

**Justification:** Modeling complex prerequisite logic (e.g., "(A or B) and C") requires a much more complicated database structure. Storing the requirement as a simple text string is a pragmatic tradeoff. It greatly simplifies the database design while still providing the necessary information for students to read and interpret themselves.

---

### One Instructor Per Section

**Assumption:** We assume that each course section has one primary instructor responsible for it.

**Justification:** While some courses may be team-taught, modeling a many-to-many relationship between instructors and sections would add complexity (requiring another junction table). For a student-facing planning tool, a one-to-many relationship covers the vast majority of cases and keeps the model simpler.

---

### Separated MeetingTime Entity

**Assumption:** We assume a single section can have multiple meetings in a week, often at different times or locations (e.g., a lecture and a lab).

**Justification:** This is a critical normalization step. Storing multiple meeting times within the Section table would violate database principles and make time-based queries (for filtering and conflict detection) extremely difficult and inefficient. A separate MeetingTime table creates a clean and flexible one-to-many relationship.

---

### User_Selection Instead of Schedule

**Assumption:** We simplify the schedule management by using a User_Selection table that directly links users to course-instructor combinations.

**Justification:** Instead of having separate Schedule and Schedule_Section tables, we use User_Selection to track which courses (with specific instructors) a user has selected. This simplifies the data model while still allowing users to manage their course selections. The application can implement schedule naming/organization features in the frontend using this table.

---

### Composite Primary Keys for Review and User_Selection

**Assumption:** We use composite primary keys (user_id, course_id, instructor_id) instead of auto-increment IDs for Review and User_Selection tables.

**Justification:** The composite keys naturally enforce business rules (one review per user-course-instructor, one selection per user-course-instructor) and eliminate the need for additional unique constraints. This simplifies the schema and improves data integrity.

---

### Course_Instructor Aggregation Table

**Assumption:** We maintain a separate Course_Instructor table to store aggregated review statistics (review_sum, review_count) for performance optimization.

**Justification:** Calculating average ratings from the Review table on every query would be inefficient. The Course_Instructor table with a trigger ensures review statistics are always up-to-date, allowing fast retrieval of average ratings without complex aggregations.

---


---

## Files in This Repository

- **README.md** - This file: Project overview, business logic, and database schema
- **IMPLEMENTATION.md** - Technical implementation guide with step-by-step instructions
- **COMMANDS.sql** - MySQL/MariaDB database schema (needs conversion to PostgreSQL)
- **create_tables.sql** - Obsolete table creation script (see COMMANDS.sql)
- **Minestone 2 User Interface - Google Docs.pdf** - UI mockups and design specifications

---
