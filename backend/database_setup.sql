-- ============================================================
-- Finance Dashboard System — Database Setup
-- ============================================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS finance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE finance_db;

-- ============================================================
-- Table: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          INT             NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)    NOT NULL,
    email       VARCHAR(150)    NOT NULL,
    password    VARCHAR(255)    NOT NULL,
    role        ENUM(
                    'admin',
                    'analyst',
                    'viewer'
                )               NOT NULL DEFAULT 'viewer',
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
);

-- ============================================================
-- Table: records
-- ============================================================
CREATE TABLE IF NOT EXISTS records (
    id          INT             NOT NULL AUTO_INCREMENT,
    user_id     INT             NOT NULL,
    amount      DECIMAL(12, 2)  NOT NULL, /* Updated to DECIMAL to match backend financial precision */
    type        ENUM(
                    'income',
                    'expense'
                )               NOT NULL,
    category    VARCHAR(100)    NOT NULL,
    date        DATE            NOT NULL,
    notes       TEXT            NULL,
    is_deleted  BOOLEAN         NOT NULL DEFAULT FALSE, /* Required for your soft-delete logic */
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, /* Audit timestamp */

    -- Constraints
    PRIMARY KEY (id),
    CONSTRAINT fk_records_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE /* Changed to CASCADE to match your SQLAlchemy models */
        ON UPDATE CASCADE,

    -- Indexes for frequent query patterns (Dashboard optimizations)
    INDEX idx_records_type      (type),
    INDEX idx_records_date      (date),
    INDEX idx_records_category  (category),
    INDEX idx_records_user_id   (user_id, date) /* Updated to composite index for better filtering */
);
