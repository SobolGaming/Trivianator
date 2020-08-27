from django.urls import path, re_path

from . import views

urlpatterns = [
    path(route='',
        view=views.QuizListView.as_view(),
        name='quiz_index'),

    path(route='progress/',
        view=views.QuizUserProgressView.as_view(),
        name='quiz_progress'),

    path(route='leaderboards/',
        view=views.QuizLeaderboardsView.as_view(),
        name='quiz_leaderboards'),

    re_path(route=r'^category/$',
        view=views.CategoriesListView.as_view(),
        name='quiz_category_list_all'),

    re_path(route=r'^category/(?P<category_name>[\w|\W-]+)/$',
        view=views.ViewQuizListByCategory.as_view(),
        name='quiz_category_list_matching'),

    re_path(route=r'^marking/$',
        view=views.QuizMarkingList.as_view(),
        name='quiz_marking'),

    re_path(route=r'^marking/(?P<pk>[\d.]+)/$',
        view=views.QuizMarkingDetail.as_view(),
        name='quiz_marking_detail'),

    #  passes variable 'slug' to quiz detail view
    re_path(route=r'^(?P<slug>[\w-]+)/$',
        view=views.QuizDetailView.as_view(),
        name='quiz_start_page'),

    #  passes variable 'quiz_name' to quiz take view
    re_path(route=r'^(?P<quiz_name>[\w-]+)/take/$',
        view=views.QuizTake.as_view(),
        name='quiz_question'),
]
