from django import forms
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple

class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_answers_list()]   
        if question.question_type == 'multi_choice':
            self.fields["answers"] = forms.ChoiceField(choices=choice_list, widget=CheckboxSelectMultiple)
        else:
            self.fields["answers"] = forms.ChoiceField(choices=choice_list, widget=RadioSelect)