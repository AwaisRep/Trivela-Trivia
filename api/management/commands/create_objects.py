from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from api.models import CareerBank, PlayerBank, TriviaBank, ClubBank, FormationBank
import traceback
import json

class Command(BaseCommand):
    help = 'Mass generate q/a'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file containing the questions and answers')

    def handle(self, *args, **options):
        json_file = options['json_file']

        with open(json_file, 'r') as file:
            data = json.load(file)

        for item in data['bank']: #Access the bank key in the JSON file
            for question, answers in item.items(): #Access the question and answers in each row of the bank
                try:
                    trivia = TriviaBank(question=question, answer=answers) # Create an instance of the model
                    trivia.full_clean()  # Validate the instance
                    trivia.save()  # Save the instance
                    self.stdout.write(self.style.SUCCESS(f'Successfully created trivia: {question}'))
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Failed to create trivia: {question}. Error: {e}'))