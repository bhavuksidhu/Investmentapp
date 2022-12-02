from datetime import date

import pandas
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from pandas.io.sas.sas_constants import magic
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import CreateView, ListView, DetailView
from api.serializers import QuizSerializer
from quizzes import utils as quiz_utils
from quizzes.models import Quiz, Prize, QuestionFile, Question, QuestionOption
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
                prize_images.append({
                    "prize_key": quiz_utils.name_prefix(index),
                    "prize_name": prize.name,
                    "prize_image": request.build_absolute_uri(prize.image.url),
                })

            questions = []
            for question in quiz.questions():

                options = []
                for option in QuestionOption.objects.filter(question=question.pk):
                    options.append(option.option)

                questions.append({
                    "number": question.pk,
                    "question": question.question_text,
                    "options": options,
                    "correct_option": question.correct_choice,
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
                "questions": questions
            })

        return Response({"quizzes": quizzes}, status=200)


class CreateQuizView(LoginRequiredMixin, CreateView):
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

            files = form.files

            ########################
            #  Question files      #
            ########################
            quiz_files_count = int(form.cleaned_data['quiz_duration'])

            if quiz_files_count > 0:
                for index in range(quiz_files_count):
                    quiz_file = files.get(f"question_file_day_{index + 1}")

                    question_file_obj = QuestionFile.objects.create(
                        quiz=quiz,
                        name=quiz_utils.get_quiz_file_name(index),
                        file=quiz_file
                    )

                    # save questions to db
                    df = pandas.read_excel(question_file_obj.file.path)
                    for question, row in df.iterrows():
                        qstn = Question.objects.create(
                            quiz=quiz, question_text=row['question'], correct_choice=row['correct_option']
                        )

                        QuestionOption.objects.create(question=qstn, option=row['option1'])
                        QuestionOption.objects.create(question=qstn, option=row['option2'])
                        QuestionOption.objects.create(question=qstn, option=row['option3'])
                        QuestionOption.objects.create(question=qstn, option=row['option4'])

            return redirect(to=f"/adminpanel/quizzes/details/{quiz.pk}/")
        else:
            messages.error(request, "Validation errors occurred", extra_tags="alert alert-danger")
            context = {"form": form}
            return render(request, self.template_name, context)


class ListQuizView(LoginRequiredMixin, ListView):
    permission_classes = (IsAuthenticated,)
    model = Quiz
    ordering = "created_at"
    template_name = "quizzes/list_quizzes.html"
    context_object_name = "quizzes"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # token = Token.objects.get(user=self.request.user)
        # print(token)

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


class QuizDetailView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = "quizzes/quiz_details.html"
    permission_classes = (IsAuthenticated,)
