from django import forms
from .models import Score, UserSubject

class ScoreForm(forms.ModelForm):
    # Rule: Year 1978-2025 | Total Questions 40-100
    year = forms.IntegerField(min_value=1978, max_value=2025)
    total = forms.IntegerField(min_value=40, max_value=100)
    correct = forms.IntegerField(min_value=0)

    class Meta:
        model = Score
        fields = ['subject', 'year', 'correct', 'total']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # RULE: Only show subjects the user chose in the setup step
            user_subjects = UserSubject.objects.filter(user=user).values_list('name', 'name')
            self.fields['subject'] = forms.ChoiceField(choices=user_subjects)

    def clean(self):
        cleaned_data = super().clean()
        correct = cleaned_data.get("correct")
        total = cleaned_data.get("total")

        # RULE: If user tries something like 123/100, REJECT IT
        if correct is not None and total is not None:
            if correct > total:
                raise forms.ValidationError(f"Invalid Score: You cannot have {correct} correct out of {total} total questions.")
        return cleaned_data