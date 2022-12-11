from django.urls import path

from quizzes.views import ListQuizView, CreateQuizView, QuizDetailView

app_name = "quizzes"

urlpatterns = [
    path("create/", CreateQuizView.as_view(), name="create-quiz"),
    path("details/<int:pk>/", QuizDetailView.as_view(), name="quiz-details"),
    path("", ListQuizView.as_view(), name="list-quizzes"),
]
