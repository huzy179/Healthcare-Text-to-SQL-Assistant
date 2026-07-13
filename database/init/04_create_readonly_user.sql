DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = 'healthcare_readonly'
  ) THEN
    CREATE ROLE healthcare_readonly LOGIN PASSWORD 'readonly_password';
  END IF;
END
$$;

DO $$
BEGIN
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO healthcare_readonly', current_database());
END
$$;

GRANT USAGE ON SCHEMA public TO healthcare_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO healthcare_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO healthcare_readonly;
