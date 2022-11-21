import json
import os.path

from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.serializers import serialize
from api.serializers import QuizSerializer
from quizzes.models import Quiz, Prize, QuizFile


class QuizView(APIView):
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)
    serializer = QuizSerializer
    model = Quiz

    def post(self, request: Request, *args, **kwargs):

        serializer_obj = self.serializer(data=request.data)
        if serializer_obj.is_valid():
            new_quiz = self.model.objects.create(
                name=request.data.get('name'),
                start_date_time=request.data.get('start_date_time'),
                end_date_time=request.data.get('end_date_time'),
                active_start_time=request.data.get('active_start_time'),
                active_end_time=request.data.get('active_end_time'),
                max_slots=request.data.get('max_slots'),
                quiz_duration=request.data.get('quiz_duration'),
                winner_instructions=request.data.get('winner_instructions'),
                rules=request.data.get('rules'),
                terms=request.data.get('terms'),
            )
            quiz_qs = self.model.objects.filter(pk=new_quiz.pk)
            response = {
                "message": "Quiz created successfully",
                "new_quiz": quiz_qs.values()
            }

            quiz = quiz_qs.get()

            prize_images = request.FILES.getlist('prize_images')
            for file in prize_images:
                file_dir = os.path.join(settings.MEDIA_ROOT, "prize_images", f"{quiz.pk}")

                if not os.path.exists(file_dir):
                    try:
                        os.mkdir(file_dir)
                    except Exception as exc:
                        raise Exception(f"Failed creating directory: {exc}")
                file_path = os.path.join(file_dir, file.name)

                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                prize_image = Prize.objects.create(quiz_id=quiz, name=file.name, image=file_path)

            prize_files = request.FILES.getlist('prize_files')
            for file in prize_files:
                file_dir = os.path.join(settings.MEDIA_ROOT, "quiz_files", f"{quiz.pk}")

                if not os.path.exists(file_dir):
                    try:
                        os.mkdir(file_dir)
                    except Exception as exc:
                        raise Exception(f"Failed creating directory: {exc}")
                file_path = os.path.join(file_dir, file.name)

                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                file = QuizFile.objects.create(quiz_id=quiz, name=file.name, file=file_path)

            return Response({"response": response}, status=201)
        else:
            response = {
                "message": "Errors occurred",
                "errors": serializer_obj.errors
            }
            return Response(response, status=200)

    def get(self, request: Request, *args, **kwargs):
        response = self.model.objects.all().values()

        return Response({"quizzes": response}, status=200)
