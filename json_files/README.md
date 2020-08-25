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
        "Save": (Optional) Boolean (true or false) - should answers be saved upon quiz completion; defaults to "True"
        "SingleAttempt": (Optional) Boolean (true or false) - is each user given only one attempt to take the quiz; defaults to "False"
        "Draft": (Optional) Boolean (true or false) - is the quiz still in development, if "True" will not appear to non-admin users; defaults to "False"
        "Timer": (Optional) Positive Integer - value in seconds, if greater than 0, allowed for quiz attempt; defaults to 0
        "Leaderboards": (Optional) Boolean (true or false) - should leaderboards be shown at end of quiz; defaults to "True"
        "Competitive": (Optional) Boolean (true or false) - is this quiz competitive; defaults to "False"
        "StartTime": (Optional) DateTime - when quiz starts considering attempts for leaderboards and recording answers; defaults to "now() of posting"
            DateTime is Provided as "YYYY-MM-DD HH:MM:SS+ZZZZ" (the '+ZZZZ' is optional for specifing timezone offset from local server time)
        "EndTime": (Optional) DateTime - when quiz stops considering attempts for leaderboards and recording of answers; defaults to "not() +1 hour of posting"
            DateTime is Provided as "YYYY-MM-DD HH:MM:SS+ZZZZ" (the '+ZZZZ' is optional for specifing timezone offset from local server time)
        "Questions": [  next we have an array of Questions associated with the quiz, each non-optional field must be provided for each question
            {
                "QuestionType": Selection of either "single_choice" or "multi_choice" depending of just one, or more than one answers are correct
                "Category": (Optional) String - name of Category associated with the question; can be "" or null
                "Content": String - the text of the question
                "Explanation": (Optional) String - explanation of the reasoning behind the answers or about the question, defaults to ""
                "Timer": CURRENTLY NOT IMPLEMENTED - (Optional) Positive Integer - value in seconds, if greater than 0, allowed for question attempt; defaults to 0
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
### Categories
Categories exist to allow users to track what their strengths and weakness are.<br>
For example, question dealing with **Lore** could be assigned the category of "Lore", whereas questions dealing with **Nodes** can have their own category.<br>
As a user answers quiz questions perhaps they know all the **node** related answers but are bad at **lore**. The existance of categories tracks this.<br>
Additionally, it allows administrators to filter based on categories.

### Competitive
Quizzes marked as **Competitive** have an associated Start DateTime and End DateTime required. Between their Start and Close DateTime they will not display results or leaderboards at the end of quiz although both will be recorded. **Competitive** quizzes will only allow 1 attempt per user. These attempts CAN be timed with a timer specified for the length of the entire quiz. Once a **competitive** quiz completes, users can still take the quiz but it will not record results or consider peformance for inclusion in the Leaderboards.
