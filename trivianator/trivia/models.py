import json
import re
from django.db import models
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import MaxValueValidator, validate_comma_separated_integer_list
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, timedelta, is_aware, make_aware
from django.conf import settings
from model_utils.managers import InheritanceManager
from django.utils.translation import ugettext as _
from .signals import json_uploaded
from .validators import json_file_validator
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User

# Create your models here.
QUESTION_TYPES = (
    ('single_choice', _("Single correct answer")),
    ('multi_choice', _("Multiple correct answers")),
)

ANSWER_ORDER_OPTIONS = (
    ('none', _('None')),
    ('content', _('Content')),
    ('random', _('Random')),
)

ANSWER_REVEAL_OPTIONS = (
    (1, _("After each question")),
    (2, _("At end of quiz")),
    (3, _("Never")),
)

class CategoryManager(models.Manager):

    def new_category(self, category):
        new_category = self.create(category=re.sub('\s+', '-', category)
                                   .lower())

        new_category.save()
        return new_category


class Category(models.Model):

    category = models.CharField(
        verbose_name=_("Category"),
        max_length=250, blank=True,
        unique=True, null=True)

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category


class Quiz(models.Model):

    title = models.CharField(
        verbose_name=_("Title"),
        max_length=60, blank=False)

    url = models.SlugField(
        max_length=60, blank=False,
        help_text=_("a user friendly url"),
        verbose_name=_("user friendly url"))

    category = models.ForeignKey(
        Category, null=True, blank=True,
        verbose_name=_("Category"), on_delete=models.CASCADE)

    random_order = models.BooleanField(
        blank=False, default=False,
        verbose_name=_("Random Order"),
        help_text=_("Display the questions in a random order or as they are set?"))

    max_questions = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Max Questions"),
        help_text=_("Number of questions to be answered on each attempt."))

    answers_reveal_option = models.PositiveSmallIntegerField(
        blank=False, default=1, choices = ANSWER_REVEAL_OPTIONS,
        help_text=_("Determines when correct answers are revealed for each question."),
        verbose_name=_("Answers Reveal Option"))

    saved = models.BooleanField(
        blank=True, default=True,
        help_text=_("If yes, the result of each attempt by a user will be saved."),
        verbose_name=_("Saved"))

    single_attempt = models.BooleanField(
        blank=False, default=False,
        help_text=_("If yes, only one attempt by a user will be permitted."
                    " Non users cannot sit this quiz."),
        verbose_name=_("Single Attempt"))

    draft = models.BooleanField(
        blank=True, default=False,
        verbose_name=_("Draft"),
        help_text=_("If yes, the quiz is not displayed in the quiz list and can only be"
                    " taken by users who can edit quizzes."))

    timer = models.PositiveSmallIntegerField(blank=True, default=0,
        verbose_name=_("Quiz Timer"),
        help_text=_("If > 0, amount of seconds allowed to complete the quiz."))

    show_leaderboards = models.BooleanField(blank=True, default=True,
        verbose_name=_("Show Leaderboards"),
        help_text=_("Boolean if leaderboards should be displayed after quiz completion."))

    competitive = models.BooleanField(blank=True, default=False,
        verbose_name=_("Competitive"),
        help_text=_("Boolean if this quiz is competitive. If 'True' it disables "
                    "displaying results of the quiz or of the leaderboards, although "
                    "leaderboard data is collected. Requires 'StartTime' and 'EndTime' "
                    "to be specified."))

    start_time = models.DateTimeField(blank=True, null=True, default=None,
        verbose_name=_("StartTime"),
        help_text=_("Start DateTime of the quiz."))

    end_time = models.DateTimeField(blank=True, null=True, default=None,
        verbose_name=_("EndTime"),
        help_text=_("End DateTime of the quiz."))

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.url = re.sub('\s+', '-', self.url).lower()

        self.url = ''.join(letter for letter in self.url if
                           letter.isalnum() or letter == '-')

        if self.single_attempt is True:
            self.saved = True

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    def anon_score_id(self):
        return str(self.id) + "_score"

    def anon_q_list(self):
        return str(self.id) + "_q_list"

    def anon_q_data(self):
        return str(self.id) + "_data"

    @property
    def get_leaderboard(self):
        return Leaderboard.objects.filter(quiz=self).order_by('-score', 'completion_time')[:30]

    @property
    def end_time_expired(self):
        if self.competitive:
            if now() >= self.end_time:
                return True
            else:
                return False
        return True


# progress manager
class ProgressManager(models.Manager):

    def new_progress(self, user):
        new_progress = self.create(user=user,
                                   score="")
        new_progress.save()
        return new_progress


class Progress(models.Model):
    """
    Progress is used to track an individual signed in user's score on different
    categories across all quizzes.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)

    serialized_performance = models.CharField(validators=[validate_comma_separated_integer_list], max_length=2048,
                                              verbose_name=_("Per Category Performance"))

    objects = ProgressManager()

    class Meta:
        verbose_name = _("User Progress")
        verbose_name_plural = _("User Progress Records")

    @property
    def list_all_cat_scores(self):
        """
        Returns a dict in which the key is the category name and the item is
        a list of three integers.
        The first is the number of questions correct,
        the second is the possible best score,
        the third is the percentage correct.
        The dict will have one key for every category that you have defined
        """
        serialized_performance_before = self.serialized_performance
        output = {}

        for cat in Category.objects.all():
            to_find = re.escape(cat.category) + r",(\d+),(\d+),"
            #  group 1 is score, group 2 is highest possible

            match = re.search(to_find, self.serialized_performance, re.IGNORECASE)

            if match:
                score = int(match.group(1))
                possible = int(match.group(2))

                try:
                    percent = int(round((float(score) / float(possible)) * 100))
                except:
                    percent = 0

                output[cat.category] = [score, possible, percent]

            else:  # if category has not been added yet, add it.
                self.serialized_performance += cat.category + ",0,0,"
                output[cat.category] = [0, 0, 0]

        if len(self.serialized_performance) > len(serialized_performance_before):
            # If a new category has been added, save changes.
            self.save()

        return output

    def update_score(self, question, score_to_add=0, possible_to_add=0):
        """
        Pass in question object, amount to increase score and max possible.
        Does not return anything.
        """
        category_test = Category.objects.filter(category=question.category).exists()

        if any([item is False for item in [category_test,
                                           score_to_add,
                                           possible_to_add,
                                           isinstance(score_to_add, int),
                                           isinstance(possible_to_add, int)]]):
            return _("error"), _("category does not exist or invalid score")

        to_find = re.escape(str(question.category)) + r",(?P<score>\d+),(?P<possible>\d+),"

        match = re.search(to_find, self.serialized_performance, re.IGNORECASE)

        if match:
            updated_score = int(match.group('score')) + abs(score_to_add)
            updated_possible = int(match.group('possible')) +\
                abs(possible_to_add)

            new_score = ",".join(
                [
                    str(question.category),
                    str(updated_score),
                    str(updated_possible), ""
                ])

            # swap old score for the new one
            self.serialized_performance = self.serialized_performance.replace(match.group(), new_score)
            self.save()

        else:
            #  if not present but existing, add with the points passed in
            self.serialized_performance += ",".join(
                [
                    str(question.category),
                    str(score_to_add),
                    str(possible_to_add),
                    ""
                ])
            self.save()

    def show_saved(self):
        """
        Finds the previous quizzes marked as 'saved'.
        Returns a queryset of complete quizzes.
        """
        return Sitting.objects.filter(user=self.user, complete=True)

    def __str__(self):
        return self.user.username + ' - '  + self.serialized_performance


class SittingManager(models.Manager):

    def new_sitting(self, user, quiz):
        if quiz.random_order is True:
            question_set = quiz.question_set.all().select_subclasses().order_by('?')
        else:
            question_set = quiz.question_set.all().select_subclasses()

        question_set = [item.id for item in question_set]

        if len(question_set) == 0:
            raise ImproperlyConfigured('Question set of the quiz is empty. '
                                       'Please configure questions properly')

        if quiz.max_questions and quiz.max_questions < len(question_set):
            question_set = question_set[:quiz.max_questions]

        questions = ",".join(map(str, question_set)) + ","

        new_sitting = self.create(user=user,
                                  quiz=quiz,
                                  question_order=questions,
                                  question_list=questions,
                                  incorrect_questions="",
                                  current_score=0,
                                  complete=False,
                                  start=now(),
                                  user_answers='{}')
        return new_sitting

    def user_sitting(self, user, quiz):
        if quiz.single_attempt is True and self.filter(user=user, quiz=quiz, complete=True).exists():
            return False

        try:
            sitting = self.get(user=user, quiz=quiz, complete=False)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, complete=False)[0]
        return sitting


class Sitting(models.Model):
    """
    Used to store the progress of logged in users sitting a quiz.
    Replaces the session system used by anon users.
    Question_order is a list of integer pks of all the questions in the
    quiz, in order.
    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.
    Incorrect_questions is a list in the same format.
    Sitting deleted when quiz finished unless quiz.saved is true.
    User_answers is a json object in which the question PK is stored
    with the answer the user gave.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"), on_delete=models.CASCADE)

    question_order = models.CharField(validators=[validate_comma_separated_integer_list],
        max_length=1024, verbose_name=_("Question Order"))

    question_list = models.CharField(validators=[validate_comma_separated_integer_list],
        max_length=1024, verbose_name=_("Question List"))

    incorrect_questions = models.CharField(validators=[validate_comma_separated_integer_list],
        max_length=1024, blank=True, verbose_name=_("Incorrect questions"))

    current_score = models.IntegerField(verbose_name=_("Current Score"))

    complete = models.BooleanField(default=False, blank=False,
                                   verbose_name=_("Complete"))

    user_answers = models.TextField(blank=True, default='{}',
                                    verbose_name=_("User Answers"))

    start = models.DateTimeField(auto_now_add=True, verbose_name=_("Start"))

    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    objects = SittingManager()

    class Meta:
        permissions = (("view_sittings", _("Can see completed quizzes.")),)

    def get_first_question(self):
        """
        Returns the next question.
        If no question is found, returns False
        Does NOT remove the question from the front of the list.
        """
        if not self.question_list:
            return False

        first, _ = self.question_list.split(',', 1)
        question_id = int(first)
        return Question.objects.get_subclass(id=question_id)

    def remove_first_question(self):
        if not self.question_list:
            return

        _, others = self.question_list.split(',', 1)
        self.question_list = others
        self.save()

    def add_to_score(self, points):
        self.current_score += int(points)
        self.save()

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(',') if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0            # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()
        self.save()

        # add to leaderboard if quiz was competitive and currently in session
        if self.quiz.competitive and self.quiz.end_time > now() and self.quiz.start_time < now():
            if not Leaderboard.objects.filter(quiz=self.quiz, user=self.user).exists():
                ld = Leaderboard.objects.create(
                    quiz=self.quiz, user=self.user, score=self.current_score, completion_time=(self.end - self.start).seconds
                )

    def add_incorrect_question(self, question):
        """
        Adds uid of incorrect question to the list.
        The question object must be passed in.
        """
        if len(self.incorrect_questions) > 0:
            self.incorrect_questions += ','
        self.incorrect_questions += str(question.id)
        if self.complete:
            self.add_to_score(-1)
        self.save()

    @property
    def get_incorrect_questions(self):
        """
        Returns a list of non empty integers, representing the pk of
        questions
        """
        return [int(q) for q in self.incorrect_questions.split(',') if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ','.join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def result_message(self):
        return _("Thank you for taking the quiz.")

    def add_user_answer(self, question, guess):
        current = json.loads(self.user_answers)
        current[question.id] = guess
        self.user_answers = json.dumps(current)
        self.save()

    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()
        questions = sorted(
            self.quiz.question_set.filter(id__in=question_ids).select_subclasses(),
            key=lambda q: question_ids.index(q.id))

        if with_answers:
            user_answers = json.loads(self.user_answers)
            for question in questions:
                try: 
                    question.user_answer = user_answers[str(question.id)]
                except KeyError:
                    # quiz or question timer expired
                    pass

        return questions

    @property
    def questions_with_user_answers(self):
        return {
            q: q.user_answer for q in self.get_questions(with_answers=True)
        }

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        answered = len(json.loads(self.user_answers))
        total = self.get_max_score
        return answered, total


class Question(models.Model):
    """
    Base class for all question types.
    Shared properties placed here.
    """

    quiz = models.ManyToManyField(Quiz,
                                  verbose_name=_("Quiz"),
                                  blank=True)

    question_type = models.CharField(
                                max_length=30, blank=False,
                                default = 'single_choice',
                                choices = QUESTION_TYPES,
                                help_text=_("The question type."),
                                verbose_name=_("Question Type"))

    category = models.ForeignKey(Category,
                                 verbose_name=_("Category"),
                                 blank=True,
                                 null=True, on_delete=models.CASCADE)

    figure = models.ImageField(upload_to='uploads/%Y/%m/%d',
                               blank=True,
                               null=True,
                               verbose_name=_("Figure"))

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Enter the question text that "
                                           "you want displayed"),
                               verbose_name=_('Question'))

    explanation = models.TextField(max_length=2000,
                                   blank=True,
                                   help_text=_("Explanation to be shown "
                                               "after the question has "
                                               "been answered."),
                                   verbose_name=_('Explanation'))

    timer = models.PositiveSmallIntegerField(blank=True, default=0,
                                             verbose_name=_("Question Timer"),
                                             help_text=_("If > 0, amount of seconds allowed to answer the question."))

    answer_order = models.CharField(max_length=30, blank=False,
                                    default = 'none', choices = ANSWER_ORDER_OPTIONS,
                                    help_text = _("The order in which multichoice "
                                                  "answer options are displayed "
                                                  "to the user"),
                                    verbose_name=_("Answer Order"))

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return self.content

    def check_if_correct_sc(self, guess):
        answer = Answer.objects.get(id=guess)
        if answer.correct is True:
            return True
        else:
            return False

    def check_if_correct_mc(self, guess, choices):
        for choice in choices:
            answer = Answer.objects.get(id=str(choice))
            if answer.correct is True and str(choice) not in guess:
                return False
            if answer.correct is False and str(choice) in guess:
                return False
        return True

    def order_answers(self, queryset):
        if self.answer_order == 'content':
            return queryset.order_by('content')
        elif self.answer_order == 'random':
            return queryset.order_by('?')
        return queryset

    def get_answers(self):
        return self.order_answers(Answer.objects.filter(question=self))

    def get_answers_list(self):
        return [(answer.id, answer.content) for answer in self.order_answers(Answer.objects.filter(question=self))]

    def answer_choice_to_string(self, guess):
        if isinstance(guess, list):
            ret = []
            for elem in guess:
                ret.append(Answer.objects.get(id=elem).content)
            return ret
        else:
            if guess == '':
                return ''
            return Answer.objects.get(id=guess).content


class Answer(models.Model):
    question = models.ForeignKey(Question, verbose_name='Question', on_delete=models.CASCADE)

    content = models.CharField(max_length=1000,
                               blank=False,
                               help_text=_("Enter the answer text that "
                                           "you want displayed"),
                               verbose_name=_("Content"))

    correct = models.BooleanField(blank=False,
                                  default=False,
                                  help_text=_("Is this a correct answer?"),
                                  verbose_name=_("Correct"))

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")


class Leaderboard(models.Model):
    quiz = models.ForeignKey(Quiz, verbose_name='Quiz', on_delete=models.CASCADE)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)

    score = models.PositiveSmallIntegerField(verbose_name=_("Score"))

    completion_time = models.PositiveIntegerField(verbose_name=_("Completion Time"))

    objects = InheritanceManager()

    def __str__(self):
        return self.user.username + "_" + self.quiz.title

    class Meta:
        verbose_name = _("Leaderboard")
        verbose_name_plural = _("Leaderboards")


def upload_json_file(instance, filename):
    qs = instance.__class__.objects.filter(user=instance.user)
    if qs.exists():
        num_ = qs.last().id + 1
    else:
        num_ = 1
    return f'json_files/{num_}/{instance.user.username}/{filename}'


class JSONUpload(models.Model):
    title       = models.CharField(max_length=100, verbose_name=_('Title'), blank=False)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)
    file        = models.FileField(upload_to=upload_json_file, validators=[json_file_validator])
    completed   = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


def sanitize_string(data):
    return re.sub('\s+', '-', data)

def process_datetime_string(date_str):
    ret = parse_datetime(date_str)
    # make timezone aware if not aware
    if not is_aware(ret):
        ret = make_aware(ret)
    return ret

def json_upload_post_save(sender, instance, created, *args, **kwargs):
    if not instance.completed:
        json_file = instance.file
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
                start_time = process_datetime_string(data['Quiz']['StartTime']) if 'StartTime' in data['Quiz'] else now(),
                end_time = process_datetime_string(data['Quiz']['EndTime']) if 'EndTime' in data['Quiz'] else now() + timedelta(hours=1),
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

post_save.connect(json_upload_post_save, sender=JSONUpload)
