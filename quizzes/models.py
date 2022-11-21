from django.db import models


class Quiz(models.Model):
    name = models.CharField(max_length=500, null=False, blank=False)
    start_date_time = models.DateTimeField(null=False, blank=False)
    end_date_time = models.DateTimeField(null=False, blank=False)
    active_start_time = models.TimeField(null=False, blank=False)
    active_end_time = models.TimeField(null=False, blank=False)
    max_slots = models.CharField(max_length=500, null=False, blank=False)
    quiz_duration = models.CharField(max_length=500, null=False, blank=False)
    winner_instructions = models.TextField(null=False, blank=False)
    rules = models.TextField(null=False, blank=False)
    terms = models.TextField(null=False, blank=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def prizes(self):
        return Prize.objects.filter(quiz_id=self.pk)

    def quiz_files(self):
        return QuizFile.objects.filter(quiz_id=self.pk)


class Prize(models.Model):
    quiz_id = models.ForeignKey(to=Quiz, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    image = models.FileField()

    def __str__(self):
        return "%s for quiz_id= %s" % (self.name, self.quiz_id)


class QuizFile(models.Model):
    quiz_id = models.ForeignKey(to=Quiz, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    file = models.FileField()

    def __str__(self):
        return "%s for quiz_id= %s" % (self.name, self.quiz_id)
