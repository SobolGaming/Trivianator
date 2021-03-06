import random

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView
from .forms import QuestionForm
from .models import Quiz, Category, Progress, Sitting, Question, MOTD
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound

class QuizMarkerMixin(object):
    @method_decorator(login_required)
    @method_decorator(permission_required('quiz.view_sittings'))
    def dispatch(self, *args, **kwargs):
        return super(QuizMarkerMixin, self).dispatch(*args, **kwargs)


class SittingFilterTitleMixin(object):
    def get_queryset(self):
        queryset = super(SittingFilterTitleMixin, self).get_queryset()
        quiz_filter = self.request.GET.get('quiz_filter')
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)

        return queryset


class QuizListView(ListView):
    model = Quiz
    # @login_required
    def get_queryset(self):
        queryset = super(QuizListView, self).get_queryset()
        return queryset.filter(draft=False)

    def get_context_data(self, **kwargs):
        context = super(QuizListView, self).get_context_data(**kwargs)
        q_competitive = self.get_queryset().filter(competitive=True)
        context['now'] = now()
        context['competitive'] = []
        context['competitive_taken'] = []
        context['competitive_old'] = []
        context['competitive_old_taken'] = []
        context['competitive_upcoming'] = []
        for q in q_competitive:
            # see if we have a sitting for this quiz already
            prev_score, prev_sit = q.get_quiz_sit_info(self.request.user)

            if q.start_time <= now() and q.end_time > now():
                context['competitive'].append(
                    {
                        'quiz': q,
                        'taken': prev_sit != None and prev_sit.complete,
                    }
                )
            elif q.start_time > now():
                context['competitive_upcoming'].append(q)
            elif q.end_time <= now():
                if prev_sit != None:
                    results = {
                        'quiz': prev_sit.quiz,
                        'percent': prev_sit.get_percent_correct,
                        'sitting': prev_sit,
                    }
                    context['competitive_old_taken'].append(results)
                else:
                    context['competitive_old'].append(q)

        context['generic_new'] = []
        context['generic_taken'] = []
        context['generic_results'] = {}
        non_competitive_quizzes = self.get_queryset().filter(competitive=False)
        for q in non_competitive_quizzes:
            prev_score, _ = q.get_quiz_sit_info(self.request.user)
            if prev_score != None:
                context['generic_taken'].append(q)
                context['generic_results'][q.title] = prev_score
            else:
                context['generic_new'].append(q)

        context['competitive_upcoming_count'] = len(context['competitive_upcoming'])
        context['competitive_old_count'] = len(context['competitive_old'])
        context['competitive_old_taken_count'] = len(context['competitive_old_taken'])

        if self.request.user.has_perm('trivia.change_quiz'):
            context['draft_quizzes'] = []
            draft_qs = super(QuizListView, self).get_queryset().filter(draft=True)
            for draft_quiz in draft_qs:
                context['draft_quizzes'].append(draft_quiz)

        # see if there is any admin messages to display
        get_motd(self.request)

        return context


class QuizListViewGuest(ListView):
    template_name = 'guest_quiz_list.html'
    model = Quiz
    def get_queryset(self):
        queryset = super(QuizListViewGuest, self).get_queryset()
        return queryset.filter(draft=False)

    def get_context_data(self, **kwargs):
        context = super(QuizListViewGuest, self).get_context_data(**kwargs)
        q_list = self.get_queryset()

        context['quiz_list'] = []
        context['quiz_list_flat'] = "Quizzes: " + " \n "
        for q in q_list:
            context['quiz_list'].append(q)
            context['quiz_list_flat'] += q.title + " \n "

        context['quiz_list_flat'] = context['quiz_list_flat'].replace('-', ' ')
        # see if there is any admin messages to display
        get_motd(self.request)

        return context


class QuizDetailView(DetailView):
    model = Quiz
    slug_field = 'url'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # from django.contrib.auth.models import Permission
        # print([(x.id, x.name) for x in Permission.objects.filter(user=request.user)])
        if (self.object.get_time_until_start > 0 or self.object.draft) and not request.user.has_perm('trivia.change_quiz'):
            raise PermissionDenied

        context = self.get_context_data(object=self.object)

        # if there is a quiz specific message during a competitive active period
        if self.object.competitive and not self.object.end_time_expired and self.object.message:
            messages.warning(request, self.object.message, extra_tags='safe')
        if not self.object.competitive and self.object.message:
            messages.warning(request, self.object.message, extra_tags='safe')

        return self.render_to_response(context)


class CategoriesListView(ListView):
    model = Category


class ViewQuizListByCategory(ListView):
    model = Quiz
    template_name = 'view_quiz_category.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category,
            category=self.kwargs['category_name']
        )

        return super(ViewQuizListByCategory, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self).get_context_data(**kwargs)
        context['category'] = self.category
        return context

    def get_queryset(self):
        queryset = super(ViewQuizListByCategory, self).get_queryset()
        return queryset.filter(category=self.category, draft=False)


class QuizUserProgressView(TemplateView):
    template_name = 'progress.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuizUserProgressView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuizUserProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context['cat_scores'] = progress.list_all_cat_scores
        context['saved'] = progress.show_saved()
        context['started'] = progress.show_started()
        context['display_categories'] = True
        context['hide'] = []
        for quiz in context['saved']:
            if quiz.quiz.competitive and now() < quiz.quiz.end_time:
                context['display_categories'] = False
                context['hide'].append(quiz.quiz.title)
                break
        for quiz in context['started']:
            if quiz.quiz.competitive and now() < quiz.quiz.end_time:
                context['display_categories'] = False
                context['hide'].append(quiz.quiz.title)
                break

        # see if there is any admin messages to display
        get_motd(self.request)

        return context


class QuizLeaderboardsView(QuizListView):
    template_name = 'leaderboard_list.html'
    model = Quiz
    # @login_required
    def get_queryset(self):
        queryset = super(QuizLeaderboardsView, self).get_queryset()
        return queryset.filter(draft=False)

    def get_context_data(self, **kwargs):
        context = super(QuizLeaderboardsView, self).get_context_data(**kwargs)
        q_competitive = self.get_queryset().filter(competitive=True)
        context['now'] = now()
        context['competitive_old'] = []
        for q in q_competitive:
            if q.end_time <= now():
                context['competitive_old'].append(q)

        context['competitive_old_count'] = len(context['competitive_old'])
        return context


class QuizLeaderboardsDetailView(SittingFilterTitleMixin, DetailView):
    model = Quiz
    template_name = 'leaderboard_detail.html'


class QuizMarkingList(QuizMarkerMixin, SittingFilterTitleMixin, ListView):
    model = Sitting

    def get_queryset(self):
        queryset = super(QuizMarkingList, self).get_queryset().filter(complete=True)

        user_filter = self.request.GET.get('user_filter')
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        return queryset

    class Meta:
        pass


class QuizMarkingDetail(QuizMarkerMixin, DetailView):
    model = Sitting

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get('qid', None)
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context['questions'] = context['sitting'].get_questions(with_answers=True)
        return context


class QuizTake(FormView):
    form_class = QuestionForm
    template_name = 'question.html'

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, url=self.kwargs['quiz_name'])
        if self.quiz.draft and not request.user.has_perm('trivia.change_quiz'):
            raise PermissionDenied

        self.logged_in_user = self.request.user.is_authenticated

        if self.logged_in_user:
            self.sitting = Sitting.objects.user_sitting(request.user, self.quiz)
            if self.sitting is False:
                return render(request, 'single_complete.html')

        return super(QuizTake, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=QuestionForm):
        if self.logged_in_user:
            self.question = self.sitting.get_first_question()
            self.progress = self.sitting.progress()
        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super(QuizTake, self).get_form_kwargs()
        return dict(kwargs, question=self.question)

    def form_valid(self, form):
        if self.logged_in_user:
            self.form_valid_user(form)
            if self.sitting.get_first_question() is False:
                return self.final_result_user()
            if self.quiz.timer > 0:
                elapsed = now() - self.sitting.start
                if elapsed.total_seconds() > self.quiz.timer:
                    return self.final_result_user()
        self.request.POST = {}

        return super(QuizTake, self).get(self, self.request)

    def get_context_data(self, **kwargs):
        context = super(QuizTake, self).get_context_data(**kwargs)
        if Sitting.objects.filter(quiz=self.quiz,user=self.request.user).exists():
            context['time_remaining'] = Sitting.objects.user_sitting(quiz=self.quiz,user=self.request.user).get_quiz_time_remaining()
        context['question'] = self.question
        context['quiz'] = self.quiz
        if hasattr(self, 'previous'):
            context['previous'] = self.previous
        if hasattr(self, 'progress'):
            context['progress'] = self.progress
        return context

    def form_valid_user(self, form):
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data['answers']

        is_correct = False
        if 'multi_choice' == self.question.question_type:
            is_correct = self.question.check_if_correct_mc(guess, [id for id, val in self.question.get_answers_list()], self.quiz.competitive and not self.quiz.end_time_expired)
        else:
            is_correct = self.question.check_if_correct_sc(guess, self.quiz.competitive and not self.quiz.end_time_expired)

        # if end_time of a competitive quiz has passed and you started the quiz before it ended, disregard last answer
        if self.quiz.competitive and self.quiz.end_time_expired and self.sitting.start < self.quiz.end_time:
            is_correct = False
            guess = ''
        # if quiz timer was set and expired, disregard last answer
        if self.quiz.timer > 0 and (now() - self.sitting.start).total_seconds() > self.quiz.timer:
            is_correct = False
            guess = ''

        if is_correct is True:
            self.sitting.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        if self.quiz.answers_reveal_option == 1:
            self.previous = {'previous_answer': guess,
                             'previous_outcome': is_correct,
                             'previous_question': self.question,
                             'answers': self.question.get_answers(),
                             'question_type': self.question.question_type,
                             'no_longer_competitive': self.quiz.end_time_expired,
            }
        else:
            self.previous = {}

        # increment question count if competitive and active
        if self.quiz.competitive and not self.quiz.end_time_expired:
            self.question.inc()

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

    def final_result_user(self):
        elapsed = (now() - self.sitting.start).total_seconds()

        results = {
            'quiz': self.quiz,
            'score': self.sitting.get_current_score,
            'max_score': self.sitting.get_max_score,
            'percent': self.sitting.get_percent_correct,
            'sitting': self.sitting,
            'previous': self.previous,
            'elapsed': elapsed,
            'no_longer_competitive': self.quiz.end_time_expired,
        }

        self.sitting.mark_quiz_complete()

        if self.quiz.answers_reveal_option == 2 or (self.quiz.end_time_expired is True and self.quiz.answers_reveal_option == 3) \
            or (self.quiz.draft and self.request.user.has_perm('trivia.change_quiz')):
            results['questions'] = self.sitting.get_questions(with_answers=True)
            results['incorrect_questions'] = self.sitting.get_incorrect_questions
        
        if self.quiz.end_time_expired is True or (self.quiz.draft and self.request.user.has_perm('trivia.change_quiz')):
            results['reveal_answer'] = True

        prev_score, prev_sit = self.quiz.get_quiz_sit_info(self.request.user)
        if prev_score == None:
            raise Exception("Invalid Sitting at End!")

        return render(self.request, 'result.html', results)


class SittingResultView(DetailView):
    model = Sitting
    template_name = 'result.html'

    def get_queryset(self):
        queryset = super(SittingResultView, self).get_queryset()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(SittingResultView, self).get_context_data(**kwargs)
        sitting = self.get_object()
        # if this sitting does not belong to the user (b/c they hand crafted the URL)
        # raise 403
        if sitting.user != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied

        # if quiz is competitive and not yet complete, don't show results
        if sitting.quiz.competitive and not sitting.quiz.end_time_expired and not sitting.quiz.draft:
            return context
        else:
            context['quiz'] = sitting.quiz
            context['reveal_answer'] = True
            context['score'] = sitting.get_current_score
            context['max_score'] = sitting.get_max_score
            context['percent'] = sitting.get_percent_correct
            context['sitting'] = sitting
            context['questions'] = sitting.get_questions(with_answers=True)
            context['incorrect_questions'] = sitting.get_incorrect_questions
            context['no_longer_competitive'] = True
        return context


class QuizAnswerStatView(DetailView):
    model = Quiz
    template_name = 'answer_stats.html'

    def get_context_data(self, **kwargs):
        context = super(QuizAnswerStatView, self).get_context_data(**kwargs)
        quiz = self.get_object()
        try:
            sitting = Sitting.objects.get(quiz=quiz, complete=True)
        except Sitting.MultipleObjectsReturned:
            sitting = Sitting.objects.filter(quiz=quiz, complete=True)[0]
        except Sitting.DoesNotExist:
            return context

        if sitting:
            questions = sitting.get_questions()
            context['questions'] = []
            for question in questions:
                answers = question.get_answers_percent_list()
                q_stat = {
                    'q_content': question.content,
                    'q_figure': question.figure,
                    'answers': [],
                }
                for entry in answers:
                    a_stat = {
                        'a_content': entry[0],
                        'a_percent': entry[1],
                        'a_correct': entry[2],
                        'a_count': entry[3],
                    }
                    q_stat['answers'].append(a_stat)
                context['questions'].append(q_stat)
        return context


def get_motd(request):
    try:
        obj = MOTD.objects.get()
        messages.error(request, obj.msg)
    except Exception as e:
        pass


def index(request):
    return render(request, 'index.html', {})


def login_user(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect("index")
        else:
            messages.success(request, 'Error logging in')
            return redirect('login')
    else:
        return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('login')
