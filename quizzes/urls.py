from django.urls import path

from quizzes.views import QuizView

app_name = "payments"

urlpatterns = [
    path("create/", QuizView.as_view(), name="subscribe"),
]
