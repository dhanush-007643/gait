-- =============================================================================
-- seed_data.sql
-- Synthetic / Demo Data for Gait Abnormality Classification System
-- =============================================================================
--
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
-- IMPORTANT — READ BEFORE USE
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
-- ALL data in this file is SYNTHETIC / DEMO data.
-- It is fabricated SOLELY to test the software pipeline.
-- It does NOT represent, approximate, or claim to represent measurements
-- from any real human being, patient, or clinical study.
-- Do NOT use these values for any medical, clinical, or research claim.
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--
-- To apply:
--   psql -U <user> -d <dbname> -f db/seed_data.sql
--
-- Run schema.sql FIRST to create all tables and enums.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. Demo Users  (3 synthetic accounts)
-- ---------------------------------------------------------------------------
-- Passwords shown here are DEMO ONLY — in production use proper hashed values.
-- $2b$12$DEMO... is not a real bcrypt hash; replace before deploying.

INSERT INTO users (name, email, password_hash, role) VALUES
    -- Demo admin account
    ('Demo Admin',      'admin@gaitlab.demo',      '$2b$12$DEMO_HASH_ADMIN_PLACEHOLDER',      'admin'),
    -- Demo researcher account
    ('Demo Researcher', 'researcher@gaitlab.demo',  '$2b$12$DEMO_HASH_RESEARCHER_PLACEHOLDER',  'researcher'),
    -- Demo student account
    ('Demo Student',    'student@gaitlab.demo',     '$2b$12$DEMO_HASH_STUDENT_PLACEHOLDER',     'student')
ON CONFLICT DO NOTHING;


-- ---------------------------------------------------------------------------
-- 2. Gait Sessions  (6 synthetic sessions — one per gait class)
-- ---------------------------------------------------------------------------
-- data_source = 'simulated' because no real CSV was uploaded.
-- subject_id uses 'SYN_' prefix to clearly indicate synthetic subjects.

INSERT INTO gait_sessions
    (user_id, subject_id, session_date, duration_seconds, walking_condition, data_source, file_name)
VALUES
    -- Session 1 — Normal gait demo
    (2, 'SYN_DEMO_001', '2026-09-01 09:00:00+05:30', 45.00, 'lab',      'simulated',   NULL),

    -- Session 2 — Parkinsonian gait demo
    (2, 'SYN_DEMO_002', '2026-09-01 09:30:00+05:30', 38.00, 'lab',      'simulated',   NULL),

    -- Session 3 — Hemiplegic gait demo
    (2, 'SYN_DEMO_003', '2026-09-01 10:00:00+05:30', 40.00, 'lab',      'simulated',   NULL),

    -- Session 4 — Ataxic gait demo
    (2, 'SYN_DEMO_004', '2026-09-01 10:30:00+05:30', 35.00, 'lab',      'simulated',   NULL),

    -- Session 5 — Spastic gait demo (uploaded CSV)
    (2, 'SYN_DEMO_005', '2026-09-01 11:00:00+05:30', 42.00, 'lab',      'uploaded_csv','demo_spastic.csv'),

    -- Session 6 — Antalgic gait demo (uploaded CSV)
    (2, 'SYN_DEMO_006', '2026-09-01 11:30:00+05:30', 50.00, 'outdoor',  'uploaded_csv','demo_antalgic.csv')
ON CONFLICT DO NOTHING;


-- ---------------------------------------------------------------------------
-- 3. Sensor Data  (12 sample rows — first 2 timesteps of session 1 only)
-- ---------------------------------------------------------------------------
-- In production each 45-second session at 100 Hz = 4500 rows.
-- These 12 rows demonstrate the schema only — not real measurements.

INSERT INTO sensor_data
    (session_id, timestamp, acceleration_x, acceleration_y, acceleration_z,
     gyroscope_x, gyroscope_y, gyroscope_z)
VALUES
    -- Session 1, t=0.00 s — synthetic normal walking sample
    (1, 0.00,  0.12, -0.08,  9.82,   0.02, -0.01,  0.03),
    (1, 0.01,  0.15, -0.06,  9.80,   0.03, -0.02,  0.02),
    (1, 0.02,  0.18, -0.05,  9.78,   0.03, -0.01,  0.04),
    (1, 0.03,  0.20, -0.04,  9.76,   0.04,  0.00,  0.03),
    (1, 0.04,  0.22, -0.03,  9.74,   0.04,  0.01,  0.02),
    (1, 0.05,  0.19, -0.05,  9.77,   0.03,  0.00,  0.03),

    -- Session 2, t=0.00 s — synthetic parkinsonian shuffling sample
    (2, 0.00,  0.05, -0.02,  9.70,   0.01, -0.01,  0.01),
    (2, 0.01,  0.06, -0.02,  9.69,   0.01,  0.00,  0.01),
    (2, 0.02,  0.07, -0.03,  9.68,   0.02, -0.01,  0.02),
    (2, 0.03,  0.06, -0.02,  9.70,   0.01,  0.00,  0.01),
    (2, 0.04,  0.05, -0.01,  9.71,   0.01,  0.01,  0.01),
    (2, 0.05,  0.07, -0.02,  9.69,   0.02, -0.01,  0.02)
ON CONFLICT DO NOTHING;


-- ---------------------------------------------------------------------------
-- 4. Gait Features  (6 rows — one per demo session)
-- ---------------------------------------------------------------------------
-- Values are SYNTHETIC — chosen to reflect class characteristics in the
-- literature but are NOT derived from real patient data.

INSERT INTO gait_features
    (session_id, step_count, cadence, walking_speed, step_length, stride_length,
     step_time, stride_time, stance_time, swing_time, gait_symmetry,
     mean_acceleration, acceleration_std, acceleration_rms)
VALUES
    -- Session 1 — Normal
    (1,  82,  109.3,  1.35,  0.698,  1.396,  0.549,  1.098,  0.659,  0.415,  0.961,
         9.85,  0.82,  9.89),

    -- Session 2 — Parkinsonian  (short steps, higher cadence, slow speed)
    (2,  76,  120.0,  0.65,  0.325,  0.650,  0.500,  1.000,  0.620,  0.310,  0.781,
         8.72,  2.10,  9.12),

    -- Session 3 — Hemiplegic  (slow, asymmetric, wide step-time variability)
    (3,  38,   57.0,  0.48,  0.420,  0.840,  1.053,  2.105,  0.730,  0.380,  0.524,
         8.15,  3.20,  8.80),

    -- Session 4 — Ataxic  (wide-based, high acceleration variability)
    (4,  42,   72.0,  0.55,  0.458,  0.916,  0.833,  1.667,  0.720,  0.420,  0.632,
         8.40,  4.10,  9.20),

    -- Session 5 — Spastic  (stiff, reduced swing time)
    (5,  50,   71.4,  0.58,  0.410,  0.820,  0.840,  1.680,  0.730,  0.280,  0.712,
         9.10,  2.70,  9.50),

    -- Session 6 — Antalgic  (reduced stance on painful side, limp pattern)
    (6,  68,   81.6,  0.82,  0.502,  1.005,  0.735,  1.470,  0.510,  0.480,  0.738,
         9.30,  1.60,  9.55)
ON CONFLICT DO NOTHING;


-- ---------------------------------------------------------------------------
-- 5. Predictions  (6 rows — one prediction per demo session)
-- ---------------------------------------------------------------------------

INSERT INTO predictions
    (session_id, predicted_class, confidence_score, model_name, model_version)
VALUES
    (1, 'normal',       0.9312, 'random_forest_baseline', '1.0.0'),
    (2, 'parkinsonian', 0.8741, 'random_forest_baseline', '1.0.0'),
    (3, 'hemiplegic',   0.8120, 'random_forest_baseline', '1.0.0'),
    (4, 'ataxic',       0.7654, 'random_forest_baseline', '1.0.0'),
    (5, 'spastic',      0.8003, 'random_forest_baseline', '1.0.0'),
    (6, 'antalgic',     0.8225, 'random_forest_baseline', '1.0.0')
ON CONFLICT DO NOTHING;


-- ---------------------------------------------------------------------------
-- 6. Model Performance  (1 row — baseline training run)
-- ---------------------------------------------------------------------------

INSERT INTO model_performance
    (model_name, model_version, accuracy, precision_score, recall_score,
     f1_score, training_samples, training_date)
VALUES
    ('random_forest_baseline', '1.0.0',
     0.8333, 0.8412, 0.8333, 0.8350, 96, '2026-09-01 08:00:00+05:30')
ON CONFLICT (model_name, model_version) DO NOTHING;
