SELECT COUNT(*) AS total_patients
FROM patients;

SELECT gender, COUNT(*) AS total
FROM patients
GROUP BY gender
ORDER BY total DESC;

SELECT description, COUNT(*) AS total
FROM conditions
GROUP BY description
ORDER BY total DESC
LIMIT 10;

SELECT EXTRACT(YEAR FROM start) AS year, COUNT(*) AS total_encounters
FROM encounters
GROUP BY year
ORDER BY year;

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
  encounterclass,
  AVG(total_claim_cost) AS avg_claim_cost
FROM encounters
GROUP BY encounterclass
ORDER BY avg_claim_cost DESC;
