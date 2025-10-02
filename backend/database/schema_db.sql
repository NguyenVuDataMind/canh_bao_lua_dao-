-- Anti-Phishing / Fraud Detection Web App - PostgreSQL Schema
-- Generated from provided DBML and requirements
-- Notes:
-- - Uses enums for controlled vocabularies
-- - Uses GENERATED ALWAYS AS IDENTITY for integer PKs
-- - Uses timestamptz for timestamps
-- - Adds comments where helpful

-- =============================
-- Extensions (optional helpers)
-- =============================
-- Enable pgcrypto if you want gen_random_uuid() for tokens, etc.
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================
-- Enums
-- =============================
DO $$ BEGIN
  -- user role/status
  CREATE TYPE user_role AS ENUM ('user', 'moderator', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE user_status AS ENUM ('active', 'suspended');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE report_status AS ENUM ('open', 'validated', 'dismissed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE severity_level AS ENUM ('low', 'medium', 'high');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE engine_type AS ENUM ('urlcheck', 'antivirus', 'ml');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE verdict_type AS ENUM ('malicious', 'suspicious', 'clean', 'error');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE indicator_type AS ENUM ('url', 'domain', 'ip', 'email', 'phone', 'hash');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE indicator_status AS ENUM ('malicious', 'suspicious', 'clean', 'unknown');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE threatfeed_format AS ENUM ('csv', 'txt', 'json', 'stix');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE case_status AS ENUM ('draft', 'published', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE lesson_status AS ENUM ('draft');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE quiz_mode AS ENUM ('single_choice', 'multi_choice', 'true_false');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE sos_status AS ENUM ('pending', 'sent', 'acknowledged', 'resolved');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE notification_type AS ENUM ('alert', 'lesson', 'system');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =============================
-- Tables
-- =============================

CREATE TABLE IF NOT EXISTS users (
  user_id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email          VARCHAR NOT NULL UNIQUE,
  password_hash  VARCHAR NOT NULL,
  full_name      VARCHAR,
  phone          VARCHAR,
  role           user_role NOT NULL DEFAULT 'user',
  status         user_status NOT NULL DEFAULT 'active',
  created_at     timestamptz NOT NULL DEFAULT now(),
  last_login_at  timestamptz
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE TABLE IF NOT EXISTS user_sessions (
  session_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id        INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  refresh_token  VARCHAR NOT NULL UNIQUE,
  ip_address     VARCHAR,
  user_agent     VARCHAR,
  expires_at     timestamptz NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

CREATE TABLE IF NOT EXISTS auth_providers (
  auth_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id      INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  provider     VARCHAR NOT NULL,
  provider_uid VARCHAR NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_auth_provider UNIQUE (provider, provider_uid)
);

CREATE INDEX IF NOT EXISTS idx_auth_providers_user_id ON auth_providers(user_id);

CREATE TABLE IF NOT EXISTS devices (
  device_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id       INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  device_uuid   VARCHAR NOT NULL UNIQUE,
  platform      VARCHAR,
  push_token    VARCHAR,
  created_at    timestamptz NOT NULL DEFAULT now(),
  last_seen_at  timestamptz
);

CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_platform ON devices(platform);

CREATE TABLE IF NOT EXISTS device_gps_state (
  device_id     INT PRIMARY KEY REFERENCES devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE,
  gps_enabled   INT,
  last_fix_ts   timestamptz,
  last_accuracy DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS emergency_contacts (
  contact_id  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id     INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  name        VARCHAR,
  phone       VARCHAR,
  relation    VARCHAR,
  method      VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_emergency_contacts_user_id ON emergency_contacts(user_id);

CREATE TABLE IF NOT EXISTS location_telemetry (
  telemetry_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id      INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  device_id    INT NOT NULL REFERENCES devices(device_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  latitude     DOUBLE PRECISION NOT NULL,
  longitude    DOUBLE PRECISION NOT NULL,
  accuracy_m   DOUBLE PRECISION,
  speed        DOUBLE PRECISION,
  ts           timestamptz
);

CREATE INDEX IF NOT EXISTS idx_location_telemetry_user_ts ON location_telemetry(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_location_telemetry_device_ts ON location_telemetry(device_id, ts);
CREATE INDEX IF NOT EXISTS idx_location_telemetry_lat_lon ON location_telemetry(latitude, longitude);

CREATE TABLE IF NOT EXISTS reports (
  report_id        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id          INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  reported_url     VARCHAR,
  reported_email   VARCHAR,
  reported_phone   VARCHAR,
  description      TEXT,
  source           VARCHAR,
  report_date      timestamptz,
  status           report_status NOT NULL DEFAULT 'open',
  severity         severity_level
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_report_date ON reports(report_date);
CREATE INDEX IF NOT EXISTS idx_reports_reported_url ON reports(reported_url);
CREATE INDEX IF NOT EXISTS idx_reports_reported_email ON reports(reported_email);
CREATE INDEX IF NOT EXISTS idx_reports_reported_phone ON reports(reported_phone);

CREATE TABLE IF NOT EXISTS report_attachments (
  attachment_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  report_id        INT NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE ON UPDATE CASCADE,
  file_url         VARCHAR NOT NULL,
  file_type        VARCHAR NOT NULL,
  mime_type        VARCHAR,
  storage_provider VARCHAR,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_report_attachments_report_id ON report_attachments(report_id);

CREATE TABLE IF NOT EXISTS indicators (
  indicator_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  type         indicator_type NOT NULL,
  value        VARCHAR NOT NULL,
  status       indicator_status,
  risk_score   DOUBLE PRECISION,
  first_seen   timestamptz,
  last_seen    timestamptz,
  source       VARCHAR,
  notes        TEXT,
  CONSTRAINT uq_indicator UNIQUE (type, value)
);

CREATE INDEX IF NOT EXISTS idx_indicators_status ON indicators(status);
CREATE INDEX IF NOT EXISTS idx_indicators_last_seen ON indicators(last_seen);

CREATE TABLE IF NOT EXISTS report_indicators (
  report_id    INT NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE ON UPDATE CASCADE,
  indicator_id INT NOT NULL REFERENCES indicators(indicator_id) ON DELETE CASCADE ON UPDATE CASCADE,
  relation     VARCHAR,
  primary_flag INT,
  CONSTRAINT pk_report_indicators PRIMARY KEY (report_id, indicator_id)
);

CREATE INDEX IF NOT EXISTS idx_report_indicators_indicator_id ON report_indicators(indicator_id);

CREATE TABLE IF NOT EXISTS scan_engines (
  engine_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name      VARCHAR NOT NULL,
  vendor    VARCHAR,
  version   VARCHAR,
  type      engine_type,
  enabled   INT NOT NULL DEFAULT 1,
  CONSTRAINT uq_scan_engine_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS scan_results (
  scan_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  report_id    INT REFERENCES reports(report_id) ON DELETE SET NULL ON UPDATE CASCADE,
  indicator_id INT NOT NULL REFERENCES indicators(indicator_id) ON DELETE CASCADE ON UPDATE CASCADE,
  engine_id    INT NOT NULL REFERENCES scan_engines(engine_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  verdict      verdict_type NOT NULL,
  score        DOUBLE PRECISION,
  raw_json     TEXT,
  scanned_at   timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scan_results_indicator_engine_scanned_at ON scan_results(indicator_id, engine_id, scanned_at);
CREATE INDEX IF NOT EXISTS idx_scan_results_report_id ON scan_results(report_id);

CREATE TABLE IF NOT EXISTS threat_feeds (
  feed_id         INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name            VARCHAR NOT NULL,
  source_url      VARCHAR NOT NULL,
  format          threatfeed_format NOT NULL,
  enabled         INT NOT NULL DEFAULT 1,
  last_fetched_at timestamptz,
  CONSTRAINT uq_threat_feed_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS feed_items (
  feed_item_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  feed_id          INT NOT NULL REFERENCES threat_feeds(feed_id) ON DELETE CASCADE ON UPDATE CASCADE,
  indicator_type   VARCHAR NOT NULL,
  indicator_value  VARCHAR NOT NULL,
  first_seen       timestamptz,
  last_seen        timestamptz,
  raw_line         TEXT
);

CREATE INDEX IF NOT EXISTS idx_feed_items_feed_id ON feed_items(feed_id);
CREATE INDEX IF NOT EXISTS idx_feed_items_indicator ON feed_items(indicator_type, indicator_value);

CREATE TABLE IF NOT EXISTS cases (
  case_id     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title       VARCHAR NOT NULL,
  category    VARCHAR,
  description TEXT,
  status      case_status NOT NULL DEFAULT 'draft',
  severity    severity_level,
  created_by  INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at);

CREATE TABLE IF NOT EXISTS case_indicators (
  case_id      INT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE ON UPDATE CASCADE,
  indicator_id INT NOT NULL REFERENCES indicators(indicator_id) ON DELETE CASCADE ON UPDATE CASCADE,
  role         VARCHAR,
  CONSTRAINT pk_case_indicators PRIMARY KEY (case_id, indicator_id)
);

CREATE INDEX IF NOT EXISTS idx_case_indicators_indicator_id ON case_indicators(indicator_id);

CREATE TABLE IF NOT EXISTS case_attachments (
  case_attachment_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id            INT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE ON UPDATE CASCADE,
  file_url           VARCHAR NOT NULL,
  file_type          VARCHAR NOT NULL,
  mime_type          VARCHAR,
  storage_provider   VARCHAR,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_case_attachments_case_id ON case_attachments(case_id);

CREATE TABLE IF NOT EXISTS case_labels (
  case_label_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id       INT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE ON UPDATE CASCADE,
  label         VARCHAR NOT NULL,
  CONSTRAINT uq_case_label UNIQUE (case_id, label)
);

CREATE INDEX IF NOT EXISTS idx_case_labels_case_id ON case_labels(case_id);

CREATE TABLE IF NOT EXISTS datasets (
  dataset_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id    INT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE ON UPDATE CASCADE,
  split      VARCHAR NOT NULL,
  input_ref  VARCHAR,
  target_ref VARCHAR,
  created_at timestamptz NOT NULL DEFAULT now(),
  notes      TEXT
);

CREATE TABLE IF NOT EXISTS lessons (
  lesson_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title       VARCHAR NOT NULL,
  status      lesson_status NOT NULL DEFAULT 'draft',
  description TEXT,
  created_by  INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS lesson_cases (
  lesson_id INT NOT NULL REFERENCES lessons(lesson_id) ON DELETE CASCADE ON UPDATE CASCADE,
  case_id   INT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE ON UPDATE CASCADE,
  role      VARCHAR,
  CONSTRAINT pk_lesson_cases PRIMARY KEY (lesson_id, case_id)
);

CREATE INDEX IF NOT EXISTS idx_lesson_cases_case_id ON lesson_cases(case_id);

CREATE TABLE IF NOT EXISTS quizzes (
  quiz_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  lesson_id INT NOT NULL REFERENCES lessons(lesson_id) ON DELETE CASCADE ON UPDATE CASCADE,
  title     VARCHAR,
  mode      quiz_mode
);

CREATE TABLE IF NOT EXISTS quiz_questions (
  question_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  quiz_id       INT NOT NULL REFERENCES quizzes(quiz_id) ON DELETE CASCADE ON UPDATE CASCADE,
  order_no      INT NOT NULL,
  question_text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz_order ON quiz_questions(quiz_id, order_no);

CREATE TABLE IF NOT EXISTS quiz_options (
  option_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL REFERENCES quiz_questions(question_id) ON DELETE CASCADE ON UPDATE CASCADE,
  order_no    INT NOT NULL,
  option_text TEXT NOT NULL,
  is_correct  INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_quiz_options_question_order ON quiz_options(question_id, order_no);

CREATE TABLE IF NOT EXISTS sos_requests (
  sos_id            INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id          INT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  device_id        INT NOT NULL REFERENCES devices(device_id) ON DELETE RESTRICT ON UPDATE CASCADE,
  triggered_at     timestamptz NOT NULL,
  status           sos_status NOT NULL DEFAULT 'pending',
  last_location_id INT REFERENCES location_telemetry(telemetry_id) ON DELETE SET NULL ON UPDATE CASCADE,
  notes            TEXT
);

CREATE TABLE IF NOT EXISTS sos_dispatch_logs (
  dispatch_id  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sos_id       INT NOT NULL REFERENCES sos_requests(sos_id) ON DELETE CASCADE ON UPDATE CASCADE,
  sent_to      VARCHAR NOT NULL,
  payload      TEXT,
  sent_at      timestamptz NOT NULL,
  status       VARCHAR NOT NULL,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS user_notifications (
  notification_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id         INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
  type            notification_type NOT NULL,
  title           VARCHAR NOT NULL,
  body            TEXT,
  read_at         timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_notifications_user_created ON user_notifications(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_notifications_read_at ON user_notifications(read_at);

CREATE TABLE IF NOT EXISTS audit_logs (
  log_id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id     INT REFERENCES users(user_id) ON DELETE SET NULL ON UPDATE CASCADE,
  action      VARCHAR NOT NULL,
  object_type VARCHAR,
  object_id   INT,
  ip_address  VARCHAR,
  ts          timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_ts ON audit_logs(ts);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_ts ON audit_logs(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_ts ON audit_logs(action, ts);

-- END OF SCHEMA


