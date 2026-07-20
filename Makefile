COMPOSE ?= docker compose
MCP_SERVICE ?= mcp-server
POSTGRES_SERVICE ?= postgres
EVAL_SERVICE ?= eval
FRONTEND_SERVICE ?= frontend

.PHONY: help setup build build-frontend frontend frontend-logs up down ps logs db-shell check-tables sample-queries verify-joins mcp eval eval-generated test-rbac local-eval clean reset-db

help:
	@printf "Healthcare Text-to-SQL MCP commands\n\n"
	@printf "  make setup           Copy .env.example to .env if missing\n"
	@printf "  make build           Build MCP Docker image\n"
	@printf "  make build-frontend  Build Next.js frontend image\n"
	@printf "  make up              Start PostgreSQL\n"
	@printf "  make frontend        Start Next.js frontend on FRONTEND_PORT\n"
	@printf "  make frontend-logs   Tail frontend logs\n"
	@printf "  make down            Stop Docker services\n"
	@printf "  make ps              Show Docker services\n"
	@printf "  make logs            Tail PostgreSQL logs\n"
	@printf "  make db-shell        Open psql shell as admin user\n"
	@printf "  make check-tables    Check imported table row counts\n"
	@printf "  make sample-queries  Run sample SQL queries\n"
	@printf "  make verify-joins    Verify important joins\n"
	@printf "  make mcp             Run MCP server over stdio via Docker Compose\n"
	@printf "  make eval            Run Text-to-SQL evaluation in Docker\n"
	@printf "  make eval-generated  Run Docker eval with outputs/generated_sql.jsonl\n"
	@printf "  make test-rbac       Smoke test table/column permission rules\n"
	@printf "  make local-eval      Run Text-to-SQL evaluation locally\n"
	@printf "  make clean           Remove stopped containers for this compose project\n"
	@printf "  make reset-db        Stop services and delete PostgreSQL volume\n"

setup:
	@test -f .env || cp .env.example .env

build:
	$(COMPOSE) build $(MCP_SERVICE) $(EVAL_SERVICE)

build-frontend:
	$(COMPOSE) build $(FRONTEND_SERVICE)

up:
	$(COMPOSE) up -d $(POSTGRES_SERVICE)

frontend:
	$(COMPOSE) up -d $(POSTGRES_SERVICE)
	$(COMPOSE) --profile frontend up -d $(FRONTEND_SERVICE)

frontend-logs:
	$(COMPOSE) logs -f $(FRONTEND_SERVICE)

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f $(POSTGRES_SERVICE)

db-shell:
	$(COMPOSE) exec $(POSTGRES_SERVICE) psql -U healthcare_user -d healthcare

check-tables:
	$(COMPOSE) exec -T $(POSTGRES_SERVICE) psql -U healthcare_user -d healthcare < database/scripts/check_tables.sql

sample-queries:
	$(COMPOSE) exec -T $(POSTGRES_SERVICE) psql -U healthcare_user -d healthcare < database/scripts/sample_queries.sql

verify-joins:
	$(COMPOSE) exec -T $(POSTGRES_SERVICE) psql -U healthcare_user -d healthcare < database/scripts/verify_joins.sql

mcp:
	$(COMPOSE) run --rm -T $(MCP_SERVICE)

eval:
	$(COMPOSE) run --rm $(EVAL_SERVICE) python scripts/evaluate_text_to_sql.py --user-id admin

eval-generated:
	$(COMPOSE) run --rm $(EVAL_SERVICE) python scripts/evaluate_text_to_sql.py --user-id admin --generated-file outputs/generated_sql.jsonl

test-rbac:
	$(COMPOSE) run --rm $(EVAL_SERVICE) python -c "import sys; sys.path.append('/app/mcp_server'); from permissions import can_read_sql; tests=[('staff','SELECT ssn FROM patients'),('staff','SELECT * FROM patients'),('admin','SELECT * FROM patients'),('user','SELECT * FROM patients'),('user','SELECT COUNT(*) FROM encounters')]; [print(t, can_read_sql(*t)) for t in tests]"

local-eval:
	python3 scripts/evaluate_text_to_sql.py --user-id admin

clean:
	$(COMPOSE) rm -f

reset-db:
	$(COMPOSE) down -v
