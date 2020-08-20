# Trivianator
Django-based Trivia Quiz Framework

# Instructions

1) ### Installation
  Make sure to have python version 3 install on you pc or laptop.
  If not install it from [here](https://www.python.org) <br>
  **Clone repository** <br>
  `https://github.com/SobolGaming/Trivianator.git`<br>
  `cd Trivianator`

2) ### Dependencies
  This is a Docker-based Django framework. Please make sure you have Docker installed.

3) ### Docker Build
  The following commands builds all the docker containers and then instantiates them for a running system.<br>
  `docker-compose -f local.yml up` <br>
  When complete, your site will be hosted on `http://127.0.0.1:8000`

4) ### Running Django Management Commands
  To run any `python manage.py <CMD>` like you would typically, you need to:<br>
    Find the django container ID using: `docker ps` <br>
    Enter the django container using: `docker exec -it <CONTAINER_ID> /bin/bash` <br>
    Load the environment variables indicating the DB setup attached to Django using: <br>
      `set -a` <br>
      `source django.env` <br>
      `set +a` <br>
    Run the command: `python manage.py <CMD>`

5) ### Useful Commands when getting started
  Once system is up and running create a superuser:<br>
    `docker-compose -f .\local.yml run --rm django python manage.py createsuperuser`<br>
  Log into the administrative trivia site to create quizes and questions using above created account:<br>
    `http://127.0.0.1:8000/admin/trivia`<br>
  If you ever modify the data_type of existing model fields you will need to edit the Postgres DB for it to work.<br>
  During development you can just `docker-compose -f .\local.yml down -v`. Adding the `-v` deletes the volume and wipes the DB.<br>
  In production you would need to `django python manage.py makemigrations` and `django python manage.py migrate`.

6) ### URLs of note
  `http://127.0.0.1:8000/trivia/quizzes/` lists all available quizzes<br>
  `http://127.0.0.1:8000/trivia/marking/` lists results of users for each quiz (for admins)<br>
  `http://127.0.0.1:8000/trivia/progress/` lists all quizzes taken by the user and their result<br>
  `http://127.0.0.1:8000/trivia/category/` lists all quiz/question related categories<br>
  `http://127.0.0.1:8000/trivia/<FriendlyURL>` direct URL to a quiz identified by the friendly URL set when creating the quiz
