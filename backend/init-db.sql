-- GymSystem Database Initialization Script
-- This script initializes the PostgreSQL database for GymSystem

-- Create database if it doesn't exist (this is handled by Docker environment variables)
-- The database 'gymsystem' is created automatically by the postgres Docker image

-- Connect to the gymsystem database
\c gymsystem;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create custom types for enums (these will be created by Alembic migrations)
-- But we can create them here for initial setup if needed

-- User roles enum
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'MEMBER',
        'STAFF', 
        'TRAINER',
        'MANAGER',
        'ADMIN',
        'OWNER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Membership status enum
DO $$ BEGIN
    CREATE TYPE membership_status AS ENUM (
        'ACTIVE',
        'INACTIVE',
        'SUSPENDED',
        'EXPIRED',
        'CANCELLED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Payment status enum
DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM (
        'PENDING',
        'COMPLETED',
        'FAILED',
        'CANCELLED',
        'REFUNDED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Class status enum
DO $$ BEGIN
    CREATE TYPE class_status AS ENUM (
        'SCHEDULED',
        'IN_PROGRESS',
        'COMPLETED',
        'CANCELLED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Reservation status enum
DO $$ BEGIN
    CREATE TYPE reservation_status AS ENUM (
        'CONFIRMED',
        'CANCELLED',
        'NO_SHOW',
        'ATTENDED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Exercise category enum
DO $$ BEGIN
    CREATE TYPE exercise_category AS ENUM (
        'CARDIO',
        'STRENGTH',
        'FLEXIBILITY',
        'BALANCE',
        'SPORTS',
        'FUNCTIONAL',
        'REHABILITATION'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Muscle group enum
DO $$ BEGIN
    CREATE TYPE muscle_group AS ENUM (
        'CHEST',
        'BACK',
        'SHOULDERS',
        'BICEPS',
        'TRICEPS',
        'FOREARMS',
        'ABS',
        'OBLIQUES',
        'LOWER_BACK',
        'GLUTES',
        'QUADRICEPS',
        'HAMSTRINGS',
        'CALVES',
        'FULL_BODY'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Equipment type enum
DO $$ BEGIN
    CREATE TYPE equipment_type AS ENUM (
        'BODYWEIGHT',
        'DUMBBELLS',
        'BARBELL',
        'KETTLEBELL',
        'RESISTANCE_BANDS',
        'CABLE_MACHINE',
        'CARDIO_MACHINE',
        'BENCH',
        'PULL_UP_BAR',
        'MEDICINE_BALL',
        'FOAM_ROLLER',
        'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Difficulty level enum
DO $$ BEGIN
    CREATE TYPE difficulty_level AS ENUM (
        'BEGINNER',
        'INTERMEDIATE',
        'ADVANCED',
        'EXPERT'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create functions for common operations

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to generate unique IDs
CREATE OR REPLACE FUNCTION generate_unique_id(prefix TEXT DEFAULT '')
RETURNS TEXT AS $$
BEGIN
    RETURN prefix || UPPER(REPLACE(uuid_generate_v4()::TEXT, '-', ''));
END;
$$ language 'plpgsql';

-- Function to calculate age from date of birth
CREATE OR REPLACE FUNCTION calculate_age(birth_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(birth_date));
END;
$$ language 'plpgsql';

-- Function to check if membership is active
CREATE OR REPLACE FUNCTION is_membership_active(start_date DATE, end_date DATE, status membership_status)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN status = 'ACTIVE' AND CURRENT_DATE BETWEEN start_date AND end_date;
END;
$$ language 'plpgsql';

-- Function to calculate membership duration in days
CREATE OR REPLACE FUNCTION membership_duration_days(start_date DATE, end_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN end_date - start_date;
END;
$$ language 'plpgsql';

-- Function to get membership remaining days
CREATE OR REPLACE FUNCTION membership_remaining_days(end_date DATE)
RETURNS INTEGER AS $$
BEGIN
    IF end_date < CURRENT_DATE THEN
        RETURN 0;
    ELSE
        RETURN end_date - CURRENT_DATE;
    END IF;
END;
$$ language 'plpgsql';

-- Function to format phone number
CREATE OR REPLACE FUNCTION format_phone(phone_number TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Remove all non-digit characters
    phone_number := REGEXP_REPLACE(phone_number, '[^0-9]', '', 'g');
    
    -- Format based on length
    IF LENGTH(phone_number) = 10 THEN
        RETURN '(' || SUBSTRING(phone_number, 1, 3) || ') ' || 
               SUBSTRING(phone_number, 4, 3) || '-' || 
               SUBSTRING(phone_number, 7, 4);
    ELSIF LENGTH(phone_number) = 11 AND SUBSTRING(phone_number, 1, 1) = '1' THEN
        RETURN '+1 (' || SUBSTRING(phone_number, 2, 3) || ') ' || 
               SUBSTRING(phone_number, 5, 3) || '-' || 
               SUBSTRING(phone_number, 8, 4);
    ELSE
        RETURN phone_number;
    END IF;
END;
$$ language 'plpgsql';

-- Function to validate email format
CREATE OR REPLACE FUNCTION is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ language 'plpgsql';

-- Function to generate membership number
CREATE OR REPLACE FUNCTION generate_membership_number()
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    sequence_part TEXT;
    membership_number TEXT;
BEGIN
    year_part := EXTRACT(YEAR FROM CURRENT_DATE)::TEXT;
    
    -- Get next sequence number for this year
    SELECT LPAD((COUNT(*) + 1)::TEXT, 4, '0')
    INTO sequence_part
    FROM memberships 
    WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE);
    
    membership_number := 'MEM' || year_part || sequence_part;
    
    RETURN membership_number;
END;
$$ language 'plpgsql';

-- Function to generate employee ID
CREATE OR REPLACE FUNCTION generate_employee_id()
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    sequence_part TEXT;
    employee_id TEXT;
BEGIN
    year_part := EXTRACT(YEAR FROM CURRENT_DATE)::TEXT;
    
    -- Get next sequence number for this year
    SELECT LPAD((COUNT(*) + 1)::TEXT, 3, '0')
    INTO sequence_part
    FROM employees 
    WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE);
    
    employee_id := 'EMP' || year_part || sequence_part;
    
    RETURN employee_id;
END;
$$ language 'plpgsql';

-- Function to generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number()
RETURNS TEXT AS $$
DECLARE
    year_part TEXT;
    month_part TEXT;
    sequence_part TEXT;
    invoice_number TEXT;
BEGIN
    year_part := EXTRACT(YEAR FROM CURRENT_DATE)::TEXT;
    month_part := LPAD(EXTRACT(MONTH FROM CURRENT_DATE)::TEXT, 2, '0');
    
    -- Get next sequence number for this month
    SELECT LPAD((COUNT(*) + 1)::TEXT, 4, '0')
    INTO sequence_part
    FROM invoices 
    WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
    AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE);
    
    invoice_number := 'INV' || year_part || month_part || sequence_part;
    
    RETURN invoice_number;
END;
$$ language 'plpgsql';

-- Create indexes for better performance (these will also be created by Alembic)
-- But we can create some basic ones here

-- Create a view for active memberships
CREATE OR REPLACE VIEW active_memberships AS
SELECT 
    m.*,
    u.first_name,
    u.last_name,
    u.email,
    mt.name as membership_type_name,
    membership_remaining_days(m.end_date) as remaining_days
FROM memberships m
JOIN users u ON m.user_id = u.id
JOIN membership_types mt ON m.membership_type_id = mt.id
WHERE m.status = 'ACTIVE' 
AND CURRENT_DATE BETWEEN m.start_date AND m.end_date;

-- Create a view for upcoming classes
CREATE OR REPLACE VIEW upcoming_classes AS
SELECT 
    c.*,
    u.first_name || ' ' || u.last_name as instructor_name,
    COUNT(r.id) as current_reservations,
    (c.max_capacity - COUNT(r.id)) as available_spots
FROM classes c
JOIN users u ON c.instructor_id = u.id
LEFT JOIN reservations r ON c.id = r.class_id AND r.status = 'CONFIRMED'
WHERE c.date_time > CURRENT_TIMESTAMP
AND c.status = 'SCHEDULED'
GROUP BY c.id, u.first_name, u.last_name
ORDER BY c.date_time;

-- Create a view for member statistics
CREATE OR REPLACE VIEW member_statistics AS
SELECT 
    u.id,
    u.first_name || ' ' || u.last_name as full_name,
    u.email,
    COUNT(DISTINCT r.id) as total_reservations,
    COUNT(DISTINCT CASE WHEN r.status = 'ATTENDED' THEN r.id END) as attended_classes,
    COUNT(DISTINCT CASE WHEN r.status = 'NO_SHOW' THEN r.id END) as no_shows,
    CASE 
        WHEN COUNT(DISTINCT r.id) > 0 THEN 
            ROUND((COUNT(DISTINCT CASE WHEN r.status = 'ATTENDED' THEN r.id END) * 100.0) / COUNT(DISTINCT r.id), 2)
        ELSE 0
    END as attendance_rate,
    MAX(r.created_at) as last_reservation_date
FROM users u
LEFT JOIN reservations r ON u.id = r.user_id
WHERE u.role_id = 1 -- Assuming role_id 1 is MEMBER
GROUP BY u.id, u.first_name, u.last_name, u.email;

-- Insert initial data (this will be handled by the application)
-- But we can insert some basic configuration data

-- Insert default roles (if the roles table exists)
-- This will be handled by Alembic migrations and application initialization

-- Create audit log table for tracking changes
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, changed_at)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD), CURRENT_TIMESTAMP);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, changed_at)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), CURRENT_TIMESTAMP);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values, changed_at)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW), CURRENT_TIMESTAMP);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE gymsystem TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Create application user (optional, for production)
-- CREATE USER gymsystem_app WITH PASSWORD 'your_secure_password';
-- GRANT CONNECT ON DATABASE gymsystem TO gymsystem_app;
-- GRANT USAGE ON SCHEMA public TO gymsystem_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gymsystem_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gymsystem_app;

-- Set timezone
SET timezone = 'UTC';

-- Show database information
\echo 'GymSystem database initialized successfully!'
\echo 'Database: gymsystem'
\echo 'Extensions: uuid-ossp, pgcrypto, unaccent'
\echo 'Custom functions and views created'
\echo 'Ready for Alembic migrations'

-- List all custom functions
\echo 'Custom functions created:'
\df+ update_updated_at_column
\df+ generate_unique_id
\df+ calculate_age
\df+ is_membership_active
\df+ membership_duration_days
\df+ membership_remaining_days
\df+ format_phone
\df+ is_valid_email
\df+ generate_membership_number
\df+ generate_employee_id
\df+ generate_invoice_number

-- List all custom views
\echo 'Custom views created:'
\dv+ active_memberships
\dv+ upcoming_classes
\dv+ member_statistics