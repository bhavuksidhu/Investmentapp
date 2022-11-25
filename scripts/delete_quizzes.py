from quizzes.models import Quiz, QuizFile, Prize

def run():
    # Fetch all questions
    quizzes = Quiz.objects.all()
    files = QuizFile.objects.all()
    prizes = Prize.objects.all()
    # Delete questions
    quizzes.delete()
    files.delete()
    prizes.delete()