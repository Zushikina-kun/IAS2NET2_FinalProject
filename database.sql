-- Gym Membership System Database
-- Group 9 | Leader: Directo, Brix A.
-- Members: Quimson Jibreel A., Madayag Djaunathan Albert S.
-- Note: This SQL schema is for reference only. The system uses JSON/CSV storage.

CREATE DATABASE IF NOT EXISTS gym_membership;
USE gym_membership;

-- Admin users table
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gym members table
CREATE TABLE IF NOT EXISTS members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    folder_name VARCHAR(100) NOT NULL UNIQUE,
    membership_type ENUM('monthly', 'quarterly', 'annual') DEFAULT 'monthly',
    status ENUM('active', 'expired', 'suspended') DEFAULT 'active',
    start_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    contact VARCHAR(20),
    email VARCHAR(100),
    emergency_contact VARCHAR(100),
    notes TEXT,
    total_visits INT DEFAULT 0,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entry log table
CREATE TABLE IF NOT EXISTS entry_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    folder_name VARCHAR(100),
    full_name VARCHAR(100),
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_result ENUM('granted', 'denied') DEFAULT 'granted',
    deny_reason VARCHAR(100),
    emotion VARCHAR(50),
    gender VARCHAR(10),
    age INT,
    confidence FLOAT
);

-- Default admin account (password hash of 'admin123' using SHA-256)
INSERT INTO admin_users (username, password_hash) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9')
ON DUPLICATE KEY UPDATE username=username;
