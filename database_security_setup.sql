-- Database Security Setup for NYU Course Planner
-- This script sets up role-based access control at the
-- database level with two roles: 'app_user' and 'app_admin'
--
-- Role Definitions:
--   - app_user: End users who interact with the application
--   - app_admin: Developers/administrators with full access
-- Step 1: Create Roles
-- Create the app_user role (for end users)
DROP ROLE IF EXISTS app_user;
CREATE ROLE app_user WITH LOGIN PASSWORD 'user_password_change_in_production';

-- Create the app_admin role (for developers/administrators)
DROP ROLE IF EXISTS app_admin;
CREATE ROLE app_admin WITH LOGIN PASSWORD 'admin_password_change_in_production';

-- Step 2: Grant Privileges to app_user (End Users)

-- Allow app_user to read public course/instructor data
GRANT SELECT ON Course TO app_user;
GRANT SELECT ON Instructor TO app_user;
GRANT SELECT ON Section TO app_user;
GRANT SELECT ON Meeting_Time TO app_user;
GRANT SELECT ON Course_Instructor TO app_user;

-- Allow app_user to read all reviews (to view course reviews)
GRANT SELECT ON Review TO app_user;

-- Allow app_user to manage their own user account
GRANT SELECT, INSERT ON Users TO app_user;
-- Users can only update their own password (application-level enforcement)
GRANT UPDATE (password_hash) ON Users TO app_user;

-- Allow app_user to manage their own course selections
GRANT SELECT, INSERT, DELETE ON User_Selection TO app_user;
-- Users can only see/modify their own selections (application-level enforcement)

-- Allow app_user to create and view reviews
GRANT SELECT, INSERT ON Review TO app_user;
-- Users can only create reviews for themselves (application-level enforcement)
-- Users can update their own reviews (application-level enforcement)
GRANT UPDATE (rating, comment) ON Review TO app_user;

-- Step 3: Grant Execution Privileges to app_user

-- Allow app_user to execute stored procedures and functions
GRANT EXECUTE ON PROCEDURE AddUserSelection TO app_user;
GRANT EXECUTE ON PROCEDURE RemoveUserSelection TO app_user;
GRANT EXECUTE ON PROCEDURE PostReview TO app_user;
GRANT EXECUTE ON FUNCTION CheckUserLogin TO app_user;
GRANT EXECUTE ON FUNCTION RegisterNewUser TO app_user;
GRANT EXECUTE ON FUNCTION SearchCourse TO app_user;
GRANT EXECUTE ON FUNCTION SearchReview TO app_user;

-- Step 4: Grant Privileges to app_admin (Developers)

-- Grant full access to all tables for app_admin
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_admin;

-- Grant privileges on future tables (for schema evolution)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_admin;

-- Allow app_admin to execute all stored procedures and functions
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA public TO app_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_admin;

-- Grant privileges on future procedures/functions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON PROCEDURES TO app_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO app_admin;

-- Allow app_admin to create/modify database objects (for development)
GRANT CREATE ON SCHEMA public TO app_admin;
GRANT USAGE ON SCHEMA public TO app_admin;

-- Step 5: Sequence Privileges (for SERIAL columns)
-- Grant usage on sequences (needed for Users.user_id SERIAL)
DO $$
DECLARE
    seq_name TEXT;
BEGIN
    -- Get the actual sequence name for Users.user_id
    SELECT pg_get_serial_sequence('Users', 'user_id') INTO seq_name;
    IF seq_name IS NOT NULL THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO app_user', seq_name);
    END IF;
END $$;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_admin;

-- Grant privileges on future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_admin;

-- Step 6: Revoke Public Schema Access 
-- Revoke default public schema access from PUBLIC role
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE course_planner FROM PUBLIC;



