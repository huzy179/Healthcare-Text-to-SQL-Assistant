COMPOSE ?= docker compose
MCP_SERVICE ?= mcp-server
POSTGRES_SERVICE ?= postgres
EVAL_SERVICE ?= eval

.PHONY: help setup build up down ps logs db-shell check-tables sample-queries verify-joins mcp eval local-eval clean reset-db

help:
	@printf "Healthcare Text-to-SQL MCP commands\n\n"
	@printf "  make setup           Copy .env.example to .env if missing\n"
	@printf "  make build           Build MCP Docker image\n"
	@printf "  make up              Start PostgreSQL\n"
	@printf "  make down            Stop Docker services\n"
	@printf "  make ps              Show Docker services\n"
	@printf "  make logs            Tail PostgreSQL logs\n"
	@printf "  make db-shell        Open psql shell as admin user\n"
	@printf "  make check-tables    Check imported table row counts\n"
	@printf "  make sample-queries  Run sample SQL queries\n"
	@printf "  make verify-joins    Verify important joins\n"
	@printf "  make mcp             Run MCP server over stdio via Docker Compose\n"
	@printf "  make eval            Run Text-to-SQL evaluation in Docker\n"
	@printf "  make local-eval      Run Text-to-SQL evaluation locally\n"
	@printf "  make clean           Remove stopped containers for this compose project\n"
	@printf "  make reset-db        Stop services and delete PostgreSQL volume\n"

setup:
	@test -f .env || cp .env.example .env

build:
	$(COMPOSE) build $(MCP_SERVICE)

up:
	$(COMPOSE) up -d $(POSTGRES_SERVICE)

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
	$(COMPOSE) run --rm $(EVAL_SERVICE)

local-eval:
	python3 scripts/evaluate_text_to_sql.py

clean:
	$(COMPOSE) rm -f

reset-db:
	$(COMPOSE) down -v
