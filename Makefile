COMPOSE ?= docker compose
DOCKER_DESKTOP_COMPOSE ?= '/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe' compose
MCP_SERVICE ?= mcp-server
POSTGRES_SERVICE ?= postgres
EVAL_SERVICE ?= eval
FRONTEND_SERVICE ?= frontend
VLLM_SERVICE ?= vllm

.PHONY: help setup env-check build build-frontend dev frontend recreate-frontend frontend-vllm frontend-logs vllm vllm-logs health docker-desktop-up docker-desktop-health up down ps logs db-shell check-tables sample-queries verify-joins mcp eval eval-gold generate-sql eval-generated eval-llm docker-desktop-eval-llm test-rbac local-eval clean reset-db

help:
	@printf "Healthcare Text-to-SQL MCP commands\n\n"
	@printf "Main:\n"
	@printf "  make setup              Create .env if missing\n"
	@printf "  make dev                Start PostgreSQL, vLLM, and frontend\n"
	@printf "  make recreate-frontend  Recreate frontend after .env/code changes\n"
	@printf "  make health             Smoke test schema and DB query path\n"
	@printf "  make down               Stop services\n\n"
	@printf "Docker Desktop / WSL:\n"
	@printf "  make docker-desktop-up      Start dev stack via docker.exe\n"
	@printf "  make docker-desktop-health  Run health check via docker.exe\n\n"
	@printf "Logs:\n"
	@printf "  make ps                 Show services\n"
	@printf "  make frontend-logs      Tail frontend logs\n"
	@printf "  make vllm-logs          Tail vLLM logs\n"
	@printf "  make logs               Tail PostgreSQL logs\n\n"
	@printf "Build/Test:\n"
	@printf "  make build              Build MCP/eval image\n"
	@printf "  make build-frontend     Build frontend image\n"
	@printf "  make check-tables       Check imported table row counts\n"
	@printf "  make eval-gold          Validate reference SQL, DB, and validator\n"
	@printf "  make eval-llm           Generate SQL with vLLM, then evaluate it\n"
	@printf "  make test-rbac          Smoke test table/column permission rules\n"

setup:
	@test -f .env || cp .env.example .env
	@$(MAKE) env-check

env-check:
	@test -f .env
	@grep -q '^LLM_BASE_URL=' .env
	@grep -q '^LLM_API_KEY=' .env
	@grep -q '^LLM_MODEL=' .env
	@grep -q '^VLLM_MODEL=' .env
	@printf ".env looks ready for local vLLM\n"

build:
	$(COMPOSE) build $(MCP_SERVICE) $(EVAL_SERVICE)

build-frontend:
	$(COMPOSE) build $(FRONTEND_SERVICE)

up:
	$(COMPOSE) up -d $(POSTGRES_SERVICE)

dev: frontend-vllm

frontend:
	$(COMPOSE) up -d $(POSTGRES_SERVICE)
	$(COMPOSE) --profile frontend up -d $(FRONTEND_SERVICE)

recreate-frontend:
	$(COMPOSE) --profile frontend --profile vllm up -d --force-recreate $(FRONTEND_SERVICE)

vllm:
	$(COMPOSE) --profile vllm up -d $(VLLM_SERVICE)

vllm-logs:
	$(COMPOSE) logs -f $(VLLM_SERVICE)

frontend-vllm:
	$(COMPOSE) up -d $(POSTGRES_SERVICE)
	$(COMPOSE) --profile vllm up -d $(VLLM_SERVICE)
	$(COMPOSE) --profile frontend --profile vllm up -d $(FRONTEND_SERVICE)

frontend-logs:
	$(COMPOSE) logs -f $(FRONTEND_SERVICE)

health:
	$(COMPOSE) ps
	$(COMPOSE) exec $(FRONTEND_SERVICE) node -e "fetch('http://127.0.0.1:3000/api/schema?userId=admin').then(r=>r.json()).then(j=>{if(!j.prompt_rules||!j.tables){process.exit(1)}; console.log('schema ok:', Object.keys(j.tables).length, 'tables')})"
	$(COMPOSE) exec $(FRONTEND_SERVICE) node -e "fetch('http://127.0.0.1:3000/api/query',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({mode:'sql',userId:'admin',sql:'SELECT gender, COUNT(*) AS total FROM patients GROUP BY gender ORDER BY total DESC'})}).then(r=>r.json()).then(j=>{if(!j.ok){console.error(j.error);process.exit(1)}; console.log('query ok:', JSON.stringify(j.rows))})"

docker-desktop-up:
	$(MAKE) COMPOSE="$(DOCKER_DESKTOP_COMPOSE)" frontend-vllm

docker-desktop-health:
	$(MAKE) COMPOSE="$(DOCKER_DESKTOP_COMPOSE)" health

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

eval: eval-gold

eval-gold:
	$(COMPOSE) run --rm $(EVAL_SERVICE) python scripts/evaluate_text_to_sql.py --mode gold --user-id admin --output-file reports/text_to_sql_gold_results.jsonl --summary-file reports/text_to_sql_gold_summary.md

generate-sql:
	$(COMPOSE) --profile vllm up -d $(VLLM_SERVICE)
	$(COMPOSE) run --rm $(EVAL_SERVICE) python scripts/generate_text_to_sql.py --user-id admin --output-file outputs/generated_sql.jsonl

eval-generated:
	$(COMPOSE) run --rm $(EVAL_SERVICE) python scripts/evaluate_text_to_sql.py --mode generated --user-id admin --generated-file outputs/generated_sql.jsonl --output-file reports/text_to_sql_llm_results.jsonl --summary-file reports/text_to_sql_llm_summary.md

eval-llm: generate-sql eval-generated

docker-desktop-eval-llm:
	$(MAKE) COMPOSE="$(DOCKER_DESKTOP_COMPOSE)" eval-llm

test-rbac:
	$(COMPOSE) run --rm $(EVAL_SERVICE) python -c "import sys; sys.path.append('/app/mcp_server'); from permissions import can_read_sql; tests=[('staff','SELECT ssn FROM patients'),('staff','SELECT * FROM patients'),('admin','SELECT * FROM patients'),('user','SELECT * FROM patients'),('user','SELECT COUNT(*) FROM encounters')]; [print(t, can_read_sql(*t)) for t in tests]"

local-eval:
	python3 scripts/evaluate_text_to_sql.py --mode gold --user-id admin

clean:
	$(COMPOSE) rm -f

reset-db:
	$(COMPOSE) down -v
