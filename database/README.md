# Database

PostgreSQL stores the imported healthcare CSV data.

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

## Recreate Database Volume

This deletes the local PostgreSQL volume and imports CSV files again.

```bash
docker compose down -v
docker compose up -d postgres
```
