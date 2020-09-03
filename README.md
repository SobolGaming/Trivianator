# Trivianator
Django-based Trivia Quiz Framework

# Features of this Dockerized Setup
* Uses ASGI so that it can be extended to support websocket/Channels (at a later
   date)
* Has support built in to turn on celery for background tasks and long duration
  work in response to web requests (at later date)
* Has examples of apache and nginx included that are roughly setup to support
  easier integration into an existing environment
* Automatically minimizes static files in develop/local mode.

# To Be Done
* Minify files for production
* Add OAuth Google-supported User Credentials

# Dependencies
This is a Docker-based Django framework. Please make sure you have Docker and
docker-compose installed.

# Running in Local/Development

In the development build docker is configured to load your local files directly
from this directory.  It is live mounted and is not baked into the docker image.
Django has file modification detection and will automatically reload itself if
it sees files change.  This works in general but will fail to execute changes in
`__init__.py` files.

Django will also automatically `makemigrations` and `migrate` for you when you
bring the stack up to try to keep the dev cycle quick.

The development stack supports serving the files itself and allows plain HTTP
for easy testing.

Email output is handled by a local mailhog instance that will print emails to
stdout.  If you need to view it, simply have the docker output for the entire
compose stack up or specifically run `docker logs` on the mailhog container.

If you need to quickly clear the entire database to start over then follow
[this](#clear-development-db)


1) #### Django Compose file Customization

   * (Unnecessary) Edit the `local.yml` file to suite your setup if you feel
     like it.
   * (Unnecessary) Enable or disable additional containers if you feel like it
     (apache/nginx perhaps)
   * (Unnecessary) Remap ports if you feel like it

2) #### Django & Postgres Env Customization

   * Edit the `.envs/.local` file to suite your setup.
   * If accessing from anything other than the `localhost`: Configure the
     `ALLOWED_HOSTS` and `INTERNAL_IPS` to match your setup (to show you debug
     traces when bad things happen in the webpage)

3) #### Actually deploy

   * `docker-compose -f local.yml up --build`
   * When complete, your site will be hosted on `127.0.0.1:8000`

4) Check out [First Steps](#first-steps-after-running)

## Running in Production

The production setup of django is setup to support running behind a standalone
web server.  It is generally setup to be more secure and to refuse non ssl
connections etc.

For Standalone webserver deployment, example configurations for apache and nginx
are provided in docker compose recipes `compose/production/<nginx or apache>` so
that you can copy it and configure similarly.  You WILL NEED to modify them to
fit your particular environment.  The examples do NOT include ssl customization

### Production Checklist
1) #### Volume Preparation

   Create the external volume mounts so that your existing standalone Apache or
   nginx can reach static files

   NOTE: below are for a Linux OS, please adjust for Windows (you will probably
   want to use WSL or WSL 2).

   * `mkdir /opt/mediafiles`
   * `mkdir /opt/staticfiles`
   * `chmod /opt/staticfiles to writeable `
   * `chmod /opt/mediafiles`
   * `docker volume create -o type=none -o o=bind -o device=/opt/staticfiles static_files_data`
   * `docker volume create -o type=none -o o=bind -o device=/opt/mediafiles media_files_data`

   If you would like to change the staticfiles or mediafiles location then you
   will need to [update the compose files](#django-compose-file-customization),
   and the docker volume create command. The containers themselves should still
   be fine.

2) #### Django Compose file Customization

   * Edit the `production.yml` file to suite your setup.
   * Enable or disable additional containers
   * Remap ports as you desire

3) #### Django & Postgres Env Customization

   * Edit the `.envs/.production` file to suite your setup.
   * You will need to understand some Django configuration to setup options.
   * Specifically setup the usernames and passwords BEFORE you `makemigrations`
     and `migrate`
   * Edit `trivianator/contrib/sites/migrations/0003_*` to set the domain correctly
     * Generally replace the placeholder `quiz.ashesofcreation.wiki` with the
       correct hostname in the entire codebase
   * Specifically ideally change all the security options to True
   * Configure the `ALLOWED_HOSTS` to match your setup (proxy server etc)
   * Configure email stuff.  This will depend on how you expect to send email or
     currently do.

4) #### Actually deploy

   * `DJANGO_SELF_HOST=<selfhostip> docker-compose -f production.yml up --build`
   * When complete, your site will be hosted on `<Host Running Docker>:8000`

5) #### Makemigrations and migrate if there are Model Changes (Or First Time)

   * Follow [this](#how-to-perform-migrations-in-production)

6) Check out [First Steps](#first-steps-after-running)

If you feel like experimenting with a dockerized example of a production apache
or nginx setup (serving static files for django, etc NOT SECURITY) You may add
the apache and nginx servers in to the `production.yml` and use the
`.envs/.insecure.production` file to see an example of "production".  It does
not configure SSL.

## First Steps after Running

1) Create a super user
   * Run `python manage.py createsuperuser` following
     [this](#how-to-perform-management-commands-in-docker)
2) Upload quizzes for users to take
   * Login to the [admin page](#urls-of-note) with the superuser/admin
   * navigate to the quiz_uploads (TBD INSTRUCTIONS)
   * Add the *.tgz file containing the quiz you wish to upload

## FAQ

### How to perform management commands in docker

* `docker exec -it <CONTAINER_ID> /bin/bash`
* `source /entrypoint` to set DATABASE_URL and CELERY_BROKER_URL
* perform actual command `python management.py <commandargs>`

### How to perform model migrations in production

* Same as [above](#how-to-perform-management-commands-in-docker)
* For the commands:
  * `python management.py makemigrations`
  * `python management.py migrate`

### URLs of note

* `http://server:8000/admin` admin interface for superusers (could be at a different URL in `production`)

This is specified in `.envs/.production/.django` with `DJANGO_ADMIN_URL`
parameter

* `http://server:8000/` landing page and list all available quizzes for a user
* `http://server:8000/marking/` lists results of users for each quiz (for admins)
* `http://server:8000/progress/` lists all quizzes taken by the user
and their result
* `http://server:8000/leaderboards/` lists all available leaderboards
* `http://server:8000/category/` lists all quiz/question related
categories
* `http://server:8000/<FriendlyURL>` direct URL to a quiz identified by
the friendly URL set when creating the quiz

### How to add Quizzes

* Log into `http://server:8000/admin`

**NOTE**: The actual URL for `/admin/` should be different for `production` as
it should be a long unique URL for security reasons.

This is specified in `.envs/.production/.django` with `DJANGO_ADMIN_URL`
parameter

### Clear development db

* Run `docker-compose -f local.yml down -v`

This will clear all docker internal volumes including the postgres database.
The django docker image start script automatically will recreate the tables when
it connects with `migrate`

### Clear migrations to start from scratch

rm -rf all the `000*` files in any migrations folders of the trivia app or other
self created apps.  Do not touch the `trivianator/contrib/sites/migrations`
folder unless you know what you are doing.

### General Help links

* https://cookiecutter-django.readthedocs.io/en/latest/index.html
* https://docs.djangoproject.com/en/3.1/
