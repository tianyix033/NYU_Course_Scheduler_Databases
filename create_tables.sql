-- obsolete; see COMMANDS.sql
create Table Course(
    course_id VARCHAR(30),
    title VARCHAR(30) NOT NULL,
    credits INT(1) NOT NULL,
    course_description TEXT,
    prerequisites VARCHAR(50),
    Primary Key (course_id)
);

CREATE TABLE Instructor (
    instructor_id INT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL
);

create Table Section(
    section_id INT,
    course_id VARCHAR(30) NOT NULL,
    instructor_id INT NOT NULL,
    section_type ENUM('Lecture', 'Lab') NOT NULL,
    campus ENUM('Washington Square', 'Brooklyn Campus') NOT NULL,
    Primary Key (section_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (instructor_id) REFERENCES Instructor(instructor_id)
);

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT NOT NULL, 
    username VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY(user_id)
);

CREATE TABLE Review (
    user_id INT,
    course_id VARCHAR(30),
    instructor_id INT,
    rating INT NOT NULL CHECK (rating >= 0 AND rating <= 5)
    comment TEXT,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, course_id, instructor_id),
    FOREIGN KEY(user_id) REFERENCES User(user_id)
);

CREATE TABLE User_Selection (
    user_id INT, 
    course_id VARCHAR(30), 
    instructor_id INT,
    FOREIGN KEY(user_id) REFERENCES User(user_id),
    FOREIGN KEY(course_id) REFERENCES Course(course_id),
    FOREIGN KEY(instructor_id) REFERENCES Instructor(instructor_id),
    PRIMARY KEY (user_id, course_id, instructor_id)
);

create Table Meeting_Time(
    meeting_id INT,
    section_id INT,
    day_of_week ENUM('M', 'T', 'W', 'TR', 'F') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    meeting_location VARCHAR(20),
    Primary Key (meeting_id),
    FOREIGN KEY (section_id) REFERENCES Section(section_id)
);

