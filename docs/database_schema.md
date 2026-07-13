# Database Schema

The database imports selected healthcare CSV files using lowercase PostgreSQL column names.

Core tables:

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

The initial schema is defined in `database/init/01_create_tables.sql`.

Related planning docs:

- `docs/data_inventory.md`
- `docs/data_dictionary.md`
- `docs/mvp_scope.md`
- `docs/database_setup.md`
