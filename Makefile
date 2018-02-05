shell:
	docker-compose run --rm python sh

.PHONY: python
python:
	docker-compose run --rm python python

environment:
	docker-compose build

clean:
	docker-compose down
	rm -rf .pytest_cache .coverage __pycache__ python/__pycache__

.PHONY: tests
tests:
	docker-compose run --rm python pytest --cov=index tests
