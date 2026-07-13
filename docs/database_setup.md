# Database Setup

Step 2 status: complete.

## Runtime

PostgreSQL is configured through Docker Compose.

```text
Container: healthcare_text_to_sql_postgres
Image: postgres:16
Host port: 5433
Container port: 5432
Database: healthcare
Admin user: healthcare_user
Read-only user: healthcare_readonly
```

The host port is `5433` because another local project is already using `5432`.

## Imported MVP Tables

Verified row counts:

| Table | Rows |
|---|---:|
| `patients` | 11,379 |
| `encounters` | 656,915 |
| `conditions` | 406,115 |
| `medications` | 545,439 |
| `observations` | 8,430,610 |
| `procedures` | 1,811,160 |
| `claims` | 1,202,354 |
| `providers` | 1,140 |
| `organizations` | 1,140 |
| `payers` | 10 |

## Verification Commands

Check table counts:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/check_tables.sql
```

Verify main joins:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/verify_joins.sql
```

Run manual sample queries:

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/sample_queries.sql
```

## Join Check Notes

Most main relationships match fully:

- `encounters -> patients`: 656,915 matched rows.
- `conditions -> patients`: 406,115 matched rows.
- `conditions -> encounters`: 406,115 matched rows.
- `medications -> patients`: 545,439 matched rows.
- `medications -> encounters`: 545,439 matched rows.
- `procedures -> patients`: 1,811,160 matched rows.
- `procedures -> encounters`: 1,811,160 matched rows.
- `providers -> organizations`: 1,140 matched rows.

Observation joins:

- `observations -> patients`: 8,430,610 matched rows.
- `observations -> encounters`: 8,123,065 matched rows.

This means every observation has a matching patient, but some observations do not match an encounter. Text-to-SQL prompts and joins should prefer patient joins for observations unless the question explicitly needs encounter context.

## Files Created For Step 2

- `docker-compose.yml`
- `.env.example`
- `database/init/01_create_tables.sql`
- `database/init/02_import_csv.sql`
- `database/init/03_create_indexes.sql`
- `database/init/04_create_readonly_user.sql`
- `database/scripts/check_tables.sql`
- `database/scripts/verify_joins.sql`
- `database/scripts/sample_queries.sql`
