# Database

PostgreSQL stores the imported healthcare CSV data.

## Files

- `init/01_create_tables.sql`: creates the MVP tables.
- `init/02_import_csv.sql`: imports CSV files from `data/synthea_csv`.
- `init/03_create_indexes.sql`: creates indexes for common filters and joins.
- `init/04_create_readonly_user.sql`: creates the read-only user used by the API.
- `scripts/check_tables.sql`: counts rows after import.
- `scripts/verify_joins.sql`: checks important join relationships.
- `scripts/sample_queries.sql`: manual SQL queries for Step 2 validation.

## Start PostgreSQL

```bash
cp .env.example .env
docker compose up -d postgres
```

The init scripts in `database/init` run only when the Docker volume is first created.

## Check Tables

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/check_tables.sql
```

## Verify Joins

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/verify_joins.sql
```

## Run Sample Queries

```bash
docker compose exec -T postgres psql -U healthcare_user -d healthcare < database/scripts/sample_queries.sql
```

## API Connection User

Use the read-only user for backend query execution:

```text
postgresql://healthcare_readonly:readonly_password@localhost:5433/healthcare
```

## Recreate Database Volume

This deletes the local PostgreSQL volume and imports CSV files again.

```bash
docker compose down -v
docker compose up -d postgres
```
