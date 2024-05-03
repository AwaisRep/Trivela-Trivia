import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.conf import settings
from api.models import Trivia, TriviaBank, MatchmakingQueue, User, UserChannel, UserHistory
import time
from asgiref.sync import sync_to_async
from django.db.models import Prefetch

class MatchmakingConsumer(AsyncWebsocketConsumer):
    ''''
    Class that handles the matchmaking process for users. It adds users to the queue and pairs them with an opponent.
    '''

    async def connect(self):
        '''
        Called when the websocket is handshaking as part of the connection process.
        '''
        await self.accept()
        user = self.scope["user"]
        self.room_group_name = f'user_{user.id}'  # Creating a unique group name based on user ID
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.add_to_queue(user) # Add the user to the queue

    async def disconnect(self, close_code):
        '''Leave the group and queue when the socket is disconnected.'''
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.remove_from_queue(self.scope["user"])

    async def add_to_queue(self, user):
        '''Add the user to the matchmaking queue.'''

        user_in_queue, created = await self.get_or_create_queue_entry(user)
        if not created:
            await self.send(json.dumps({'message': 'You are already in the queue.'}))
            return

        opponent = await self.get_opponent(user) # Attempt to match them with an opponent already in the queue
        if opponent:
            await self.notify_users_game_started(user, opponent.user)  # Single call for both users to start
            await self.remove_users_from_queue([user, opponent.user]) # Remove both users from the queue once they're matched
        else:
            await self.send(json.dumps({'message': 'You are now in the waiting list. Searching for an opponent.'})) # Otherwise notify the user that they're in the queue

    async def notify_users_game_started(self, player_one, player_two):
        '''Notify both players that the game is starting.'''

        game_id = await self.create_game(player_one, player_two) # Create the game with both players, and retrieve game id
        game_start_message = {
            'url': f'/ws/trivia/{game_id}/', # Send the url to connect to that specific websocket
            'message': 'Game is starting. The timer is set to begin...',
            'gameStarted': True
        }

        # Notify both players using a single call each with direct dictionary passing
        await self.channel_layer.group_send(
            f'user_{player_one.id}',
            {
                'type': 'game_message',
                'message': game_start_message  # Pass the dictionary directly
            }
        )

        await self.channel_layer.group_send(
            f'user_{player_two.id}',
            {
                'type': 'game_message',
                'message': game_start_message  # Pass the dictionary directly
            }
        )

    # Receive message from room group
    async def game_message(self, event):
        '''Send the message to the client that the game is starting'''
        # Convert the message dictionary directly back to JSON for sending to the client
        message_json = json.dumps(event['message'])
        await self.send(text_data=message_json)

    # The following functions are database operations that run asynchronously as we need to clean up database connections
    @database_sync_to_async
    def get_or_create_queue_entry(self, user):
        '''Get or create a matchmaking queue entry for the user'''
        return MatchmakingQueue.objects.get_or_create(user=user)

    @database_sync_to_async
    def get_opponent(self, user):
        '''Get an opponent for the user from the matchmaking queue'''
        return MatchmakingQueue.objects.exclude(user=user).select_related('user').first()

    @database_sync_to_async
    def create_game(self, player_one, player_two):
        '''Create a new Trivia row with both players and return the game id.'''
        new_game = Trivia.objects.create(player_one=player_one, player_two=player_two, is_active=True)
        return new_game.gameID

    @database_sync_to_async
    def remove_users_from_queue(self, users):
        '''Remove the row of users from the matchmaking queue'''
        MatchmakingQueue.objects.filter(user__in=users).delete()

    @database_sync_to_async
    def remove_from_queue(self, user):
        '''Remove the user from the matchmaking queue if they leave the page or disconnect'''
        MatchmakingQueue.objects.filter(user=user).delete()


class TriviaGameConsumer(AsyncWebsocketConsumer):
    '''Class that handles the gameplay of a session between two users.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_data = {}  # Dictionary to store each user's data
        self.end_game_lock = asyncio.Lock() # Lock to prevent multiple calls to end_game (race)

    async def connect(self):
        '''Called when the users are ready to start playing the game'''

        self.room_group_name = f'game_{self.scope["url_route"]["kwargs"]["game_id"]}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if await self.check_game_ready(): # Guarantee the game is ready before starting
            await self.start_game() # Start the game

    async def disconnect(self, close_code):
        '''Called when the websocket is disconnected. Nullifies the game session'''
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        '''Called when a message is received from the client'''

        data = json.loads(text_data) # Unpack the data as a JSON object
        if data.get('action') == 'submit_answer':
            user = self.scope["user"] # Get the user who made the call
            if user not in self.user_data:  # Initialize the user's data if it's not already done
                self.user_data[user] = {'question_count': 0, 'correct_answers': 0, 'current_question_index': 0}

            if self.user_data[user]['question_count'] >= 10:  # If the user has already answered 10 questions
                await self.send(text_data=json.dumps({
                    'message': 'You have already answered all questions'
                }))
                return

            if self.game_end:  # If the game has ended, ignore the answer and return a message
                await self.send(text_data=json.dumps({
                    'message': 'Invalid game session'
                }))
                return

            await self.check_answer(data['answer'], data['question_id'], user)
            self.user_data[user]['question_count'] += 1  # Increment the question count after checking the answer

            if not self.game_end:  # If the game is not over
                if self.user_data[user]['current_question_index'] < len(self.questions) - 1:  # If there are more questions
                    self.user_data[user]['current_question_index'] += 1  # Increment the question index for the user
                    await self.send_question(self.questions[self.user_data[user]['current_question_index']], user)  # Send the next question
                else:
                    await self.send(text_data=json.dumps({
                        'message': 'You have answered all questions. Wait for the results.'
                    }))

    async def send_server_time(self):
        '''Send the server time to each client every second'''
        while not self.game_end: # Only send the tick if the game has not ended
            elapsed_time = time.time() - self.game_start_time
            remaining_time = max(60 - elapsed_time, 0)
            remaining_time_rounded = round(remaining_time)
            await self.send(text_data=json.dumps({
                'remaining_time': remaining_time_rounded
            }))
            await asyncio.sleep(1) # Wait for 1 second before sending the next tick

    async def start_game(self):
        '''Start the game session'''
        self.game_end = False  # Flag to indicate if the game has ended

        # Start the game timer for 60 seconds
        self.game_start_time = time.time()
        asyncio.create_task(self.end_game_timer())

        # Start sending remaining time every second
        asyncio.create_task(self.send_server_time())

        game = await self.get_game() # Fetch the game instance
        if game is not None:
            player_one = game.player_one.__str__()
            player_two = game.player_two.__str__()
            self.user_data[player_one] = {'question_count': 0, 'correct_answers': 0, 'current_question_index': 0}
            self.user_data[player_two] = {'question_count': 0, 'correct_answers': 0, 'current_question_index': 0}
            # Set the initial user data at the start of the game

        self.questions = await self.load_questions()  # Load the questions
        for user in self.user_data.keys():
            await self.send_question(self.questions[0], user)  # Send the first question to each user

        # Send the game start message
        await self.send(text_data=json.dumps({'message': 'The game has started. Go!'}))

    async def send_question(self, question, user):
        '''Send a question to a user'''
        await self.send(text_data=json.dumps({
            'question': question.question,
            'question_id': question.id,
            'index': self.user_data[user]['question_count']+1,
        }))

    async def check_answer(self, answer, question_id, user):
        '''Check if the answer is correct and update the score and index'''
        correct = await self.is_correct_answer(question_id, answer)
        if correct: # Modify relevant scoped variables if the answer is correct
            self.user_data[user]['correct_answers'] += 1
            await self.update_score(user)
        await self.send(text_data=json.dumps({
            'result': 'correct' if correct else 'incorrect',
            'question_count': self.user_data[user]['question_count'],
            'correct_answers': self.user_data[user]['correct_answers']
        }))

    async def end_game_timer(self):
        '''Delay the game end for 60 seconds after the game starts'''
        await asyncio.sleep(60)  # Wait for 60 seconds
        if not self.game_end:
            await self.end_game()

    async def end_game(self):
        '''End the game session and finalize the game result'''
        async with self.end_game_lock: # Acquire the lock to prevent multiple calls
            if self.game_end:  # If the game has already ended, return immediately
                return
            self.game_end = True  # Set the game end flag to True

            # Fetch the game instance and finalize it
            game = await self.get_game()
            await database_sync_to_async(game.finalize_game)()

            # Fetch the players from the game instance
            player_one = game.player_one
            player_two = game.player_two

            # Determine the game result message
            result = await database_sync_to_async(getattr)(game, 'result') # Ensure we use sync_to_async for consistency
            if result is not None:
                result = await database_sync_to_async(getattr)(result, 'username') # Get the winner's username (if any)

            # Possible cases for the winner/drawer
            if result == player_one.username:
                result_message = {
                    player_one.username: 'Nicely done! You won!',
                    player_two.username: 'Unlucky, you lost.'
                }
            elif result == player_two.username:
                result_message = {
                    player_one.username: 'Unlucky, you lost.',
                    player_two.username: 'Nicely done! You won!'
                }
            else:
                result_message = {
                    player_one.username: 'You drew! A point shared!',
                    player_two.username: 'You drew! A point shared!'
                }

            # Send the game over message to each player
            for user, message in result_message.items():
                await self.channel_layer.group_send(self.room_group_name, {  # Use the group name
                    'type': 'game_message',
                    'game_over': True,
                    'user': user,  # Add a 'user' field to the message
                    'message': message,
                    'remaining_time': 0,
                })

    async def is_correct_answer(self, question_id, answer):
        '''Check if the answer is correct for the given question id'''
        question = await sync_to_async(TriviaBank.objects.get)(id=question_id)
        correct_answers = question.answer
        return any(correct_answer.upper() == answer.upper() for correct_answer in correct_answers) # Make comparison case-insensitive

    async def get_game(self):
        '''Get the game instance id for the current game'''
        game_id = self.scope['url_route']['kwargs']['game_id']
        game = await database_sync_to_async(Trivia.objects.prefetch_related(
            Prefetch('player_one'),
            Prefetch('player_two'),
        ).get)(gameID=game_id) # Retrieve the particular game id for the session that exists between the two players
        return game
    
    async def game_message(self, event):
        '''Send the game message to the client based on the user scope'''
        if event['user'] == self.scope['user'].username:
            await self.send(text_data=json.dumps(event))

    @sync_to_async
    def get_result(self, game):
        '''Get the result of the game from the game instance in a consistent manner'''
        return game.result

    @database_sync_to_async
    def update_score(self, user):
        '''Update the score of the user in the game instance'''
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        try:
            game = Trivia.objects.get(gameID=game_id)
        except Trivia.DoesNotExist:
            return  # Handle the exception as appropriate for your application
        if user == game.player_one:
            game.score_playerOne += 1
        else:
            game.score_playerTwo += 1
        game.save()

    @database_sync_to_async
    def load_questions(self):
        '''Retrieve 10 random questions from the database'''
        return list(TriviaBank.objects.order_by('?')[:10])  # Randomly select 10 questions

    @database_sync_to_async
    def check_game_ready(self):
        '''Check if the row has been created in the Trivia model with game id'''
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        try:
            game = Trivia.objects.get(gameID=game_id)
        except Trivia.DoesNotExist:
            return False  # Return False if the game does not exist
        return game.player_one is not None and game.player_two is not None