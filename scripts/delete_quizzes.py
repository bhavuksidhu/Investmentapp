from quizzes.models import Quiz, QuestionFile, Prize

def run():
    # Fetch all questions
    quizzes = Quiz.objects.all()
    files = QuestionFile.objects.all()
    prizes = Prize.objects.all()
    # Delete questions
    quizzes.delete()
    files.delete()
    prizes.delete()
