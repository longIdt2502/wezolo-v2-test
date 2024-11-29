postgres:
	docker run --name postgres --network bank-network -p 5432:5432 -e POSTGRES_USER=root -e POSTGRES_PASSWORD=localhost1234 -d postgres

createdb:
	docker exec -it postgres createdb --username=root --owner=root wezolo

dropdb:
	docker exec -it postgres dropdb wezolo

runserver:
	python manage.py makemigrations && python manage.py migrate && python manage.py insert_data && python manage.py init_reward_tier && python manage.py init_package && python manage.py init_role && python manage.py init_price && python manage.py init_benefit && python manage.py runserver 0.0.0.0:8000