.PHONY: install test validate-dataset compile ingest run-baseline run-rag run-agent api phoenix pilot lint

install:
	cp -n .env.example .env || true
	uv sync --extra dev --extra evals

test:
	uv run pytest tests/unit -q

test-integration:
	uv run pytest tests/integration -q -m integration

validate-dataset:
	uv run python scripts/validate_dataset.py evals/datasets/dev.jsonl

compile:
	uv run python -m compileall -q src scripts apps tests

ingest:
	uv run python scripts/ingest_knowledge.py

run-baseline:
	uv run python scripts/run_experiment.py --mode baseline \
		--dataset evals/datasets/dev.jsonl \
		--output artifacts/runs/baseline_v1.jsonl

run-rag:
	uv run python scripts/run_experiment.py --mode rag \
		--dataset evals/datasets/dev.jsonl \
		--output artifacts/runs/rag_v1.jsonl

run-agent:
	uv run python scripts/run_agent_experiment.py \
		--dataset evals/datasets/dev.jsonl \
		--output artifacts/runs/agent_v1.jsonl

api:
	uv run uvicorn strideguard.api:app --reload

phoenix:
	docker compose -f docker-compose.phoenix.yml up -d

pilot:
	uv run streamlit run apps/pilot_app.py

lint:
	uv run ruff check src scripts apps tests
