from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from ..models.configuration import Configuration
from ..models.headers import Header

# bug fix
import collections.abc
collections.Mapping = collections.abc.Mapping
from PyInquirer import prompt

from prompt_toolkit.validation import Validator, ValidationError


class Document:
    """
    A class representing the document created by draft.
    """

    _exercises = None
    _user_values = None

    @property
    def user_values(self):
        if self._user_values is None:
            self.__prompt_for_user_values__()
        return self._user_values

    @user_values.setter
    def user_values(self, newValue: Dict[str, Any]):
        self._user_values = newValue

    @property
    def exercises(self):
        if self._exercises is None:
            self.__prompt_for_exercises__()
        return self._exercises

    def __init__(self, header: Header, configuration: Configuration):
        self.configuration = configuration
        self.header = header

    def compile(self):
        """
        Compile the document.

        That means:
        - Prompt and validate the document's name
        - Create the document and write the preamble
        - Write the header by replacing its placeholders and removing
          the document body.
        - Begin the document body
        - Iterate over the exercises, fill in their placeholders
          🚨 Every placeholder should be unique in each exercise type.
        - Write to the document and copy any additional templates
          in the directory
        - Close the document body
        """
        class DocumentNameValidator(Validator):
            @staticmethod
            def __validate__(text: str) -> Optional[ValidationError]:
                if not len(text) != 0:
                    return (False, ValidationError(
                        message='The name of the file cannot be empty.',
                        cursor_position=len(text)
                    ))
                path = Path(
                    text
                    if text.endswith('.tex')
                    else text + '.tex'
                )
                if path.exists():
                    return (False, ValidationError(
                        message='A document with this name already exists.',
                        cursor_position=len(text)
                    ))

            def validate(self, document):
                error = DocumentNameValidator.__validate__(document.text)
                if error is not None:
                    raise error

        error = DocumentNameValidator.__validate__(self.header.name)
        document_name_prompt = [{
            'type': 'input',
            'message': 'What should the document be called?',
            'default': self.header.name,
            'validate': DocumentNameValidator,
            'name': 'output',
        }]
        document_name = (
            self.prompt_user(document_name_prompt)  # can return {}
            if error is None
            else prompt(document_name_prompt)  # {'output': 'exam}
        ).get(
            'output',
            self.configuration.user_values.get('output', '')
            # last default is never reached
        )

    def prompt_user(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prompt the user with the provided prompts only if they haven't
        been declared in any configuration's file yet.
        """
        def exists(key: str) -> Callable[Dict[str, Any], bool]:
            def when(answers: Dict[str, Any]) -> bool:
                if key in self.configuration.user_values:
                    return False
                else:
                    return True
            return when

        # Omit any prompts for values already defined in
        questions = prompts.copy()
        for question in questions:
            question['when'] = exists(question['name'])

        result = {}
        answers = prompt(questions)
        for key, value in answers.items():
            result[key] = value
        return result

    def __prompt_for_exercises__(self):
        """
        Prompt the user to choose which exercises should be
        included in the document.
        """
        class AmountValidator(Validator):
            def validate(self, document):
                ok = document.text.isdigit() and int(document.text) > 0
                if not ok:
                    raise ValidationError(
                        message='Please input a digit 1 or greater.',
                        cursor_position=len(document.text)
                    )

        result: Dict[str, Any] = {}

        exercise_types = self.prompt_user(
            self.configuration.exercises_prompt
        )['exercises']

        # Manage multiple creation
        is_multiples = self.prompt_user([{
            'type': 'confirm',
            'name': 'multiples',
            'message': 'Any exercise more than once?',
            'default': False,
            'when': lambda _: len(exercise_types) != 0,
        }]).get('multiples', False)

        if (not isinstance(is_multiples, bool)) or is_multiples:
            for exercise in exercise_types:
                amount = prompt({
                    'type': 'input',
                    'message': "How many '%s'?" % exercise,
                    'name': 'amount',
                    'validate': AmountValidator,
                })['amount']

                for i in range(1, int(amount) + 1):
                    templates = self.configuration.exercises[exercise]
                    result.update({
                        exercise + '-' + str(i): templates.copy()
                    })
        else:
            # Build the exercises return type if no multiples
            for exercise in exercise_types:
                result.update({
                    exercise: self.configuration.exercises[exercise]
                })

        self._exercises = result

    def __prompt_for_user_values__(self):
        """
        Prompt for any needed user values and store total in
        self.-user_values.
        """
        self._user_values = self.prompt_user(self.header.prompts)
