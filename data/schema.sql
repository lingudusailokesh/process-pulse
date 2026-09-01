-- ==============================================================================
-- ProcessPulse: Enterprise Process Mining & Operational Intelligence Engine
-- Production MySQL 8.0 DDL Schema
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS process_pulse_db
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE process_pulse_db;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id VARCHAR(32) PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    cost_per_hour DECIMAL(10, 2) NOT NULL DEFAULT 45.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Process Definitions (e.g., Employee Onboarding, IT Service Request)
CREATE TABLE IF NOT EXISTS process_definitions (
    process_id VARCHAR(32) PRIMARY KEY,
    process_name VARCHAR(100) NOT NULL,
    description TEXT,
    sla_hours_target DECIMAL(6, 2) NOT NULL DEFAULT 120.00,
    target_cost DECIMAL(10, 2) NOT NULL DEFAULT 300.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Process Instances (Cases / Workflows)
CREATE TABLE IF NOT EXISTS process_instances (
    case_id VARCHAR(64) PRIMARY KEY,
    process_id VARCHAR(32) NOT NULL,
    requester_id VARCHAR(64) NOT NULL, -- Anonymized pseudonym
    department_id VARCHAR(32) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    current_status ENUM('IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'REJECTED') NOT NULL DEFAULT 'IN_PROGRESS',
    total_duration_hours DECIMAL(8, 2) NULL,
    is_sla_breached BOOLEAN NOT NULL DEFAULT FALSE,
    predicted_breach_probability DECIMAL(4, 3) NULL,
    variant_id VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (process_id) REFERENCES process_definitions(process_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT,
    INDEX idx_case_status (current_status),
    INDEX idx_case_dept_time (department_id, start_time)
) ENGINE=InnoDB;

-- 4. Process Event Logs (The Canonical Event Stream for Process Mining)
CREATE TABLE IF NOT EXISTS process_event_logs (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_id VARCHAR(64) NOT NULL,
    activity_name VARCHAR(100) NOT NULL,
    stage_order INT NOT NULL,
    actor_id VARCHAR(64) NOT NULL, -- Anonymized actor
    department_id VARCHAR(32) NOT NULL,
    event_timestamp DATETIME(3) NOT NULL,
    activity_status ENUM('STARTED', 'COMPLETED', 'REJECTED', 'REWORK_TRIGGERED') NOT NULL DEFAULT 'COMPLETED',
    cost_incurred DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES process_instances(case_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT,
    -- Critical composite indexes for fast chronological process mining & querying
    INDEX idx_case_time (case_id, event_timestamp),
    INDEX idx_activity_time (activity_name, event_timestamp),
    INDEX idx_dept_time (department_id, event_timestamp)
) ENGINE=InnoDB;

-- 5. Application Users (For Auth and RBAC)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('ADMIN', 'CONSULTANT', 'EXECUTIVE_VIEWER') NOT NULL DEFAULT 'CONSULTANT',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
