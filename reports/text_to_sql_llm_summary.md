# Text-to-SQL Evaluation Summary

| Metric | Value |
|---|---:|
| Total questions | 20 |
| Valid SQL | 0/20 |
| Exact Match Accuracy | 0/20 |
| Execution Accuracy | 0/20 |
| Average response time | 0.0 ms |

## Error Types

| Error Type | Count |
|---|---:|
| empty_sql | 20 |

## By Category

| Category | Questions | Exact Match | Execution Accuracy |
|---|---:|---:|---:|
| claim | 1 | 0/1 | 0/1 |
| cost | 2 | 0/2 | 0/2 |
| count | 1 | 0/1 | 0/1 |
| date | 1 | 0/1 | 0/1 |
| date_cost | 1 | 0/1 | 0/1 |
| filter | 2 | 0/2 | 0/2 |
| group_by | 2 | 0/2 | 0/2 |
| join | 3 | 0/3 | 0/3 |
| observation | 1 | 0/1 | 0/1 |
| top_n | 6 | 0/6 | 0/6 |

## SQL Error Analysis

### q001: Có bao nhiêu bệnh nhân trong hệ thống?

- Category: `count`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `1`
- Generated row count: `0`

Expected SQL:

```sql
SELECT COUNT(*) AS total_patients FROM patients;
```

Generated SQL:

```sql

```

### q002: Có bao nhiêu bệnh nhân theo giới tính?

- Category: `group_by`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `2`
- Generated row count: `0`

Expected SQL:

```sql
SELECT gender, COUNT(*) AS total FROM patients GROUP BY gender ORDER BY total DESC;
```

Generated SQL:

```sql

```

### q003: Top 10 thành phố có nhiều bệnh nhân nhất là gì?

- Category: `top_n`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT city, state, COUNT(*) AS total_patients FROM patients GROUP BY city, state ORDER BY total_patients DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q004: Có bao nhiêu lượt khám theo từng loại encounter?

- Category: `group_by`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT encounterclass, COUNT(*) AS total_encounters FROM encounters GROUP BY encounterclass ORDER BY total_encounters DESC;
```

Generated SQL:

```sql

```

### q005: Số lượt khám theo từng năm là bao nhiêu?

- Category: `date`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `111`
- Generated row count: `0`

Expected SQL:

```sql
SELECT EXTRACT(YEAR FROM start) AS year, COUNT(*) AS total_encounters FROM encounters GROUP BY year ORDER BY year;
```

Generated SQL:

```sql

```

### q006: Top 10 bệnh hoặc chẩn đoán phổ biến nhất là gì?

- Category: `top_n`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q007: Có bao nhiêu bệnh nhân từng có chẩn đoán liên quan đến Diabetes?

- Category: `filter`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `1`
- Generated row count: `0`

Expected SQL:

```sql
SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%diabetes%';
```

Generated SQL:

```sql

```

### q008: Có bao nhiêu bệnh nhân từng có chẩn đoán liên quan đến Hypertension?

- Category: `filter`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `1`
- Generated row count: `0`

Expected SQL:

```sql
SELECT COUNT(DISTINCT patient) AS total_patients FROM conditions WHERE description ILIKE '%hypertension%';
```

Generated SQL:

```sql

```

### q009: Top 10 thuốc xuất hiện nhiều nhất là gì?

- Category: `top_n`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT description, COUNT(*) AS total FROM medications GROUP BY description ORDER BY total DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q010: Tổng chi phí thuốc theo từng năm là bao nhiêu?

- Category: `date_cost`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `101`
- Generated row count: `0`

Expected SQL:

```sql
SELECT EXTRACT(YEAR FROM start) AS year, SUM(totalcost) AS total_medication_cost FROM medications GROUP BY year ORDER BY year;
```

Generated SQL:

```sql

```

### q011: Top 10 thủ thuật phổ biến nhất là gì?

- Category: `top_n`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT description, COUNT(*) AS total FROM procedures GROUP BY description ORDER BY total DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q012: Top 10 thủ thuật có chi phí trung bình cao nhất là gì?

- Category: `cost`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT description, AVG(base_cost) AS avg_base_cost FROM procedures GROUP BY description ORDER BY avg_base_cost DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q013: Top 10 loại observation xuất hiện nhiều nhất là gì?

- Category: `top_n`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT description, COUNT(*) AS total FROM observations GROUP BY description ORDER BY total DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q014: Giá trị trung bình của các observation dạng số phổ biến nhất là bao nhiêu?

- Category: `observation`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT description, AVG(value::NUMERIC) AS avg_value, units FROM observations WHERE value ~ '^-?[0-9]+(\.[0-9]+)?$' GROUP BY description, units ORDER BY COUNT(*) DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q015: Top 10 bệnh nhân có nhiều lượt khám nhất là ai?

- Category: `top_n`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT patient, COUNT(*) AS total_encounters FROM encounters GROUP BY patient ORDER BY total_encounters DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q016: Top 10 bệnh nhân có nhiều chẩn đoán nhất là ai?

- Category: `join`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT p.id, p.first_name, p.last_name, COUNT(c.code) AS total_conditions FROM patients p JOIN conditions c ON c.patient = p.id GROUP BY p.id, p.first_name, p.last_name ORDER BY total_conditions DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q017: Top 10 cơ sở y tế có nhiều lượt khám nhất là gì?

- Category: `join`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT o.name AS organization_name, COUNT(*) AS total_encounters FROM encounters e JOIN organizations o ON o.id = e.organization GROUP BY o.name ORDER BY total_encounters DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q018: Top 10 provider có nhiều lượt khám nhất là ai?

- Category: `join`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT pr.name AS provider_name, COUNT(*) AS total_encounters FROM encounters e JOIN providers pr ON pr.id = e.provider GROUP BY pr.name ORDER BY total_encounters DESC LIMIT 10;
```

Generated SQL:

```sql

```

### q019: Chi phí claim trung bình theo từng loại encounter là bao nhiêu?

- Category: `cost`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `10`
- Generated row count: `0`

Expected SQL:

```sql
SELECT encounterclass, AVG(total_claim_cost) AS avg_claim_cost FROM encounters GROUP BY encounterclass ORDER BY avg_claim_cost DESC;
```

Generated SQL:

```sql

```

### q020: Tổng outstanding claim amount theo từng trạng thái claim là bao nhiêu?

- Category: `claim`
- Error type: `empty_sql`
- Validation/execution error: `empty_sql`
- Expected row count: `2`
- Generated row count: `0`

Expected SQL:

```sql
SELECT status1, SUM(outstanding1) AS total_outstanding FROM claims GROUP BY status1 ORDER BY total_outstanding DESC;
```

Generated SQL:

```sql

```

