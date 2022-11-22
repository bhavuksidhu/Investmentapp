from django.urls import path

from quizzes.views import ListQuizView, QuizViewAPI

app_name = "quizzes"

urlpatterns = [
    path("create/", QuizViewAPI.as_view(), name="create"),
    path("", ListQuizView.as_view(), name="list-quizzes"),
]
