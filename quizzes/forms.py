from django import forms

from quizzes.models import Quiz


class CreateQuizForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text', 'class': 'form-control', 'placeholder': 'Enter Quiz Name'
    }))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

    active_start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    active_end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

    first_prize_name = forms.CharField(widget=forms.TextInput(
        attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'Enter Prize Name'}
    ))

    first_prize_image = forms.ImageField(required=True)

    second_prize_name = forms.CharField(widget=forms.TextInput(
        attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'Enter Prize Name'}
    ))

    second_prize_image = forms.ImageField(required=True)

    third_prize_name = forms.CharField(widget=forms.TextInput(
        attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'Enter Prize Name'}
    ))

    third_prize_image = forms.ImageField(required=True)

    max_slots = forms.CharField(widget=forms.TextInput(
        attrs={'type': 'number', 'class': 'form-control', 'placeholder': 'Enter Max. Slots'}
    ))

    quiz_duration = forms.CharField(widget=forms.TextInput(
        attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'Quiz duration in days'}
    ))

    winner_instructions = forms.CharField(widget=forms.Textarea(
        attrs={'type': 'text', 'rows': 5, 'class': 'form-control', 'placeholder': 'Enter Winner Instructions'}
    ))

    rules = forms.CharField(widget=forms.Textarea(
        attrs={'type': 'text', 'rows': 5, 'class': 'form-control', 'placeholder': 'Enter Rules'}
    ))

    terms = forms.CharField(widget=forms.Textarea(
        attrs={'type': 'text', 'rows': 5, 'class': 'form-control', 'placeholder': 'Enter Terms'}
    ))

    first_question_file = forms.FileField(required=True)
    second_question_file = forms.FileField(required=True)
    third_question_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Quiz
        exclude = ('created_at', 'updated_at')
