# Temporary User Permissions

Temporary RBAC data is stored in:

```text
mcp_server/users.json
```

## Test Users

| User ID | Username | Role | Access |
|---|---|---|---|
| `u001` | `admin` | `admin` | All MVP tables. |
| `u002` | `staff` | `staff` | Patient and clinical care tables; no claims or payer finance tables. |
| `u003` | `user` | `user` | Operational/aggregate tables; no direct patient or claims access. |

Default user:

```text
u003
```

## MCP Usage

List test users:

```text
get_users()
```

Get schema visible to a user:

```text
get_schema(user_id="staff")
```

Validate and run SQL as a user:

```text
validate_readonly_sql(sql="SELECT COUNT(*) FROM patients", user_id="staff")
run_readonly_query(sql="SELECT COUNT(*) FROM encounters", user_id="user")
```

Permission errors use this format:

```text
permission_denied_table:patients
```

## Current Role Rules

`admin`

- Can read every MVP table.

`staff`

- Can read `patients`, `encounters`, `conditions`, `medications`, `observations`, `procedures`, `providers`, `organizations`.
- Cannot read `claims` or `payers`.
- Hidden patient identity columns in schema: `ssn`, `drivers`, `passport`.

`user`

- Can read `encounters`, `conditions`, `medications`, `observations`, `procedures`, `providers`, `organizations`, `payers`.
- Cannot read `patients` or `claims`.
