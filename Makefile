install:
	python -m pip install -U pip && pip install -e .

dev:
	python src/agent.py dev

start:
	python src/agent.py start