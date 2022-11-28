from datetime import date
from django.shortcuts import render, redirect
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import CreateView, ListView, DetailView
from api.serializers import QuizSerializer
from quizzes import utils as quiz_utils
from quizzes.models import Quiz, Prize, QuestionFile
from quizzes.forms import CreateQuizForm
from django.contrib import messages


class QuizViewAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
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

                file_path = quiz_utils.save_file(file, quiz, "prize_images")

                Prize.objects.create(quiz_id=quiz, name=file.name, image=file_path)

            prize_files = request.FILES.getlist('prize_files')
            for file in prize_files:

                file_path = quiz_utils.save_file(file, quiz, "quiz_files")
                QuestionFile.objects.create(quiz_id=quiz, name=file.name, file=file_path)

            return Response({"response": response}, status=201)
        else:
            response = {
                "message": "Errors occurred",
                "errors": serializer_obj.errors
            }
            return Response(response, status=200)

    def get(self, request: Request, *args, **kwargs):
        quiz_qs = self.model.objects.all()
        quizzes = []

        for quiz in quiz_qs:
            prize_images = []

            for index, prize in enumerate(quiz.prizes()):
                name_prefix = quiz_utils.name_prefix(index)
                prize_images.append({
                    "name": f"{name_prefix} {prize.name}",
                    "prize_metadata": prize.prize_metadata,
                    "image_url": prize.image.url,
                })

            question_files = []
            for question_file in quiz.question_files():
                question_files.append({
                    "name": question_file.name,
                    "quiz_file": question_file.file.url,
                    "file_metadata": question_file.file_metadata,
                })

            quizzes.append({
                "name": quiz.name,
                "start_date": quiz.start_date,
                "start_time": f"{quiz.start_date}T{quiz.start_time}.000Z",
                "end_date": quiz.end_date,
                "end_time": f"{quiz.end_date}T{quiz.end_time}.000Z",
                "active_start_time": quiz.active_start_time,
                "active_end_time": quiz.active_end_time,
                "max_slots": quiz.max_slots,
                "quiz_duration": quiz.quiz_duration,
                "winner_instructions": quiz.winner_instructions,
                "rules": quiz.rules,
                "terms": quiz.terms,
                "prize_images": prize_images,
                "question_files": question_files
            })

        return Response({"quizzes": quizzes}, status=200)


class CreateQuizView(CreateView):
    permission_classes = (IsAdminUser,)

    serializer = QuizSerializer
    model = Quiz
    template_name = "quizzes/create_quiz.html"
    form_class = CreateQuizForm

    def post(self, request, *args, **kwargs):

        form = self.form_class(data=request.POST, files=request.FILES)
        if form.is_valid():

            quiz = Quiz.objects.create(
                name=form.cleaned_data['name'],
                start_date=form.cleaned_data['start_date'],
                start_time=form.cleaned_data['start_time'],
                end_date=form.cleaned_data['end_date'],
                end_time=form.cleaned_data['end_time'],
                active_start_time=form.cleaned_data['active_start_time'],
                active_end_time=form.cleaned_data['active_end_time'],
                max_slots=form.cleaned_data['max_slots'],
                quiz_duration=form.cleaned_data['quiz_duration'],
                winner_instructions=form.cleaned_data['winner_instructions'],
                terms=form.cleaned_data['terms'],
                rules=form.cleaned_data['rules'],

            )

            # 1st prize image
            Prize.objects.create(
                quiz=quiz,
                name=form.cleaned_data.get("first_prize_name"),
                image=form.files.get("first_prize_image")
            )

            # 2nd prize image
            Prize.objects.create(
                quiz=quiz,
                name=form.cleaned_data.get("second_prize_name"),
                image=form.files.get("second_prize_image")
            )
            # 3rd prize image
            Prize.objects.create(
                quiz=quiz,
                name=form.cleaned_data.get("third_prize_name"),
                image=form.files.get("third_prize_image")
            )

            # Question files
            #  1st question file
            QuestionFile.objects.create(
                quiz=quiz,
                name="First question file",
                file=form.files.get("first_question_file")
            )
            #  2nd question file
            QuestionFile.objects.create(
                quiz=quiz,
                name="Second question file",
                file=form.files.get("second_question_file")
            )
            #  3rd question file
            QuestionFile.objects.create(
                quiz=quiz,
                name="Third question file",
                file=form.files.get("third_question_file")
            )

            context = {}
            context["form"] = form
            context["quiz"] = quiz
            messages.info(request, message="Quiz created successfully", extra_tags="alert alert-success")

            return redirect(to='adminpanel:quizzes:quiz-details', pk=quiz.pk)
        else:
            response = {
                "message": "Errors occurred",
                "errors": form.errors
            }
            context = {}
            context["form"] = form
            context["response"] = response
            messages.error(request, message="Errors occurred in the form", extra_tags="alert alert-danger")

            return render(request, self.template_name, context)


class ListQuizView(ListView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = Quiz
    ordering = "created_at"
    template_name = "quizzes/list_quizzes.html"
    context_object_name = "quizzes"

    def get_context_data(self, **kwargs):

        # token = Token.objects.create(user=user)

        context = super().get_context_data(**kwargs)

        quiz_queryset = Quiz.objects.all()
        status = self.request.GET.get("status")
        date_today = date.today()

        filtered_quizzes = quiz_queryset
        if status == "ongoing":
            filtered_quizzes = quiz_queryset.filter(
                start_date__lte=date_today,
                end_date__gte=date_today
            )
        elif status == "completed":
            filtered_quizzes = quiz_queryset.filter(
                end_date__lt=date_today
            )
        elif status == "upcoming":
            filtered_quizzes = quiz_queryset.filter(
                start_date__gte=date_today,
            )
        elif status == "awaiting_results":
            filtered_quizzes = quiz_queryset.filter(status="AWAITING_RESULTS")

        quizzes = list()
        num = 0

        for quiz in filtered_quizzes:

            num += 1

            quizzes.append({
                "num": num,
                "pk": quiz.pk,
                "name": quiz.name,
                "start_date": quiz.start_date,
                "start_time": quiz.start_time,
                "end_date": quiz.end_date,
                "end_time": quiz.end_time,
                "active_start_time": quiz.active_start_time,
                "active_end_time": quiz.active_end_time,
                "max_slots": quiz.max_slots,
                "quiz_duration": quiz.quiz_duration,
                "created_at": quiz.created_at
            })

        context["quizzes"] = quizzes

        return context


class QuizDetailView(DetailView):
    model = Quiz
    template_name = "quizzes/quiz_details.html"
    permission_classes = (IsAdminUser,)

