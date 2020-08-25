from django import template

register = template.Library()


@register.inclusion_tag('correct_answer.html', takes_context=True)
def correct_answer_for_all(context, question):
    """
    processes the correct answer based on a given question object
    if the answer is incorrect, informs the user
    """
    answers = question.get_answers()
    incorrect_list = context.get('incorrect_questions', [])
    if question.id in incorrect_list:
        user_was_incorrect = True
    else:
        user_was_incorrect = False

    return {'previous': {'answers': answers},
            'user_was_incorrect': user_was_incorrect}


@register.filter
def answer_choice_to_string(question, answer):
    return question.answer_choice_to_string(answer)


@register.filter()
def smooth_timedelta(secs):
    """Convert a datetime.timedelta object into Days, Hours, Minutes, Seconds."""
    timetot = ""
    if secs > 86400: # 60sec * 60min * 24hrs
        days = secs // 86400
        if int(days) == 1:
            timetot += "{} day".format(int(days))
        else:
            timetot += "{} days".format(int(days))
        secs = secs - days*86400

    if secs > 3600:
        hrs = secs // 3600
        if int(hrs) == 1:
            timetot += " {} hour".format(int(hrs))
        else:
            timetot += " {} hours".format(int(hrs))
        secs = secs - hrs*3600

    if secs > 60:
        mins = secs // 60
        if int(mins) == 1:
            timetot += " {} minute".format(int(mins))
        else:
            timetot += " {} minutes".format(int(mins))
        secs = secs - mins*60

    if int(secs) == 1:
        timetot += " {} second".format(int(secs))
    elif secs > 1:
        timetot += " {} seconds".format(int(secs))
    return timetot
