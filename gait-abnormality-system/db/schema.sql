-- =============================================================================
-- schema.sql
-- PostgreSQL Database Schema for Gait Abnormality Classification System
-- =============================================================================
-- B.Tech Biotechnology Capstone — Human Anatomy and Physiology
-- Course Project: Wearable Sensor-Based Real-Time Monitoring and
--                Classification of Human Gait Abnormalities
--
-- IMPORTANT DISCLAIMER:
--   This schema stores analysis sessions and ML results only.
--   No real patient medical records are stored here.
--   All sample data in seed_data.sql is explicitly synthetic/demo data
--   created solely for software pipeline testing.
--
-- Database: PostgreSQL 14+
-- To apply: psql -U <user> -d <dbname> -f schema.sql
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 0. Enum type — valid gait classification labels
-- ---------------------------------------------------------------------------
-- Using a PostgreSQL ENUM prevents invalid class values from ever being
-- inserted into the predictions table. This is more robust than a CHECK
-- constraint because the allowed set is defined in one place.
--
-- Classes:
--   normal       — Healthy walking pattern
--   parkinsonian — Short shuffling steps, festination, reduced arm swing
--   hemiplegic   — Asymmetric gait due to unilateral paralysis/weakness
--   ataxic       — Wide-based, uncoordinated, staggering pattern
--   spastic      — Stiff, scissor-like gait from spastic muscle tone
--   antalgic     — Pain-avoidance pattern (short stance on painful side)
-- ---------------------------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gait_class_enum') THEN
        CREATE TYPE gait_class_enum AS ENUM (
            'normal',
            'parkinsonian',
            'hemiplegic',
            'ataxic',
            'spastic',
            'antalgic'
        );
    END IF;
END
$$;


-- ---------------------------------------------------------------------------
-- 1. users
-- ---------------------------------------------------------------------------
-- Stores clinicians, researchers, or students who log in to the web app.
-- The "role" field controls access: 'admin' can view all sessions,
-- 'researcher' can upload data, 'student' has read-only demo access.
--
-- Relationship: One user → many gait_sessions (1:N)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    -- Primary key: auto-incrementing integer, assigned at INSERT
    user_id       SERIAL          PRIMARY KEY,

    -- Full name of the user (e.g., "Dr. Priya Sharma")
    name          VARCHAR(100)    NOT NULL,

    -- Login email — must be unique across all accounts
    email         VARCHAR(150)    NOT NULL UNIQUE,

    -- bcrypt / argon2 hash of the password — NEVER store plaintext
    password_hash VARCHAR(255)    NOT NULL,

    -- Access role: 'admin' | 'researcher' | 'student'
    role          VARCHAR(20)     NOT NULL DEFAULT 'researcher'
                  CHECK (role IN ('admin', 'researcher', 'student')),

    -- When the account was created (UTC)
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  users              IS 'Application user accounts (clinicians, researchers, students).';
COMMENT ON COLUMN users.user_id      IS 'Auto-incremented surrogate primary key.';
COMMENT ON COLUMN users.email        IS 'Unique login email address.';
COMMENT ON COLUMN users.password_hash IS 'Hashed password — never store plaintext.';
COMMENT ON COLUMN users.role         IS 'Access role: admin | researcher | student.';


-- ---------------------------------------------------------------------------
-- 2. gait_sessions
-- ---------------------------------------------------------------------------
-- Each row represents one analysis session — a single upload or simulation
-- run. Sessions are linked to the user who created them and carry metadata
-- about where the data came from (CSV upload, simulated, or public dataset).
--
-- Relationship: One user → many sessions (1:N)
--              One session → one gait_features row (1:1)
--              One session → many sensor_data rows (1:N)
--              One session → one or more predictions (1:N)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gait_sessions (
    -- Primary key
    session_id        SERIAL          PRIMARY KEY,

    -- Foreign key — the user who created this session
    user_id           INTEGER         NOT NULL
                      REFERENCES users(user_id) ON DELETE CASCADE,

    -- Participant/subject identifier (NOT a real patient ID — see disclaimer)
    -- Can be anonymous (e.g., "SYN_001") or a public dataset code (e.g., "GDI_042")
    subject_id        VARCHAR(50),

    -- Date and time of the walking session (UTC)
    session_date      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    recorded_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Approximate duration of the recorded walking bout in seconds
    duration_seconds  NUMERIC(8, 2),

    -- Walking surface/condition: 'level', 'inclined', 'treadmill', 'outdoor', 'lab'
    walking_condition VARCHAR(50)     DEFAULT 'lab',

    -- Source of the data: 'uploaded_csv' | 'simulated' | 'public_dataset'
    -- This field MUST always be set — it distinguishes real uploads from demos
    data_source       VARCHAR(20)     NOT NULL
                      CHECK (data_source IN ('uploaded_csv', 'simulated', 'public_dataset')),

    -- Original filename of the uploaded CSV (NULL for simulated data)
    file_name         VARCHAR(255),

    -- When the session record was created in the database (UTC)
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  gait_sessions               IS 'One row per analysis session (CSV upload or simulation).';
COMMENT ON COLUMN gait_sessions.subject_id    IS 'Participant code — NOT a real patient identifier.';
COMMENT ON COLUMN gait_sessions.data_source   IS 'uploaded_csv | simulated | public_dataset';
COMMENT ON COLUMN gait_sessions.file_name     IS 'Original uploaded filename (NULL for simulated data).';


-- ---------------------------------------------------------------------------
-- 3. sensor_data
-- ---------------------------------------------------------------------------
-- Raw time-series samples from the wearable IMU sensor (accelerometer +
-- gyroscope). Each row is ONE sample at ONE timestep for ONE session.
--
-- For a 30-second recording at 100 Hz → 3000 rows per session.
-- This table can grow very large — index on (session_id, timestamp).
--
-- NOTE: This table is optional. If the user uploads a pre-computed feature
-- CSV (not raw sensor data), only gait_features is populated.
--
-- Relationship: One session → many sensor rows (1:N)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sensor_data (
    -- Primary key
    sensor_id         BIGSERIAL       PRIMARY KEY,

    -- Foreign key to the parent session
    session_id        INTEGER         NOT NULL
                      REFERENCES gait_sessions(session_id) ON DELETE CASCADE,

    -- Time of this sample relative to session start (seconds)
    -- Stored as DOUBLE PRECISION for sub-millisecond precision
    timestamp         DOUBLE PRECISION NOT NULL,

    -- Accelerometer readings in m/s² (3 axes)
    acceleration_x    REAL            NOT NULL,
    acceleration_y    REAL            NOT NULL,
    acceleration_z    REAL            NOT NULL,

    -- Gyroscope readings in rad/s (3 axes)
    gyroscope_x       REAL            NOT NULL,
    gyroscope_y       REAL            NOT NULL,
    gyroscope_z       REAL            NOT NULL
);

COMMENT ON TABLE  sensor_data              IS 'Raw time-series IMU readings: accelerometer (m/s²) and gyroscope (rad/s).';
COMMENT ON COLUMN sensor_data.timestamp    IS 'Seconds from start of session. Use DOUBLE PRECISION for sub-ms accuracy.';


-- ---------------------------------------------------------------------------
-- 4. gait_features
-- ---------------------------------------------------------------------------
-- One row of computed gait parameters per session. These are the extracted
-- biomechanical features that get fed into the ML classifier.
--
-- The values are computed by src/feature_extraction.py after preprocessing.
-- All temporal features are in seconds; spatial features in meters.
--
-- Relationship: One session → one feature row (1:1)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gait_features (
    -- Primary key
    feature_id        SERIAL          PRIMARY KEY,

    -- Foreign key — each session has exactly one feature record
    session_id        INTEGER         NOT NULL UNIQUE
                      REFERENCES gait_sessions(session_id) ON DELETE CASCADE,

    -- ---- Temporal parameters ----

    -- Total number of steps detected in the session
    step_count        INTEGER,

    -- Steps per minute (cadence)
    cadence           NUMERIC(6, 2),

    -- Estimated walking speed in m/s
    walking_speed     NUMERIC(6, 4),

    -- Average distance of one step in meters (half a stride)
    step_length       NUMERIC(6, 4),

    -- Average distance of one full stride (left + right step) in meters
    stride_length     NUMERIC(6, 4),

    -- Average duration of one step in seconds
    step_time         NUMERIC(6, 4),

    -- Average duration of one full stride (two steps) in seconds
    stride_time       NUMERIC(6, 4),

    -- Time foot is in contact with ground (seconds) — typically 60% of stride
    stance_time       NUMERIC(6, 4),

    -- Time foot is in the air (seconds) — typically 40% of stride
    swing_time        NUMERIC(6, 4),

    -- Ratio between left and right step times (1.0 = perfect symmetry)
    gait_symmetry     NUMERIC(5, 4),

    -- ---- Signal statistics ----

    -- Mean of the 3-axis acceleration magnitude (m/s²)
    mean_acceleration NUMERIC(8, 4),

    -- Standard deviation of acceleration magnitude
    acceleration_std  NUMERIC(8, 4),

    -- Root-mean-square of acceleration magnitude
    acceleration_rms  NUMERIC(8, 4),

    mean_gyroscope    NUMERIC(8, 4),
    gyroscope_std     NUMERIC(8, 4),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  gait_features             IS 'Extracted biomechanical features per session — input to the ML model.';
COMMENT ON COLUMN gait_features.gait_symmetry IS 'Left-right step symmetry ratio. 1.0 = perfectly symmetric.';
COMMENT ON COLUMN gait_features.stance_time   IS '~60% of stride_time for normal gait.';
COMMENT ON COLUMN gait_features.swing_time    IS '~40% of stride_time for normal gait.';


-- ---------------------------------------------------------------------------
-- 5. predictions
-- ---------------------------------------------------------------------------
-- Stores ML model output for each session. Multiple predictions per session
-- are allowed if the user re-runs analysis with a different model version.
--
-- predicted_class uses the gait_class_enum type — invalid class values are
-- rejected by the database engine before any application logic runs.
--
-- Relationship: One session → one or more predictions (1:N)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS predictions (
    -- Primary key
    prediction_id       SERIAL           PRIMARY KEY,

    -- Foreign key to the session that generated this prediction
    session_id          INTEGER          NOT NULL
                        REFERENCES gait_sessions(session_id) ON DELETE CASCADE,

    -- The winning class label — enforced by enum, cannot be misspelled
    predicted_class     VARCHAR(50)      NOT NULL,

    -- Model's probability/confidence for the predicted class (0.0 – 1.0)
    confidence_score    NUMERIC(5, 4)    NOT NULL
                        CHECK (confidence_score BETWEEN 0.0 AND 1.0),

    prob_normal         NUMERIC(5, 4)    DEFAULT 0,
    prob_parkinsonian   NUMERIC(5, 4)    DEFAULT 0,
    prob_hemiplegic     NUMERIC(5, 4)    DEFAULT 0,
    prob_ataxic         NUMERIC(5, 4)    DEFAULT 0,
    prob_spastic        NUMERIC(5, 4)    DEFAULT 0,
    prob_antalgic       NUMERIC(5, 4)    DEFAULT 0,

    -- Identifier of the model file used (e.g., 'random_forest_v1')
    model_name          VARCHAR(100)     NOT NULL DEFAULT 'random_forest_baseline',

    -- Semantic version string (e.g., '1.0.0', '2.1.3')
    model_version       VARCHAR(20)      NOT NULL DEFAULT '1.0.0',

    -- When this prediction was generated (UTC)
    prediction_timestamp TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  predictions                  IS 'ML model output for each session. Supports multiple model versions.';
COMMENT ON COLUMN predictions.predicted_class  IS 'Winning gait class.';
COMMENT ON COLUMN predictions.confidence_score IS 'Softmax probability of predicted class [0, 1].';

COMMENT ON TABLE  predictions                  IS 'ML model output for each session. Supports multiple model versions.';
COMMENT ON COLUMN predictions.predicted_class  IS 'Winning gait class — validated by gait_class_enum.';
COMMENT ON COLUMN predictions.confidence_score IS 'Softmax probability of predicted class [0, 1].';


-- ---------------------------------------------------------------------------
-- 6. model_performance
-- ---------------------------------------------------------------------------
-- Audit log of every model training run. Stores accuracy, precision, recall,
-- and F1 so you can compare model versions over time.
--
-- This is a standalone table — not linked to sessions or users.
-- It is written to by src/train_classifier.py after each training run.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS model_performance (
    -- Primary key
    model_id        SERIAL          PRIMARY KEY,

    -- Human-readable model identifier matching the value in predictions
    model_name      VARCHAR(100)    NOT NULL,

    -- Semantic version (should match predictions.model_version)
    model_version   VARCHAR(20)     NOT NULL,

    -- Overall accuracy on the held-out test set (0.0 – 1.0)
    accuracy        NUMERIC(5, 4),

    -- Macro-averaged precision across all 6 classes
    precision_score NUMERIC(5, 4),

    -- Macro-averaged recall across all 6 classes
    recall_score    NUMERIC(5, 4),

    -- Macro-averaged F1-score across all 6 classes
    f1_score        NUMERIC(5, 4),

    -- The number of training samples used
    training_samples INTEGER,

    -- UTC datetime of training run
    training_date   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Unique constraint: only one performance record per (name, version)
    UNIQUE (model_name, model_version)
);

COMMENT ON TABLE  model_performance              IS 'Audit log of ML training runs with evaluation metrics.';
COMMENT ON COLUMN model_performance.precision_score IS 'Macro-averaged precision (average across all 6 classes).';
COMMENT ON COLUMN model_performance.recall_score    IS 'Macro-averaged recall (average across all 6 classes).';


-- =============================================================================
-- INDEXES
-- =============================================================================
-- Indexes speed up the most common query patterns:
--   1. Fetching all sessions for a user → INDEX on gait_sessions(user_id)
--   2. Fetching sensor rows for a session → INDEX on sensor_data(session_id, timestamp)
--   3. Fetching predictions for a session → INDEX on predictions(session_id)
--   4. Finding latest model metrics → INDEX on model_performance(model_name, training_date)
-- =============================================================================

-- Speeds up dashboard / history queries per user
CREATE INDEX IF NOT EXISTS idx_gait_sessions_user_id
    ON gait_sessions(user_id);

-- Speeds up "show all sessions ordered by date" queries
CREATE INDEX IF NOT EXISTS idx_gait_sessions_created_at
    ON gait_sessions(created_at DESC);

-- Speeds up time-series fetch for a specific session
CREATE INDEX IF NOT EXISTS idx_sensor_data_session_ts
    ON sensor_data(session_id, timestamp);

-- Speeds up fetching predictions for a session
CREATE INDEX IF NOT EXISTS idx_predictions_session_id
    ON predictions(session_id);

-- Speeds up filtering predictions by class (analytics)
CREATE INDEX IF NOT EXISTS idx_predictions_class
    ON predictions(predicted_class);

-- Speeds up model version lookups
CREATE INDEX IF NOT EXISTS idx_model_perf_name_version
    ON model_performance(model_name, model_version);
