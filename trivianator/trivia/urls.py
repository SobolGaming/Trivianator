from django.urls import path, re_path

from . import views

urlpatterns = [
    path(route='',
        view=views.QuizListView.as_view(),
        name='quiz_index'),

    re_path(route=r'^category/$',
        view=views.CategoriesListView.as_view(),
        name='quiz_category_list_all'),

    re_path(route=r'^category/(?P<category_name>[\w|\W-]+)/$',
        view=views.ViewQuizListByCategory.as_view(),
        name='quiz_category_list_matching'),

    re_path(route=r'^progress/$',
        view=views.QuizUserProgressView.as_view(),
        name='quiz_progress'),

    re_path(route=r'^marking/$',
        view=views.QuizMarkingList.as_view(),
        name='quiz_marking'),

    re_path(route=r'^marking/(?P<pk>[\d.]+)/$',
        view=views.QuizMarkingDetail.as_view(),
        name='quiz_marking_detail'),

    #  passes variable 'quiz_name' to quiz_take view
    re_path(route=r'^(?P<slug>[\w-]+)/$',
        view=views.QuizDetailView.as_view(),
        name='quiz_start_page'),

    re_path(route=r'^(?P<quiz_name>[\w-]+)/take/$',
        view=views.QuizTake.as_view(),
        name='quiz_question'),
]
