import django.dispatch
from django.core.files.storage import default_storage

def sanitize_string(data):
    return re.sub('\s+', '-', data)

def process_datetime_string(date_str):
    ret = parse_datetime(date_str)
    # make timezone aware if not aware
    if not is_aware(ret):
        ret = make_aware(ret)
    return ret

def extract_archive_file(file_instance):
    from zipfile38 import ZipFile
    with ZipFile(file_instance, 'r') as zip_ref:
        zip_ref.extractall('extract')

def archive_upload_post_save(sender, instance, created, *args, **kwargs):

    # Guard against duplicate signal delivery?
    if not instance.completed:
        archive = instance.file
        try:
            data = json.load(json_file)

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
                    explanation = question['Explanation'] if 'Explanation' in question else None,
                    answer_order = sanitize_string(question['AnswerOrder']) if 'AnswerOrder' in question and question['AnswerOrder'] != "" else 'none',
                )

                # Get image relative dir.
                # Put on filesystem with shutil

                if 'Image' in question and isinstance(question['Image'], list):
                    image_loc = path_join(*question['Image'])
                    if default_storage.exists(image_loc):
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
