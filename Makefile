run:
	poetry shell
	draft
clean:
	find . | grep -E "(__pycache__|\.pyc|.pytest_cache)" | xargs rm -rf
reset: clean
	rm -rf config/
test:
	# Should be called from the base-directory of the project.
	poetry run pytest -v

