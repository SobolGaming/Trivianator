import django.dispatch
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.dateparse import parse_datetime
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from tarfile import TarFile
from pathlib import Path
import tempfile
import shutil
import os
import json
import re
from trivianator.trivia.models import Category, Quiz, Question, Answer
from django.utils.timezone import now, timedelta, is_aware, make_aware
from os.path import join as path_join

def sanitize_string(data):
    return re.sub('\s+', '-', data)

def process_datetime_string(date_str):
    ret = parse_datetime(date_str)
    # make timezone aware if not aware
    if not is_aware(ret):
        ret = make_aware(ret)
    return ret

def extract_archive(archive_file, sub_dir):
    """
    Extract the archive and return JSON file.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tdir = Path(tmpdir)
        # Extract the archive
        tar = TarFile.open(fileobj=archive_file)
        tar.extractall(str(tdir))
        tar.close()

        return handle_media_files(tdir, sub_dir)
    return None

def handle_media_files(tmpdir, subdir):
    """
    Import all uploaded media from the archive.
    """
    mediaroot = Path(getattr(settings, 'MEDIA_ROOT'))
    if not os.path.isdir(str(mediaroot)): os.mkdir(str(mediaroot))
    image_dest = path_join(mediaroot, subdir, '')
    os.makedirs(os.path.dirname(image_dest), exist_ok=True)

    for name in tmpdir.glob('images/*'):
        # print('Trying to copy {} to {}'.format(str(name),image_dest))
        shutil.copy2(name, image_dest)

    for name in tmpdir.glob('*.json'):
        # print('Trying to copy {} to {}'.format(str(name),image_dest))
        shutil.copy2(name, image_dest)
        return image_dest+os.path.basename(name)

def archive_upload_post_save(sender, instance, created, *args, **kwargs):
    if not instance.completed:
        archive = instance.file
        # extract the archive
        # move all the images in media directory
        # returns JSON quiz file
        _, file_name = os.path.split(archive.name)
        sub_dir, _ = os.path.splitext(file_name)
        sub_dir = sub_dir.lower()
        json_file = extract_archive(archive, sub_dir)

        if not json_file:
            raise Exception("Invalid JSON File.")

        try:
            data = json.load(open(json_file, "r"))

            # Create quiz
            quiz_cat = Category.objects.get_or_create(category=sanitize_string(data['Quiz']['Category']).lower()) if 'Category' in data['Quiz'] and data['Quiz']['Category'] != None else (None, False)

            quiz = Quiz.objects.create(
                title = sanitize_string(data['Quiz']['Title']),
                url = sanitize_string(data['Quiz']['URL']).lower(),
                category = quiz_cat[0],
                random_order = data['Quiz']['RandomOrder'] if 'RandomOrder' in data['Quiz'] else False,
                max_questions = data['Quiz']['MaxQuestions'] if 'MaxQuestions' in data['Quiz'] else None,
                answers_reveal_option = min(max(data['Quiz']['AnswerRevealOption'], 1), 3) if 'AnswerRevealOption' in data['Quiz'] else 1,
                saved = data['Quiz']['Save'] if 'Save' in data['Quiz'] else True,
                single_attempt = data['Quiz']['SingleAttempt'] if 'SingleAttempt' in data['Quiz'] else False,
                draft = data['Quiz']['Draft'] if 'Draft' in data['Quiz'] else False,
                message = data['Quiz']['Message'] if 'Message' in data['Quiz'] and data['Quiz']['Message'] != '' else None,
                num_display = data['Quiz']['DisplayCount'] if 'DisplayCount' in data['Quiz'] and data['Quiz']['DisplayCount'] >= 0 else 30,
                timer = max(0, data['Quiz']['Timer']) if 'Timer' in data['Quiz'] else 0,
                show_leaderboards = data['Quiz']['Leaderboards'] if 'Leaderboards' in data['Quiz'] else True,
                competitive = data['Quiz']['Competitive'] if 'Competitive' in data['Quiz'] else False,
                start_time = process_datetime_string(data['Quiz']['StartTime']) if 'StartTime' in data['Quiz'] else now() + timedelta(minutes=5),
                end_time = process_datetime_string(data['Quiz']['EndTime']) if 'EndTime' in data['Quiz'] else now() + timedelta(hours=1, minutes=5),
            )

            # Create questions
            for question in data['Quiz']['Questions']:
                q_cat = Category.objects.get_or_create(category=sanitize_string(question['Category']).lower()) if 'Category' in question and question['Category'] != "" else (None, False)

                q = Question.objects.create(
                    question_type = question['QuestionType'].lower(),
                    category = q_cat[0],
                    content = question['Content'],
                    explanation = question['Explanation'] if 'Explanation' in question else "",
                    answer_order = sanitize_string(question['AnswerOrder']) if 'AnswerOrder' in question and question['AnswerOrder'] != "" else 'none',
                )

                # Get image relative dir.
                # Put on filesystem with shutil

                if 'Image' in question:
                    image_loc = path_join(sub_dir, question['Image'])
                    # print("Checking Image File Existance: ", image_loc)
                    if default_storage.exists(image_loc):
                        # print("Setting Questions Figure")
                        q.figure = image_loc
                        q.save()

                for answer in question['Answers']:
                    Answer.objects.create(
                        question = q,
                        content = answer['Content'],
                        correct = True if answer['Correct'] == 1 else False,
                    )
                # add each question to the quiz parent, can't set direcly as other parameters since it's a ManyToMany parameter
                q.quiz.add(quiz)

            instance.completed = True
            instance.save()
        except ValueError as err:
            raise err

@receiver(pre_delete, sender=Quiz)
def pre_delete_quiz(sender, instance, **kwargs):
    for question in instance.get_questions():
        if question.quiz.count() == 1 and instance in question.quiz.all():
            # instance is the only Quiz that has this Question, delete it
            question.delete()
