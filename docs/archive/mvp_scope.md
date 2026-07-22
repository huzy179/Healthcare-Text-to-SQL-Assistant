# MVP Scope

The MVP goal is to prove this flow:

```text
CSV data -> PostgreSQL -> natural language question -> generated SQL -> SQL validation -> query result
```

## Included Tables

Start with:

- `patients`
- `encounters`
- `conditions`
- `medications`
- `observations`
- `procedures`
- `claims`
- `providers`
- `organizations`
- `payers`

## Excluded From MVP

Add later:

- `claims_transactions`
- `imaging_studies`
- `payer_transitions`
- `immunizations`
- `allergies`
- `careplans`
- `devices`
- `supplies`

## First Question Categories

Implement and test questions in this order:

1. Single-table counts.
2. Group-by aggregations.
3. Top N rankings.
4. Date filters by year/month.
5. Join between patient and clinical tables.
6. Cost analytics.
7. Observation value analytics.

## First 20 Manual SQL Questions

Use these to validate the database before adding LLM generation:

1. How many patients are in the dataset?
2. How many patients are there by gender?
3. What are the top 10 cities by patient count?
4. How many encounters are there by encounter class?
5. How many encounters happened by year?
6. What are the top 10 most common conditions?
7. How many distinct patients have Diabetes-like condition descriptions?
8. How many distinct patients have Hypertension-like condition descriptions?
9. What are the top 10 medications by record count?
10. What is the total medication cost by year?
11. What are the top 10 procedures by record count?
12. What is the average procedure base cost by procedure description?
13. What are the most common observation descriptions?
14. What are average numeric values for selected observation descriptions?
15. Which patients have the most encounters?
16. Which patients have the most recorded conditions?
17. Which organizations have the most encounters?
18. Which providers have the most encounters?
19. What is the average encounter claim cost by encounter class?
20. What is the outstanding claim amount by claim status?

## Acceptance Criteria For Step 1

Step 1 is complete when:

- CSV files are inventoried.
- Row counts are known.
- MVP tables are selected.
- Later-phase tables are identified.
- Main join keys are documented.
- Main risks are documented.
