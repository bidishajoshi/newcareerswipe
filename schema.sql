-- CareerSwipe Database Schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS careerswipe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE careerswipe;

-- ─── Seekers ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS seekers (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    phone               VARCHAR(30),
    education           VARCHAR(255),
    experience          TEXT,
    skills              TEXT,
    resume_path         VARCHAR(500),
    verification_token  VARCHAR(100),
    is_verified         TINYINT(1) DEFAULT 0,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ─── Companies ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    company_name        VARCHAR(255) NOT NULL,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    description         TEXT,
    industry            VARCHAR(150),
    website             VARCHAR(300),
    logo_path           VARCHAR(500),
    verification_token  VARCHAR(100),
    is_verified         TINYINT(1) DEFAULT 0,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

-- ─── Jobs ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_listings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    required_skills TEXT,
    location        VARCHAR(255),
    job_type        ENUM('Full-time','Part-time','Contract','Internship','Remote') DEFAULT 'Full-time',
    salary          VARCHAR(100),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    INDEX idx_company (company_id)
) ENGINE=InnoDB;

-- ─── Swipes ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_swipes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    seeker_id   INT NOT NULL,
    job_id      INT NOT NULL,
    direction   ENUM('left','right') NOT NULL,
    status      ENUM('pending','accepted','rejected') DEFAULT 'pending',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seeker_id) REFERENCES seekers(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id)    REFERENCES jobs(id)    ON DELETE CASCADE,
    UNIQUE KEY unique_swipe (seeker_id, job_id),
    INDEX idx_seeker (seeker_id),
    INDEX idx_job    (job_id)
) ENGINE=InnoDB;

-- ─── Sample Data ────────────────────────────────────────────────────────────
-- Uncomment to seed demo data
/*
INSERT INTO companies (company_name,email,password_hash,description,industry,website,is_verified)
VALUES ('Leapfrog Technology','hr@leapfrog.io','hashed','Leading software company','Information Technology','https://leapfrog.io',1);

INSERT INTO jobs (company_id,title,description,required_skills,location,job_type,salary)
VALUES
  (1,'Frontend Developer','Build modern UIs with React and Tailwind.','React,JavaScript,CSS,HTML','Kathmandu','Full-time','NPR 60,000-90,000'),
  (1,'Backend Engineer','Develop REST APIs using Python Flask and MySQL.','Python,Flask,MySQL,REST API','Remote','Full-time','NPR 70,000-100,000'),
  (1,'Data Analyst','Analyse business data and build dashboards.','Python,SQL,Tableau,Excel','Kathmandu','Full-time','NPR 55,000-80,000');
*/
