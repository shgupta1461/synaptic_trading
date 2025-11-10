run:
	uvicorn src.main:app --reload

test:
	pytest -v --maxfail=1 --disable-warnings


phase2-l1l2:
	python -m src.phase2_l1_l2
