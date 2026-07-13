SELECT COUNT(*) AS total_patients
FROM patients;

SELECT gender, COUNT(*) AS total
FROM patients
GROUP BY gender
ORDER BY total DESC;

SELECT city, state, COUNT(*) AS total_patients
FROM patients
GROUP BY city, state
ORDER BY total_patients DESC
LIMIT 10;

SELECT encounterclass, COUNT(*) AS total_encounters
FROM encounters
GROUP BY encounterclass
ORDER BY total_encounters DESC;

SELECT EXTRACT(YEAR FROM start) AS year, COUNT(*) AS total_encounters
FROM encounters
GROUP BY year
ORDER BY year;

SELECT description, COUNT(*) AS total
FROM conditions
GROUP BY description
ORDER BY total DESC
LIMIT 10;

SELECT COUNT(DISTINCT patient) AS total_patients
FROM conditions
WHERE description ILIKE '%diabetes%';

SELECT COUNT(DISTINCT patient) AS total_patients
FROM conditions
WHERE description ILIKE '%hypertension%';

SELECT description, COUNT(*) AS total
FROM medications
GROUP BY description
ORDER BY total DESC
LIMIT 10;

SELECT EXTRACT(YEAR FROM start) AS year, SUM(totalcost) AS total_medication_cost
FROM medications
GROUP BY year
ORDER BY year;

SELECT description, COUNT(*) AS total
FROM procedures
GROUP BY description
ORDER BY total DESC
LIMIT 10;

SELECT description, AVG(base_cost) AS avg_base_cost
FROM procedures
GROUP BY description
ORDER BY avg_base_cost DESC
LIMIT 10;

SELECT description, COUNT(*) AS total
FROM observations
GROUP BY description
ORDER BY total DESC
LIMIT 10;

SELECT
  description,
  AVG(value::NUMERIC) AS avg_value,
  units
FROM observations
WHERE value ~ '^-?[0-9]+(\.[0-9]+)?$'
GROUP BY description, units
ORDER BY COUNT(*) DESC
LIMIT 10;

SELECT
  patient,
  COUNT(*) AS total_encounters
FROM encounters
GROUP BY patient
ORDER BY total_encounters DESC
LIMIT 10;

SELECT
  p.id,
  p.first_name,
  p.last_name,
  COUNT(c.code) AS total_conditions
FROM patients p
JOIN conditions c ON c.patient = p.id
GROUP BY p.id, p.first_name, p.last_name
ORDER BY total_conditions DESC
LIMIT 10;

SELECT
  o.name AS organization_name,
  COUNT(*) AS total_encounters
FROM encounters e
JOIN organizations o ON o.id = e.organization
GROUP BY o.name
ORDER BY total_encounters DESC
LIMIT 10;

SELECT
  pr.name AS provider_name,
  COUNT(*) AS total_encounters
FROM encounters e
JOIN providers pr ON pr.id = e.provider
GROUP BY pr.name
ORDER BY total_encounters DESC
LIMIT 10;

SELECT
  encounterclass,
  AVG(total_claim_cost) AS avg_claim_cost
FROM encounters
GROUP BY encounterclass
ORDER BY avg_claim_cost DESC;

SELECT
  status1,
  SUM(outstanding1) AS total_outstanding
FROM claims
GROUP BY status1
ORDER BY total_outstanding DESC;
