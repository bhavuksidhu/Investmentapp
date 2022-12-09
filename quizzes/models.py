from django.db import models

from core.models import UserProfile
from quizzes.utils import question_files_upload_dir, prize_images_dir


class Quiz(models.Model):
    name = models.CharField(max_length=500, null=False, blank=False)

    start_date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)

    end_date = models.DateField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)

    active_start_time = models.TimeField(null=False, blank=False)
    active_end_time = models.TimeField(null=False, blank=False)

    max_slots = models.CharField(max_length=500, null=False, blank=False)
    quiz_duration = models.CharField(max_length=500, null=False, blank=False)
    winner_instructions = models.TextField(null=False, blank=False)
    rules = models.TextField(null=False, blank=False)
    terms = models.TextField(null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ("UPCOMING", 'Upcoming'),
        ("ACTIVE", 'Active'),
        ("AWAITING_RESULTS", 'Awaiting Results'),
        ("COMPLETED", 'Completed')
    ]
    status = models.CharField(
        max_length=50, blank=True, null=False,
        choices=STATUS_CHOICES,
        default="UPCOMING",
    )

    def __str__(self):
        return self.name

    def prizes(self):
        return Prize.objects.filter(quiz_id=self.pk)

    def question_files(self):
        return QuestionFile.objects.filter(quiz_id=self.pk)

    def questions(self):
        return Question.objects.filter(quiz_id=self.pk)

    class Meta:
        ordering = ["-created_at"]


class QuizEnrollment(models.Model):
    ENROLLMENT_STATUSES = [
        ("ACTIVE", 'Active'),
        ("INACTIVE", 'Inactive'),
        ("COMPLETED", 'Completed')
    ]
    userprofile = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    quiz = models.ForeignKey(Quiz, on_delete=models.DO_NOTHING)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=ENROLLMENT_STATUSES, default="ACTIVE")
    notes = models.CharField(max_length=500, null=True, blank=True)


class Prize(models.Model):
    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE)
    prize_metadata = models.JSONField(null=True, blank=True)
    name = models.CharField(max_length=500)
    image = models.FileField(upload_to=prize_images_dir)

    def __str__(self):
        return "%s for quiz_id= %s" % (self.name, self.quiz_id)


class QuestionFile(models.Model):
    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    file_metadata = models.JSONField(null=True, blank=True)
    file = models.FileField(upload_to=question_files_upload_dir)

    def __str__(self):
        return "%s for quiz_id= %s" % (self.name, self.quiz_id)


class Question(models.Model):
    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=1000, default="")
    correct_choice = models.CharField(max_length=250, default="")

    def options(self):
        return QuestionOption.objects.filter(question_id=self.pk)


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.CharField(max_length=250)
    is_correct = models.BooleanField(default=False)


class Answer(models.Model):
    userprofile = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    question = models.ForeignKey(Question, on_delete=models.DO_NOTHING)
    duration = models.IntegerField()
    answer = models.ForeignKey(QuestionOption, on_delete=models.DO_NOTHING)


class WinnerConsent(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    second_name = models.CharField(max_length=50, blank=False, null=False)
    country_code = models.CharField(max_length=5, blank=False, null=False)
    phone_number = models.CharField(max_length=25, blank=False, null=False)
    email = models.EmailField(max_length=100, null=False, blank=False)
    address = models.TextField(max_length=500, null=False, blank=False)
    terms_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    consented_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
