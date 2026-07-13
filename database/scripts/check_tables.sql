SELECT 'patients' AS table_name, COUNT(*) AS total_rows FROM patients
UNION ALL SELECT 'encounters', COUNT(*) FROM encounters
UNION ALL SELECT 'conditions', COUNT(*) FROM conditions
UNION ALL SELECT 'medications', COUNT(*) FROM medications
UNION ALL SELECT 'observations', COUNT(*) FROM observations
UNION ALL SELECT 'procedures', COUNT(*) FROM procedures
UNION ALL SELECT 'claims', COUNT(*) FROM claims
UNION ALL SELECT 'providers', COUNT(*) FROM providers
UNION ALL SELECT 'organizations', COUNT(*) FROM organizations
UNION ALL SELECT 'payers', COUNT(*) FROM payers
ORDER BY table_name;
