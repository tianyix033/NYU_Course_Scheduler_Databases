-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Nov 10, 2025 at 04:26 AM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `course_planner`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `AddUserSelection` (IN `p_user_id` INT, IN `p_course_id` VARCHAR(30), IN `p_instructor_id` INT)   BEGIN
	DECLARE existing_count INT DEFAULT 0;

	SELECT COUNT(*)
	INTO existing_count
	FROM User_Selection
	WHERE user_id = p_user_id
	  AND course_id = p_course_id
	  AND instructor_id = p_instructor_id;

	IF existing_count = 0 THEN
		INSERT INTO User_Selection (user_id, course_id, instructor_id)
		VALUES (p_user_id, p_course_id, p_instructor_id);

		SELECT 'Successful' AS result;
	ELSE
		SELECT 'Already exist' AS result;
	END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `CheckUserLogin` (IN `input_username` VARCHAR(20), IN `input_password_hash` VARCHAR(255))   BEGIN

    DECLARE found_user_id INT;
    SELECT user_id INTO found_user_id
    FROM Users
    WHERE username = input_username AND password_hash = input_password_hash
    LIMIT 1;
    SELECT found_user_id AS authenticated_user_id;

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `PostReview` (IN `user_id` INT, IN `course_id` VARCHAR(30), IN `instructor_id` INT, IN `rating` INT, IN `comment` TEXT, IN `created_at` TIMESTAMP)   BEGIN
	INSERT INTO Review (user_id, course_id, instructor_id, rating, comment, created_at)
	VALUES (user_id, course_id, instructor_id, rating, comment, created_at);
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `RegisterNewUser` (IN `input_username` VARCHAR(20), IN `input_password_hash` VARCHAR(255))   BEGIN
    IF EXISTS (SELECT 1 FROM User WHERE username = input_username) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Username already exists.';
    ELSE

        INSERT INTO Users (username, password_hash)
        VALUES (input_username, input_password_hash);

        SELECT LAST_INSERT_ID() AS new_user_id;
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `RemoveUserSelection` (IN `p_user_id` INT, IN `p_course_id` VARCHAR(30), IN `p_instructor_id` INT)   BEGIN
	DECLARE existing_count INT DEFAULT 0;

	SELECT COUNT(*)
	INTO existing_count
	FROM User_Selection
	WHERE user_id = p_user_id
		AND course_id = p_course_id
		AND instructor_id = p_instructor_id;

	IF existing_count > 0 THEN
		DELETE FROM User_Selection
		WHERE user_id = p_user_id
			AND course_id = p_course_id
			AND instructor_id = p_instructor_id;
		SELECT 'Successful';
	ELSE
		SELECT 'Not Found';
	END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `SearchCourse` (IN `u_course_id` VARCHAR(30), IN `u_course_title` VARCHAR(255), IN `u_instructor_name` VARCHAR(200))   BEGIN
	SELECT
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
	WHERE (u_course_id IS NULL OR u_course_id = '' OR c.course_id LIKE CONCAT('%', u_course_id, '%'))
		AND (u_course_title IS NULL OR u_course_title = '' OR c.title LIKE CONCAT('%', u_course_title, '%'))
		AND (u_instructor_name IS NULL OR u_instructor_name = '' OR CONCAT(i.first_name, ' ', i.last_name) LIKE CONCAT('%', u_instructor_name, '%'))
	ORDER BY c.course_id, i.instructor_id, s.section_id, m.day_of_week;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `SearchReview` (IN `course_id` VARCHAR(30), IN `instructor_id` INT)   BEGIN
	SELECT 
		r.rating, 
		r.comment, 
		r.created_at,
		(
			SELECT title
			FROM Course c
			WHERE c.course_id = r.course_id
		) AS title,
		(
			SELECT credits
			FROM Course c
			WHERE c.course_id = r.course_id
		) AS credits,
		(
			SELECT course_description
			FROM Course c
			WHERE c.course_id = r.course_id
		) AS course_description,
		(
			SELECT CONCAT(i.first_name, ' ', i.last_name)
			FROM Instructor i
			WHERE i.instructor_id = r.instructor_id
		) AS instructor_name
	FROM Review r
	WHERE r.course_id = p_course_id
		AND r.instructor_id = p_instructor_id
	ORDER BY r.created_at DESC;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `Course`
--

CREATE TABLE `Course` (
  `course_id` varchar(30) NOT NULL,
  `title` varchar(100) NOT NULL,
  `credits` int(1) NOT NULL,
  `course_description` text DEFAULT NULL,
  `prerequisites` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Course`
--

INSERT INTO `Course` (`course_id`, `title`, `credits`, `course_description`, `prerequisites`) VALUES
('CS-UY 2204 | ECE-UY 2204', 'Digital Logic and State Machine Design', 4, 'This course covers combinational and sequential digital circuits. Topics: Introduction to digital systems. Number systems and binary arithmetic. Switching algebra and logic design. Error detection and correction. Combinational integrated circuits, including adders. Timing hazards. Sequential circuits, flipflops, state diagrams and synchronous machine synthesis. Programmable Logic Devices, PLA, PAL and FPGA. Finite-state machine design. Memory elements. ', 'CS-UY 1114(C- at least)or CS-UY 1133(C- at least)'),
('CS-UY 3224 | CS-UY 3224G', 'Intro to Operating Systems', 4, 'This course studies the fundamental concepts and principles of operating systems. Batch, spooling and multiprogramming systems are introduced. The parts of an operating system are described in terms of their functions, structure and implementation. Basic policies for allocating resources are discussed.', 'Prerequisites for Brooklyn Students: CS-UY 2214 AND (CS-UY 2134 or CS-UY 1134) AND (CS-UY 2124 or CS-UY 1124) (C- or better). | Prerequisite for Abu Dhabi Students: (ENGR-UH 3510 or CS-UH 1050) (C- or better) AND (CS-UH 2010 or ENGR-UH 3511) | Prerequisites for Shanghai Students: CSCI-SHU 210 (C- or better) AND CENG-SHU 202'),
('CS-UY 4543', 'Human Computer Interaction', 3, 'Designing a successful interactive experience or software system takes more than technical savvy and vision--it also requires a deep understanding of how to serve people\'s needs and desires through the experience of the system, and knowledge about how to weave this understanding into the development process. This course introduces key topics and methods for creating and evaluating human-computer interfaces/digital user experiences. Students apply these practices to a system of their choosing. (I encourage application to prototype systems that students are currently working on in other contexts, at any stage of development). The course builds toward a final write-up and presentation in which students detail how they tackled HCI/user experience design and evaluation of their system, and results from their investigations. Some experience creating/participating in the production of interactive experiences/software is recommended.', 'None'),
('CS-UY 4793 | CS-UY 4793G', 'Computer Networking', 3, 'This course takes a top-down approach to computer networking. After an overview of computer networks and the Internet, the course covers the application layer, transport layer, network layer and link layers. Topics at the application layer include client-server architectures, P2P architectures, DNS and HTTP and Web applications. Topics at the transport layer include multiplexing, connectionless transport and UDP, principles or reliable data transfer, connection-oriented transport and TCP and TCP congestion control. Topics at the network layer include forwarding, router architecture, the IP protocol and routing protocols including OSPF and BGP. Topics at the link layer include multiple-access protocols, ALOHA, CSMA/CD, Ethernet, CSMA/CA, wireless 802.11 networks and link-layer switches. The course includes simple quantitative delay and throughput modeling, socket programming and network application development and Ethereal labs.', 'Prerequisite for Brooklyn Students: (CS-UY 2134 or CS-UY 1134) and (CS-UY 2124 or CS-UY 1124) (C- or better) | Prerequisite for Abu Dhabi Students: ENGR-UH 3510 or CS-UH 1050 (C- or better) | Prerequisite for Shanghai Students: CSCI-SHU 210 (C- or better)'),
('CSCI-UA 101', 'Intro to Computer Science', 4, 'Foundational course on cs.', NULL),
('CSCI-UA 102', 'Data Structures', 4, 'Arrays, linked lists, trees, graphs.', 'CSCI-UA 101'),
('CSCI-UA 430', 'Agile Software Development and DevOps', 4, 'Agile software development has come to describe a specific approach and toolset that allow for the requirements of a software project to change as a project progresses without disrupting schedules, budgets, and responsibilities. The field of DevOps, a portmanteau of development and operations has introduced further processes and infrastructure to automate many of the tasks required in such development. Together, Agile\'s methodology and DevOps\' automation have increased the speed, robustness, and scalability with which software is developed today. Upon completion of this course, students will understand the core methodologies, technologies, and tools used in the software industry today.', 'CSCI-UA 201'),
('CSCI-UA 469', 'Natural Language Processing', 4, 'Natural Language Processing applies computational and linguistic knowledge to the processing of natural languages (English, Chinese, Spanish, Japanese). Applications include: machine translation, information extraction, information retrieval, and others. On the one hand, the class will include the modeling and representation of linguistic phenomena. On the other, it will cover methods for applying this knowledge using both manual rules and machine learning. Sample topics include: formal languages, hidden Markov models, part of speech tagging, vector-based methods, shallow and full parsing, semantic role labeling, information extraction and machine translation. Students will complete programming \r\nassignments (POS-tagging, Information Extraction, etc.) and group final projects.', NULL),
('CSCI-UA 475', 'Predictive Analytics ', 4, 'Predictive analytics is the art and science of extracting useful information from historical data and present data for the purpose of predicting future trends. In this course, students will be introduced to the phases of the analytics life-cycle and will gain an understanding of a variety of tools and machine learning algorithms for analyzing data and discovering forward insights. Several techniques will be introduced including: data preprocessing techniques, data reduction algorithms, data clustering algorithms, data classification algorithms, uplifting algorithms, association rules, data mining algorithms, recommender systems, and more. This course aims to provide students with skills of the new generation of data scientists that will allow them to structure, analyze and derive useful insights from data that could help make better decisions.', NULL),
('ECE-UY 1002', 'Introduction to Electrical and Computer Engineering', 2, 'This course introduces numerous subject areas in Electrical and Computer Engineering (power systems, electronics, computer networking, microprocessors, digital logic, embedded systems, communications, feedback control, and signal processing). ', 'First-year standing'),
('ECE-UY 345X', 'Undergraduate Research in Electrical and Computer Engineering', 1, 'The student will conduct research with the guidance of a faculty member. A written report is required. This course may be repeated for up to a maximum of 6 credits.', 'Contact rtoth@nyu.edu for permission'),
('MATH-UA 121', 'Calculus I', 4, 'Limits, derivatives, and integrals.', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `Course_Instructor`
--

CREATE TABLE `Course_Instructor` (
  `course_id` varchar(30) NOT NULL,
  `instructor_id` int(11) NOT NULL,
  `review_sum` int(11) DEFAULT 0,
  `review_count` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Course_Instructor`
--

INSERT INTO `Course_Instructor` (`course_id`, `instructor_id`, `review_sum`, `review_count`) VALUES
('CS-UY 2204 | ECE-UY 2204', 28934, 9, 3),
('CS-UY 3224 | CS-UY 3224G', 32241, 11, 3),
('CS-UY 4543', 45432, 4, 1),
('CS-UY 4793 | CS-UY 4793G', 47931, 12, 3),
('CSCI-UA 101', 213094198, 10, 2),
('CSCI-UA 102', 391689143, 4, 1),
('CSCI-UA 430', 142857142, 9, 2),
('CSCI-UA 469', 428571428, 4, 1),
('ECE-UY 1002', 39493, 8, 2),
('MATH-UA 121', 142890983, 5, 2);

-- --------------------------------------------------------

--
-- Table structure for table `Instructor`
--

CREATE TABLE `Instructor` (
  `instructor_id` int(11) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Instructor`
--

INSERT INTO `Instructor` (`instructor_id`, `first_name`, `last_name`) VALUES
(28934, 'Azeez', 'Bhavnagarwala'),
(32241, 'Gustavo', 'Sandoval'),
(38394, 'TBD', 'TBD'),
(39493, 'Matthew', 'Campisi'),
(45431, 'Raymond', 'Lutzky'),
(45432, 'Nitesh', 'Goyal'),
(47931, 'Lucas', 'O\'Rourke'),
(142857142, 'Amos', 'Bloomberg'),
(142890983, 'Michael Joseph', 'Stahl'),
(213094198, 'David', 'Daniels'),
(285714285, 'Ahmad', 'Emad'),
(391689143, 'Yitzchak', 'Schwartz'),
(428571428, 'Adam', 'Meyers');

-- --------------------------------------------------------

--
-- Table structure for table `Meeting_Time`
--

CREATE TABLE `Meeting_Time` (
  `meeting_id` int(11) NOT NULL,
  `section_id` int(11) DEFAULT NULL,
  `day_of_week` enum('M','T','W','TR','F','TBA') NOT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `meeting_location` varchar(40) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Meeting_Time`
--

INSERT INTO `Meeting_Time` (`meeting_id`, `section_id`, `day_of_week`, `start_time`, `end_time`, `meeting_location`) VALUES
(1001, 111111, 'TR', '12:30:00', '13:45:00', 'Online'),
(1002, 222222, 'TR', '11:00:00', '12:15:00', 'Silv 405'),
(1003, 222223, 'TR', '14:00:00', '15:15:00', 'Silv 408'),
(3001, 310947, 'W', '11:00:00', '12:15:00', 'SILV 406'),
(3002, 134867, 'W', '12:30:00', '13:45:00', 'TISC LC3'),
(3003, 458299, 'TR', '08:00:00', '09:15:00', 'SILV 206'),
(73483, 12243, 'T', '14:00:00', '15:50:00', 'Jacobs Hall 6 Metrotech RM 474'),
(172384, 12239, 'W', '14:00:00', '16:50:00', 'Jacobs Hall 6 Metrotech RM 227'),
(238949, 12240, 'TR', '17:00:00', '19:50:00', 'Jacobs Hall 6 Metrotech RM 227'),
(253673, 12275, 'T', '14:00:00', '15:20:00', '5 MetroTech Center Room AUD'),
(253674, 12275, 'TR', '14:00:00', '15:20:00', '5 MetroTech Center Room AUD'),
(273984, 12243, 'T', '14:00:00', '15:50:00', 'Jacobs Hall 6 Metrotech RM 474'),
(738648, 12241, 'F', '14:00:00', '16:50:00', 'Jacobs Hall 6 Metrotech RM 227'),
(3224111, 322411, 'T', '14:00:00', '15:50:00', '370 Jay St Room 202'),
(3224112, 322411, 'TR', '14:00:00', '15:50:00', '370 Jay St Room 202'),
(4543111, 454311, 'TBA', NULL, NULL, 'Online'),
(4543121, 454312, 'W', '17:00:00', '19:30:00', 'Jacobs Hall, 6 Metrotech Room 674'),
(4793111, 479311, 'M', '17:00:00', '18:20:00', '2 MetroTech Center Room 801'),
(4793112, 479311, 'W', '17:00:00', '18:20:00', '2 MetroTech Center Room 801');

-- --------------------------------------------------------

--
-- Table structure for table `Review`
--

CREATE TABLE `Review` (
  `user_id` int(11) NOT NULL,
  `course_id` varchar(30) NOT NULL,
  `instructor_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL CHECK (`rating` >= 0 and `rating` <= 5),
  `comment` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Review`
--

INSERT INTO `Review` (`user_id`, `course_id`, `instructor_id`, `rating`, `comment`, `created_at`) VALUES
(83873, 'CS-UY 2204 | ECE-UY 2204', 28934, 5, 'I like this course', '2025-11-07 16:59:00'),
(83873, 'ECE-UY 1002', 39493, 3, 'nice course, but hard', '2025-11-07 15:32:00'),
(83874, 'CS-UY 2204 | ECE-UY 2204', 28934, 1, 'terrible', '2025-11-07 14:59:00'),
(83876, 'CS-UY 4543', 45432, 4, 'The online component was flexible.', '2025-01-25 20:00:00'),
(83877, 'ECE-UY 1002', 39493, 5, 'Very engaging instructor.', '2025-02-10 14:00:00'),
(83878, 'CS-UY 2204 | ECE-UY 2204', 28934, 3, 'Solid material.', '2025-02-15 19:00:00'),
(83879, 'CS-UY 3224 | CS-UY 3224G', 32241, 5, 'Excellent content.', '2025-03-01 15:00:00'),
(83880, 'CS-UY 3224 | CS-UY 3224G', 32241, 2, 'The pace was too fast.', '2025-03-05 19:30:00'),
(83881, 'CS-UY 3224 | CS-UY 3224G', 32241, 4, 'Requires a lot of background knowledge.', '2025-03-10 20:00:00'),
(83882, 'CS-UY 4793 | CS-UY 4793G', 47931, 5, 'The networking labs were insightful.', '2025-04-01 15:30:00'),
(83882, 'CSCI-UA 430', 142857142, 5, 'generous in grade, nice prof', '2025-05-01 22:30:00'),
(83883, 'CS-UY 4793 | CS-UY 4793G', 47931, 4, 'Instructor explained TCP congestion control very clearly.', '2025-04-05 13:00:00'),
(83883, 'CSCI-UA 430', 142857142, 4, 'somewhat okay', '2025-03-05 13:20:00'),
(83884, 'CS-UY 4793 | CS-UY 4793G', 47931, 3, 'The theory felt a bit heavy at times.', '2025-04-10 19:45:00'),
(11111111, 'CSCI-UA 101', 213094198, 5, 'This course is very good. Would recommend', '2025-05-15 13:30:00'),
(12394712, 'CSCI-UA 101', 213094198, 5, 'amazing and helpful.', '2023-05-15 13:30:00'),
(22222222, 'MATH-UA 121', 142890983, 1, 'Terrible. A tremendous waste of time.', '2025-05-16 18:22:00'),
(33333333, 'CSCI-UA 469', 428571428, 4, 'Decent course. I learned a lot..', '2025-10-20 15:00:00'),
(34597234, 'CSCI-UA 102', 391689143, 4, 'challenging but rewarding, professor was very supportive.', '2023-12-20 16:00:00'),
(43529843, 'MATH-UA 121', 142890983, 4, 'great lecturer, exams are tough.', '2023-05-16 18:22:00');

--
-- Triggers `Review`
--
DELIMITER $$
CREATE TRIGGER `review_insert_upsert_trigger` AFTER INSERT ON `Review` FOR EACH ROW BEGIN
    INSERT INTO course_instructor 
        (course_id, instructor_id, review_sum, review_count)
    VALUES 
        (NEW.course_id, NEW.instructor_id, NEW.rating, 1)
    ON DUPLICATE KEY UPDATE
        review_sum = review_sum + NEW.rating,
        review_count = review_count + 1;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `Section`
--

CREATE TABLE `Section` (
  `section_id` int(11) NOT NULL,
  `course_id` varchar(30) NOT NULL,
  `instructor_id` int(11) NOT NULL,
  `section_type` enum('Lecture','Lab') NOT NULL,
  `campus` enum('Washington Square','Brooklyn Campus') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Section`
--

INSERT INTO `Section` (`section_id`, `course_id`, `instructor_id`, `section_type`, `campus`) VALUES
(12239, 'CS-UY 2204 | ECE-UY 2204', 28934, 'Lab', 'Brooklyn Campus'),
(12240, 'CS-UY 2204 | ECE-UY 2204', 28934, 'Lab', 'Brooklyn Campus'),
(12241, 'CS-UY 2204 | ECE-UY 2204', 28934, 'Lab', 'Brooklyn Campus'),
(12243, 'CS-UY 2204 | ECE-UY 2204', 28934, 'Lecture', 'Brooklyn Campus'),
(12275, 'ECE-UY 1002', 39493, 'Lecture', 'Brooklyn Campus'),
(111111, 'CSCI-UA 430', 142857142, 'Lecture', 'Washington Square'),
(134867, 'CSCI-UA 101', 142890983, 'Lab', 'Washington Square'),
(222222, 'CSCI-UA 469', 428571428, 'Lecture', 'Washington Square'),
(222223, 'CSCI-UA 469', 428571428, 'Lecture', 'Washington Square'),
(310947, 'CSCI-UA 101', 213094198, 'Lecture', 'Washington Square'),
(322411, 'CS-UY 3224 | CS-UY 3224G', 32241, 'Lecture', 'Brooklyn Campus'),
(454311, 'CS-UY 4543', 45431, 'Lecture', 'Brooklyn Campus'),
(454312, 'CS-UY 4543', 45432, 'Lecture', 'Brooklyn Campus'),
(458299, 'CSCI-UA 101', 391689143, 'Lecture', 'Washington Square'),
(479311, 'CS-UY 4793 | CS-UY 4793G', 47931, 'Lecture', 'Brooklyn Campus');

-- --------------------------------------------------------

--
-- Table structure for table `Users`
--

CREATE TABLE `Users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(20) NOT NULL,
  `password_hash` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Users`
--

INSERT INTO `Users` (`user_id`, `username`, `password_hash`) VALUES
(83873, 'vickyA', '344a0796ca0712be797c8bc103ea12a6'),
(83874, 'vickyB', '102ff968587291ba27ef40cac6e8b65f'),
(83875, 'vickyC', '505b2486f7317215f28da6c419bbdeb1'),
(83876, 'aronD', 'c81b9e830f6a29f82631626f376451e5'),
(83877, 'aronE', 'e8f3b2a5d1c4f9e0b7a6d5c4b3a2d1e0'),
(83878, 'aronF', 'a1b2c3d4e5f678901234567890abcdef'),
(83879, 'aronG', '1f3e7c2d9a6b58e4f0d9c8b7a6e5f4d3'),
(83880, 'aronH', '2e4d8a1c6b9e0f5d7a8b9c0d1e2f3a4b'),
(83881, 'aronI', '3a5c9b2d7e0f1a6d8b9c0e1f2a3b4c5d'),
(83882, 'aronJ', 'd4e2f1c3b5a90786543210fedcba9876'),
(83883, 'aronK', 'a7b8c9d0e1f2345678901234567890ab'),
(83884, 'aronL', 'f0e9d8c7b6a543210123456789abcdef'),
(11111111, 'sky_dragon', 'Skydragon4321?!'),
(12394712, 'alice', 'alice1234!'),
(22222222, 'flame_demon', 'Flamedemon4321?'),
(33333333, 'guy', 'guy4321?'),
(34597234, 'lisa', 'lisa1234!'),
(43529843, 'sam', 'sam1234!');

-- --------------------------------------------------------

--
-- Table structure for table `User_Selection`
--

CREATE TABLE `User_Selection` (
  `user_id` int(11) NOT NULL,
  `course_id` varchar(30) NOT NULL,
  `instructor_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `User_Selection`
--

INSERT INTO `User_Selection` (`user_id`, `course_id`, `instructor_id`) VALUES
(83873, 'CS-UY 2204 | ECE-UY 2204', 28934),
(83873, 'ECE-UY 1002', 39493),
(83874, 'ECE-UY 345X', 38394),
(83876, 'CS-UY 4543', 45432),
(83877, 'ECE-UY 1002', 39493),
(83878, 'CS-UY 2204 | ECE-UY 2204', 28934),
(83879, 'CS-UY 3224 | CS-UY 3224G', 32241),
(83880, 'CS-UY 3224 | CS-UY 3224G', 32241),
(83881, 'CS-UY 3224 | CS-UY 3224G', 32241),
(83882, 'CS-UY 4793 | CS-UY 4793G', 47931),
(83883, 'CS-UY 4793 | CS-UY 4793G', 47931),
(83884, 'CS-UY 4793 | CS-UY 4793G', 47931),
(11111111, 'CSCI-UA 430', 142857142),
(12394712, 'CSCI-UA 101', 213094198),
(22222222, 'CSCI-UA 430', 142857142),
(22222222, 'CSCI-UA 469', 428571428),
(34597234, 'MATH-UA 121', 391689143),
(43529843, 'CSCI-UA 102', 142890983);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Course`
--
ALTER TABLE `Course`
  ADD PRIMARY KEY (`course_id`);

--
-- Indexes for table `Course_Instructor`
--
ALTER TABLE `Course_Instructor`
  ADD PRIMARY KEY (`course_id`,`instructor_id`),
  ADD KEY `instructor_id` (`instructor_id`);

--
-- Indexes for table `Instructor`
--
ALTER TABLE `Instructor`
  ADD PRIMARY KEY (`instructor_id`);

--
-- Indexes for table `Meeting_Time`
--
ALTER TABLE `Meeting_Time`
  ADD PRIMARY KEY (`meeting_id`),
  ADD KEY `section_id` (`section_id`);

--
-- Indexes for table `Review`
--
ALTER TABLE `Review`
  ADD PRIMARY KEY (`user_id`,`course_id`,`instructor_id`);

--
-- Indexes for table `Section`
--
ALTER TABLE `Section`
  ADD PRIMARY KEY (`section_id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `instructor_id` (`instructor_id`);

--
-- Indexes for table `Users`
--
ALTER TABLE `Users`
  ADD PRIMARY KEY (`user_id`);

--
-- Indexes for table `User_Selection`
--
ALTER TABLE `User_Selection`
  ADD PRIMARY KEY (`user_id`,`course_id`,`instructor_id`),
  ADD KEY `course_id` (`course_id`),
  ADD KEY `instructor_id` (`instructor_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `Users`
--
ALTER TABLE `Users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=43529844;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `Course_Instructor`
--
ALTER TABLE `Course_Instructor`
  ADD CONSTRAINT `course_instructor_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `Course` (`course_id`),
  ADD CONSTRAINT `course_instructor_ibfk_2` FOREIGN KEY (`instructor_id`) REFERENCES `Instructor` (`instructor_id`);

--
-- Constraints for table `Meeting_Time`
--
ALTER TABLE `Meeting_Time`
  ADD CONSTRAINT `meeting_time_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `Section` (`section_id`);

--
-- Constraints for table `Review`
--
ALTER TABLE `Review`
  ADD CONSTRAINT `review_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`);

--
-- Constraints for table `Section`
--
ALTER TABLE `Section`
  ADD CONSTRAINT `section_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `Course` (`course_id`),
  ADD CONSTRAINT `section_ibfk_2` FOREIGN KEY (`instructor_id`) REFERENCES `Instructor` (`instructor_id`);

--
-- Constraints for table `User_Selection`
--
ALTER TABLE `User_Selection`
  ADD CONSTRAINT `user_selection_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`),
  ADD CONSTRAINT `user_selection_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `Course` (`course_id`),
  ADD CONSTRAINT `user_selection_ibfk_3` FOREIGN KEY (`instructor_id`) REFERENCES `Instructor` (`instructor_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
