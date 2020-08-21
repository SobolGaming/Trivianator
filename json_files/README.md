# JSON File Format

The JSON file for uploading a Quiz, it's associated Questions and their Answers use the following format.<br>

```
{
    "Quiz": {
        "Title": String - Name of Quiz
        "URL": String - short-name link to this Quiz - will be converted to lower-case; please don't use spaces or non-URL-compliant characters
        "Category": (Optional) String - name of Category associated with quiz; can be "" or null
        "RandomOrder": (Optional) Boolean (true or false) - should questions in the quiz be presented in random order or as entered; default to "False"
        "AnswerRevealOption": (Optional) Integer between 1 and 3 - defaults to 1
            1 == "show correct answer after each question"
            2 == "show correct answers at end of quiz"
            3 == "never show answers"
        "Save": (Optional) Boolean (true or false) - should answers be saved upon quiz completetion; defaults to "True"
        "SingleAttempt": (Optional) Boolean (true or false) - is each user given only one attempt to take the quiz; defaults to "False"
        "Draft": (Optional) Boolean (true or false) - is the quiz still in development, if "True" will not appear to non-admin users; defaults to "False"
        "Questions": [  next we have an array of Questions associated with the quiz, each non-optional field must be provided for each question
            {
                "QuestionType": Selection of either "single_choice" or "multi_choice" depending of just one, or more than one answers are correct
                "Category": (Optional) String - name of Category associated with the question; can be "" or null
                "Content": String - the text of the question
                "Explanation": (Optional) String - explanation of the reasoning behind the answers or about the question, defaults to ""
                "AnswerOrder": Selection of "none", "content", "random" - how should the answers be ordered
                    "none" == answer order presented as entered into Database
                    "content" == answer order alphabetically sorted by text of the answers
                    "random" == answer order is randomized and will vary each time the question is asked
                "Answers": [ next we have an array of Answers associated with each question
                    {
                        "Content": String - the text of the answer
                        "Correct": Boolean (true of false) - indicates if this is a correct answer
                            note - only one answer should be marked as "true" for "single_choice" QuestionType, can be 0 or more for "multi_choice" QuestionType
                    } put a "," at end of "}" for each answer except the last one to be valid JSON format
                ] end of Answers array
            } put a "," at end of "}" for each question except the last one to be valid JSON format
        ] end of Questions array
    }
}
```