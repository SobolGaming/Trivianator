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
    Enter the django container using: `docker exec -t <CONTAINER_ID> /bin/bash` <br>
    Load the environment variables indicating the DB setup attached to Django using: <br>
      `set -a` <br>
      `source django.env` <br>
      `set +a` <br>
    Run the command: `python manage.py <CMD>`

