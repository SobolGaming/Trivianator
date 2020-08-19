from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple

class QuestionForm(forms.Form):
    def __init__(self, question, question_type = 1, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_answers_list()]
        if question_type == 1:
            self.fields["answers"] = forms.ChoiceField(choices=choice_list, widget=RadioSelect)
        elif question_type == 2:
            self.fields["answers"] = forms.ChoiceField(choices=choice_list, widget=CheckboxSelectMultiple)