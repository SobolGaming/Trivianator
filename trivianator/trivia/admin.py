from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
# Register your models here.
from .models import Quiz, Category, Sitting, Question, Progress, Answer, Leaderboard, MOTD
from django.utils.translation import ugettext_lazy as _
from .models import ArchiveUpload


class ArchiveUploadsAdmin(admin.ModelAdmin):
    model = ArchiveUpload
    list_display = ('title', 'user', 'file', 'completed', )
    readonly_fields  = ('completed',)


class MOTDAdmin(admin.ModelAdmin):
    model = MOTD
    list_display = ('msg',)


class AnswerInline(admin.TabularInline):
    model = Answer


class QuizAdminForm(forms.ModelForm):
    """
        below is from
        http://stackoverflow.com/questions/11657682/
        django-admin-interface-using-horizontal-filter-with-
        inline-manytomany-field
    """

    class Meta:
        model = Quiz
        exclude = []

    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(
            verbose_name=_("Questions"),
            is_stacked=False))

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['questions'].initial = \
                self.instance.question_set.all().select_subclasses()

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data['questions'])
        self.save_m2m()
        return quiz


class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm

    list_display = ('title', 'category', )
    list_filter = ('category',)
    search_fields = ('description', 'category', )


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('category', )


class SittingAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'current_score', 'complete', 'start', 'end', )
    search_fields = ('user', 'quiz', )
    fields = ('user', 'quiz', 'current_score', 'user_answers', )


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'category', )
    list_filter = ('category',)
    fields = ('content', 'category', 'question_type',
              'figure', 'quiz', 'explanation', 'answer_order')

    search_fields = ('content', 'question_type', 'explanation')
    filter_horizontal = ('quiz',)

    inlines = [AnswerInline]


class ProgressAdmin(admin.ModelAdmin):
    """
    to do:
            create a user section
    """
    search_fields = ('user', 'score', )


class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user', 'score', 'completion_time', )
    list_filter = ('quiz', )
    search_fields = ('quiz__title', 'user__username',)


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Sitting, SittingAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(Leaderboard, LeaderboardAdmin)
admin.site.register(ArchiveUpload, ArchiveUploadsAdmin)
admin.site.register(MOTD, MOTDAdmin)
