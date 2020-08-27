# Trivianator
Django-based Trivia Quiz Framework

# Instructions

1) ### Dependencies
   This is a Docker-based Django framework. Please make sure you have Docker installed.

2) ### Preparation
   Create the external volume mounts so that your existing Apache or nginx can reach static files

   NOTE: below are for a Linux OS, please adjust for Windows (you will probably want to use WSL or WSL 2).
   * `mkdir /opt/mediafiles`
   * `mkdir /opt/staticfiles`
   * `chmod /opt/staticfiles`
   * `chmod /opt/mediafiles`
   * `docker volume create -o type=none -o o=bind -o device=/opt/staticfiles static_files_data`
   * `docker volume create -o type=none -o o=bind -o device=/opt/mediafiles media_files_data`

3) ### Docker Build
   The following command builds all the docker containers and then instantiates them for a running system.

      **Locally**: `docker-compose -f local.yml up`

      When complete, your site will be hosted on `http://127.0.0.1:8000`

      **Production**: `docker-compose -f production.yml up`

      When complete, your site will be hosted on `<one of the DJANGO_ALLOWED_HOSTS>:8000`

4) ### Running Django Management Commands
   To run any `python manage.py <CMD>` like you would typically, you need to:

   Find the django container ID using: `docker ps`

   Enter the django container using: `docker exec -it <CONTAINER_ID> /bin/bash`

   Source the entrypoint file: `source /entrypoint`

   Run the command: `python manage.py <CMD>`

5) ### For production standup
   In production you would need to `django python manage.py makemigrations` and `django python manage.py migrate` in the docker container

   NOTE: in `local development` this gets run automatically as part of docker-compose; not for `production` though.

6) ### Useful Commands when getting started
   Once system is up and running create a superuser:

      Local Dev:

         `docker-compose -f .\local.yml run --rm django python manage.py createsuperuser`

      Production Dev:

         `docker-compose -f .\production.yml run --rm django python manage.py createsuperuser`

   Log into the administrative trivia site to create quizes and questions using above created account:

      `http://127.0.0.1:8000/admin/`

      NOTE: the actual URL for `/admin/` should be different for `production` as it should be a long unique URL for sercurity reasons.

      this is specified in `.envs/.production/.django` with `DJANGO_ADMIN_URL` parameter
      
   If you ever modify the data_type of existing model fields you will need to edit the Postgres DB for it to work.

   During development you can just `docker-compose -f .\local.yml down -v`. Adding the `-v` deletes the volume and wipes the DB.

   In production you would need to `django python manage.py makemigrations` and `django python manage.py migrate`.

7) ### URLs of note
   `http://127.0.0.1:8000/` lists all available quizzes

   `http://127.0.0.1:8000/trivia/marking/` lists results of users for each quiz (for admins)

   `http://127.0.0.1:8000/trivia/progress/` lists all quizzes taken by the user and their result

   `http://127.0.0.1:8000/trivia/category/` lists all quiz/question related categories

   `http://127.0.0.1:8000/trivia/<FriendlyURL>` direct URL to a quiz identified by the friendly URL set when creating the quiz
