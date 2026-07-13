SELECT 'encounters -> patients' AS relationship, COUNT(*) AS matched_rows
FROM encounters e
JOIN patients p ON p.id = e.patient
UNION ALL
SELECT 'conditions -> patients', COUNT(*)
FROM conditions c
JOIN patients p ON p.id = c.patient
UNION ALL
SELECT 'conditions -> encounters', COUNT(*)
FROM conditions c
JOIN encounters e ON e.id = c.encounter
UNION ALL
SELECT 'medications -> patients', COUNT(*)
FROM medications m
JOIN patients p ON p.id = m.patient
UNION ALL
SELECT 'medications -> encounters', COUNT(*)
FROM medications m
JOIN encounters e ON e.id = m.encounter
UNION ALL
SELECT 'observations -> patients', COUNT(*)
FROM observations o
JOIN patients p ON p.id = o.patient
UNION ALL
SELECT 'observations -> encounters', COUNT(*)
FROM observations o
JOIN encounters e ON e.id = o.encounter
UNION ALL
SELECT 'procedures -> patients', COUNT(*)
FROM procedures pr
JOIN patients p ON p.id = pr.patient
UNION ALL
SELECT 'procedures -> encounters', COUNT(*)
FROM procedures pr
JOIN encounters e ON e.id = pr.encounter
UNION ALL
SELECT 'providers -> organizations', COUNT(*)
FROM providers pr
JOIN organizations o ON o.id = pr.organization
ORDER BY relationship;
