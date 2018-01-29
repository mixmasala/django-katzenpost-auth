serve:
	cd katzenauth && hx start --dev
collect:
	cd katzenauth && ./manage.py collectstatic
init:
	sudo mkdir -p /opt/katzenauth/static/
migrations:
	cd katzenauth && ./manage.py makemigrations && ./manage.py makemigrations katzen && ./manage.py migrate
destroydb:
	rm katzenauth/db.sqlite3
	rm -rf katzenauth/katzen/migrations
createadmin:
	cd katzenauth && ./manage.py createsuperuser
startfresh: destroydb migrations createadmin
