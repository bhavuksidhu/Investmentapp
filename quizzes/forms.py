from django import forms

from quizzes.models import Quiz


class CreateQuizForm(forms.ModelForm):
    start_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Enter Quiz Name'}
        )
        self.fields['start_date_time'].widget.attrs.update(
            {'class': 'form-control'}
        )
        self.fields['end_date_time'].widget.attrs.update(
            {'class': 'form-control', 'type': 'date'}
        )

        self.fields['active_start_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['active_end_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['max_slots'].widget.attrs.update({'class': 'form-control'})
        self.fields['quiz_duration'].widget.attrs.update({'class': 'form-control'})
        self.fields['winner_instructions'].widget.attrs.update({'class': 'form-control'})
        self.fields['rules'].widget.attrs.update({'class': 'form-control'})
        self.fields['terms'].widget.attrs.update({'rows': 1})

    class Meta:
        model = Quiz
        exclude = ('created_at', 'updated_at')
