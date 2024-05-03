import json
import glob
import os
from pathlib import Path
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.views import View
from django.conf import settings
from django.core.cache import cache
from django.contrib import auth
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.db import models
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, UserHistory, BoxToBox, GuessTheSide, CareerPath, PlayedGames, PlayerBank, CareerBank, ClubBank, FormationBank
from .serializers import UserSerializer, HistorySerializer


from .forms import loginForm, signupForm

appname = "trivelaTrivia"


def main_spa(request: HttpRequest) -> HttpResponse:
    ''' Provides main area content '''
    return render(request, 'api/spa/index.html', {})

def signup_view(request):
    ''' Handles sign up logic '''

    if request.method == "POST":
        form = signupForm(request.POST, request.FILES)

        if form.is_valid():
            
            user = form.save()
            login(request, user, backend='api.backends.EmailAuthBackend') # Custom backend served to login via email

            return HttpResponseRedirect('http://localhost:8000/login/')
    else:
        form = signupForm()
    return render(request, 'api/spa/api/auth/signup.html', {'form': form})


def login_view(request):
    ''' Handles login logic '''

    if request.method == "POST":

        form = loginForm(request.POST)
        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                return HttpResponseRedirect('http://localhost:5173/') # Redirect to the frontend on success
            else:
                # Add an error to the form
                form.add_error(None, 'Invalid email or password')
                return render(request, 'api/spa/api/auth/login.html', {'form': form})
                

    else:
        form = loginForm()

    return render(request, 'api/spa/api/auth/login.html', {'form': form})

       
def custom_logout(request):
    ''' Handles logout logic'''
    if request.method == "POST":

        if request.user.is_authenticated:

            logout(request)

            return HttpResponseRedirect('http://localhost:8000/login') # Redirect to the login page on success

    return HttpResponse("Method not allowed", status=405)

class UserProfileHistoryView(viewsets.ModelViewSet):
    '''
    API view to retrieve user profile and game history data.
    '''
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        '''
        Override the list method to provide combined user and history data.
        '''
        user = request.user # Current user
        user_serializer = UserSerializer(user)
        
        try:
            user_history, created = UserHistory.objects.get_or_create(user=user) # Create user history object if it doesn't exist
            history_serializer = HistorySerializer(user_history)
        except UserHistory.DoesNotExist:
            # Initialize an empty history if not available
            history_serializer = HistorySerializer(UserHistory())

        response_data = {
            'authenticated': True,
            'user': user_serializer.data,
            'history': history_serializer.data
        }

        return JsonResponse(response_data)


###########################################################################################

#GAME LOGIC CLASS BASED VIEWS

@method_decorator(login_required, name='dispatch')
class BoxToBoxView(View):
    ''' Handles the BoxToBox game logic '''

    def dispatch(self, request, *args, **kwargs):
        ''' Determine the particular route to take when a POST method occurs '''
        if 'game_id' in kwargs:
            return self.post(request, *args, **kwargs)
        elif 'session_id' in kwargs:
            return self.guess(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, game_id):
        '''Creates or resumes a BoxToBox game session. Returns a json response'''

        def continue_game(grid, existing_session):
            ''' Auxiliary function to continue an existing box to box session '''
            return JsonResponse({
                "message": "Existing Game Resumed",
                "session_id": existing_session.gameID,
                "clubs": {
                    "x1": existing_session.club_x1,
                    "x2": existing_session.club_x2,
                    "x3": existing_session.club_x3,
                    "y1": existing_session.club_y1,
                    "y2": existing_session.club_y2,
                    "y3": existing_session.club_y3,
                },
                "grid": grid,
                "guesses_left": 10 - existing_session.guesses,
            }, status=200)
        
        def start_new_game(game_id):
            ''' Auxiliary function to start a new box to box game session'''
            if PlayedGames.objects.filter(user=request.user, game_id=game_id, game_type='box2box', completed=True).exists(): # Guarantee the game is not already completed
                return JsonResponse({"error": "This game has already been completed."}, status=403)
            try:
                game_reference = get_new_game("box2box", game_id) # Retrieve the game details from the JSON file
                if game_reference is None:
                    return JsonResponse({"error": "Game not found."}, status=404) # Game doesn't exist

                # Initialise the game session with the clubs
                box_to_box_session = BoxToBox.objects.create(
                    user=request.user,
                    gameID=game_id,
                    club_x1=game_reference['clubs']['x1'],
                    club_x2=game_reference['clubs']['x2'],
                    club_x3=game_reference['clubs']['x3'],
                    club_y1=game_reference['clubs']['y1'],
                    club_y2=game_reference['clubs']['y2'],
                    club_y3=game_reference['clubs']['y3'],
                )

                # Set the cache for the answers and grid state (a user has 24 hours to complete the game otherwise it resets)
                answers_key = f"answers_box2box_{box_to_box_session.gameID}_{request.user.id}" # Cache key is based on game type -> game id -> user id (Always guarantees uniqueness)
                grid_key = f"grid_{box_to_box_session.gameID}_{request.user.id}" # Grid cache is only used in box to box, so we don't need to further specify the game type
                cache.set(answers_key, game_reference['answers'], timeout=86400)
                grid_initial_state = {k: False for k in game_reference['answers'].keys()}
                cache.set(grid_key, grid_initial_state, timeout=86400)

                return JsonResponse({
                    "message": "Game Started",
                    "session_id": box_to_box_session.gameID,
                    "clubs": game_reference['clubs'],
                    "grid": grid_initial_state,
                    "guesses_left": 10,
                }, status=201)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        # Get the data for whether the game has already been started or completed
        completed_game = PlayedGames.objects.filter(user=request.user, game_id=game_id, game_type="box2box").first() # Completed?
        existing_session = BoxToBox.objects.filter(user=request.user, gameID=game_id).first() # Started before?

        #First check if the game is completed
        if completed_game:
            if completed_game.completed == True:
                correct_scores = existing_session.correct_scores
                # If the user won, then give their relevant message
                if correct_scores == 9:
                    result_message = 'Game over. You won!'
                else:
                    result_message = f'Game over. You lost. Correct Scores: {correct_scores}'

                return JsonResponse({
                    "message": result_message,
                    "game_over": True,
                    "correct_scores": correct_scores,
                    "guesses_left": 0,
                    "clubs": {
                        "x1": existing_session.club_x1,
                        "x2": existing_session.club_x2,
                        "x3": existing_session.club_x3,
                        "y1": existing_session.club_y1,
                        "y2": existing_session.club_y2,
                        "y3": existing_session.club_y3,
                    },
                    "grid": {k: False for k in range(9)}
                }) # Populate the necessary data to view the clubs that were answered
            
            else:
                return JsonResponse({'error': 'Unfortunately, there was an error processing your request'})

        #Then check if the game has already been started before
        elif existing_session:

            #Try to obtain any previously stored cache values
            grid_key = f"grid_{existing_session.gameID}_{request.user.id}"
            grid = cache.get(grid_key)
            answers_key = f"answers_box2box_{existing_session.gameID}_{request.user.id}"
            answers = cache.get(answers_key)

            #If a cache that was set for either the grid or answers, no longer exists, then we start a new game since the previous expired (24 hours are up)
            if not answers or not grid:

                existing_session.delete()
                return start_new_game(existing_session)
            
            else: #Otherwise pick up where the user left off
                return continue_game(grid, existing_session)
        else:
            return start_new_game(game_id) # If the game reset or has never been accessed, start a new game

        
            
    def guess(self, request, session_id):
        '''Handles the guess made by a user, updates the grid state, and returns a json response'''

        if not request.user.is_authenticated: # Only authenticated users can play the game
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        try: # Attempt to locate the session
            box_to_box_session = BoxToBox.objects.get(gameID=session_id, user=request.user)
            
            # Check if the game is already finished
            if box_to_box_session.guesses >= 10:
                return JsonResponse({
                    'game_over': True,
                    'message': 'Maximum guesses reached. Game over.'
                }, status=200)

            guess_data = json.loads(request.body)
            user_guess = guess_data.get('guess', '') # User guess

            # Retrieve cached answers and grid state
            answers_key = f"answers_box2box_{session_id}_{request.user.id}"
            grid_key = f"grid_{session_id}_{request.user.id}"
            answers = cache.get(answers_key)
            grid = cache.get(grid_key)

            if not answers or not grid:
                return JsonResponse({'error': 'Game session expired or not found.'}, status=404)

            # Iterate through the answers to check if the user's guess is correct
            correct = False
            for coord, possible_answers_lists in answers.items():
                for possible_answers in possible_answers_lists:
                    # Convert both to lowercase before comparing
                    if user_guess.lower() in (answer.lower() for answer in possible_answers) and not grid[coord]: # Make sure the check is case-insesitive and that the answer hasn't been guessed before
                        grid[coord] = True
                        correct = True
                        box_to_box_session.correct_scores += 1
                        break  # Break if the correct answer is found to avoid redundant checks
                if correct:  # Break the outer loop as well if an answer has been found
                    break

            # Update game variables
            box_to_box_session.guesses += 1
            box_to_box_session.save()

            # Update cache with the new grid state (new 24 hour timer set on guess)
            cache.set(grid_key, grid, timeout=86400)
            cache.set(answers_key, answers, timeout=86400)

            game_over = box_to_box_session.guesses >= 10 or all(value for value in grid.values()) # Check if the guesses are used up or all answers are correct
            response_data = {
                'correct': 'yes' if correct else 'no',
                'grid': grid,
                'guesses_left': 10 - box_to_box_session.guesses,
                'game_over': game_over,
            }

            if game_over:
                self.finalize_game(session_id, request.user) # Finalise the game session

                if box_to_box_session.correct_scores == 9:
                    result_message = 'Game over. You won!'
                else:
                    result_message = f'Game over. You lost. Correct Scores: {box_to_box_session.correct_scores}'

                response_data.update({
                    'game_over': True,
                    'message': result_message
                })

            return JsonResponse(response_data)
        
        except BoxToBox.DoesNotExist:
            return JsonResponse({'error': 'Game session not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def finalize_game(self, session_id, user):
        ''' Handle game completion and result updates once the game is finished '''
        try:
            box_to_box_session = BoxToBox.objects.get(gameID=session_id, user=user)
            if box_to_box_session.guesses < 10 and not box_to_box_session.correct_scores == 9:
                return  # Ensure game is truly over before finalizing
            
            # Mark the game as completed
            PlayedGames.objects.update_or_create(
                user=user,
                game_id=session_id,
                game_type='box2box',
                defaults={'completed': True}
            )

            # Retrieve or create the user's history
            user_history, created = UserHistory.objects.get_or_create(user=user)
            # Update history based on game completion
            user_history.matches_played += 1
            if box_to_box_session.correct_scores == 9:
                user_history.matches_won += 1
                user_history.user_points += box_to_box_session.points_received
            else:
                user_history.matches_lost += 1
            user_history.save()

            # Clean up cache after game completion
            cache.delete_many([
                f"answers_box2box_{session_id}_{user.id}",
                f"grid_{session_id}_{user.id}"
            ])

        except BoxToBox.DoesNotExist:
            pass

    def get(self, request):
        ''' Retrieve all games that can be played '''
        if request.user.is_authenticated:
            
            return get_all_games(request, "box2box")
        
        else:
            return HttpResponse(403)




@method_decorator(login_required, name='dispatch')
class CareerPathView(View):

    def dispatch(self, request, *args, **kwargs):
        if 'game_id' in kwargs:
            return self.post(request, *args, **kwargs)
        elif 'session_id' in kwargs:
            return self.guess(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, game_id):
        ''' Creates or resumes a CareerPath game session. Returns a JSON response. '''

        def dispatch(self, request, *args, **kwargs):
            if 'game_id' in kwargs:
                return self.post(request, *args, **kwargs)
            elif 'session_id' in kwargs:
                return self.guess(request, *args, **kwargs)
            return super().dispatch(request, *args, **kwargs)

        def continue_game(existing_session):
            ''' Auxiliary function to continue an existing career path session '''
            get_clubs = CareerBank.objects.filter(player_id=existing_session.gameID).values('team_name', 'appearances', 'goals', 'assists', 'is_loan', 'season') # Get the players clubs and stats
            clubs_list = list(get_clubs)
            if not clubs_list:
                return JsonResponse({"error": "Game not found."}, status=404)
            
            return JsonResponse({
                "message": "Existing Game Resumed",
                "session_id": existing_session.gameID,
                "career_path": clubs_list,
                "guesses_left": 5 - existing_session.guesses,
            }, status=200) # Return the game data

        def start_new_game(game_id):
            ''' Auxiliary function to start a new career path session '''
            if PlayedGames.objects.filter(user=request.user, game_id=game_id, game_type='careerPath', completed=True).exists():
                return JsonResponse({"error": "This game has already been completed."}, status=403)
            
            player = PlayerBank.objects.filter(id=game_id).first() # Attempt to retrieve the player to be guessed by the id
            get_clubs = CareerBank.objects.filter(player_id=player.id).values('team_name', 'appearances', 'goals', 'assists', 'is_loan', 'season') # Get all their clubs and stats
            clubs_list = list(get_clubs)
            if not clubs_list:
                return JsonResponse({"error": "Game not found."}, status=404)
            
            # Create the new row in the CareerPath table
            career_path_session = CareerPath.objects.create(
                user=request.user,
                gameID=game_id,
                player_guess = player.player_names
            )

            return JsonResponse({
                "message": "Game Started",
                "session_id": game_id,
                "career_path": clubs_list,
                "guesses_left": 5,
            }, status=200) # Return the initial game data

        # Check for an existing game session that is not finished
        completed_game = PlayedGames.objects.filter(user=request.user, game_id=game_id, game_type="careerPath").first()
        existing_session = CareerPath.objects.filter(user=request.user, gameID=game_id).first()

        if completed_game:
            if completed_game.completed == True:
                result = existing_session.result
                
                player = PlayerBank.objects.filter(id=game_id).values('player_names')
                get_clubs = CareerBank.objects.filter(player_id=game_id).values('team_name', 'appearances', 'goals', 'assists', 'is_loan', 'season')
                clubs_list = list(get_clubs)
                player_names = [name.lower() for entry in player for name in entry['player_names']] # Get the player's name in a lower case manner

                if not clubs_list:
                    return JsonResponse({"error": "Game not found."}, status=404)

                if result == True:
                    result_message = f'Game over. You won! It was {player_names[0]}'
                else:
                    result_message = f'Game over. You lost. It was {player_names[0]}'

                return JsonResponse({
                    "message": result_message,
                    "session_id": game_id,
                    "career_path": clubs_list,
                    "guesses_left": 0,
                    'game_over': True,
                }, status=200)
            else:
                return JsonResponse({'error': 'Unfortunately, there was an error processing your request'})
            
        elif existing_session:
            return continue_game(existing_session)
        else:
            return start_new_game(game_id)

    def guess(self, request, session_id):
        ''' Handles the guess made by a user, returns a JSON response. '''
        try:
            career_path_session = CareerPath.objects.get(gameID=session_id, user=request.user)
            if career_path_session.guesses >= 5 or career_path_session.result:
                return JsonResponse({'game_over': True, 'message': 'No more guesses allowed or game already concluded.'}, status=200)

            guess_data = json.loads(request.body)
            user_guess = guess_data.get('guess', '').strip()

            correct_answers = PlayerBank.objects.filter(id=session_id).values('player_names')
            player_names = [name.lower() for entry in correct_answers for name in entry['player_names']]

            if correct_answers is None:
                return JsonResponse({'error': 'Game session expired or not found.'}, status=404)

            correct = user_guess.lower() in player_names # Check the guess against the correct answers in a case-insensitive manner
            if correct:
                career_path_session.result = True
                career_path_session.points_received += 1  # 1 point for a successfull game
                result_message = f'Game over. You won! It was {player_names[0]}'
            else:
                result_message = f'Game over. You lost. It was {player_names[0]}'

            career_path_session.guesses += 1
            career_path_session.save()

            game_over = career_path_session.guesses >= 5 or correct # Game is over if the guesses are exceeded or the correct answer is found
            response_data = {
                'correct': 'yes' if correct else 'no',
                'guesses_left': 5 - career_path_session.guesses,
                'game_over': game_over
            }

            if game_over:
                self.finalize_game(session_id, request.user) # Finalize the game session once it is over
                
                response_data.update({
                    'game_over': True,
                    'message': result_message,
                    'total_user_points': career_path_session.points_received,
                    'guesses_left': 0
                }) # Send the final message to be returned to the user

            return JsonResponse(response_data)
            
        except CareerPath.DoesNotExist:
            return JsonResponse({'error': 'Game session not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def finalize_game(self, session_id, user):
        ''' Finalizes game completion and updates results. '''
        try:
            career_path_session = CareerPath.objects.get(gameID=session_id, user=user) # Attempt to locat the game
            if not career_path_session.result and career_path_session.guesses < 5:
                return  # Ensure game is really over before marking as completed


            PlayedGames.objects.update_or_create(
                user=user,
                game_id=session_id,
                game_type='careerPath',
                defaults={'completed': True}
            ) # Set the game as completed

            user_history, created = UserHistory.objects.get_or_create(user=user)
            user_history.matches_played += 1
            if career_path_session.result: # 1 point for a win, otherwise a loss is added
                user_history.matches_won += 1
                user_history.user_points += career_path_session.points_received
            else:
                user_history.matches_lost += 1
            user_history.save()

        except CareerPath.DoesNotExist:
            pass
    
    def get(self, request):
        ''' Retrieve all games that can be played '''

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return HttpResponse(status=403)

        try:
            # Fetch all players
            all_players = PlayerBank.objects.all()
            games_info = []

            for player in all_players:
                # Check if there's any 
                played_games = PlayedGames.objects.filter(
                    user=request.user, 
                    game_type='careerPath', 
                    game_id=player.id  # Assuming the club.id serves as game_id
                )

                # Determine if the game has been played
                has_been_played = played_games.exists()
                if has_been_played:
                    message = "completed"
                else:
                    message = "available"

                games_info.append({
                    "game_id": player.id, 
                    "status": message
                })

            # Return the games as JSON response
            return JsonResponse({'games': games_info})

        except Exception as e:
            # Return error response if something goes wrong
            return JsonResponse({'error': 'An error occurred while fetching games: ' + str(e)}, status=500)



@method_decorator(login_required, name='dispatch')
class GuessTheSideView(View):
    ''' Handles the GuessTheSide game logic '''

    def dispatch(self, request, *args, **kwargs):
        if 'game_id' in kwargs:
            return self.post(request, *args, **kwargs)
        elif 'session_id' in kwargs:
            return self.guess(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, game_id):

        def continue_game(formation, existing_session):
            ''' Auxiliary function to continue an existing guess the side session '''

            # Get team data
            teamName = existing_session.team_guess
            teamDescription = existing_session.team_description

            return JsonResponse({
                "message": "Existing Game Resumed",
                "session_id": existing_session.gameID,
                "teamName": teamName,
                "teamDescription": teamDescription,
                "starting_eleven": formation,
                "guesses_left": 15 - existing_session.guesses,
            }, status=200) # Return previous data

        def start_new_game(game_id):
            ''' Auxiliary function to start a new guess the side session '''
            if PlayedGames.objects.filter(user=request.user, game_id=game_id, game_type='formations', completed=True).exists():
                return JsonResponse({"error": "This game has already been completed."}, status=403)

            club = ClubBank.objects.filter(id=game_id).first() # Attempt to retrieve the club that is to be played
            if not club:
                return JsonResponse({"error": "Game not found."}, status=404)

            formations = FormationBank.objects.filter(club_id=club.id).values('player_names', 'position') # Get the club's entire eleven
            starting_eleven = [{'position': f['position'], 'playerNames': f['player_names'], 'guessed': False} for f in formations] # Set the intitial state of the formation as not guessed

            guess_side_session = GuessTheSide.objects.create(
                user=request.user,
                gameID=game_id,
                team_guess=club.team_name,
                team_description=club.description
            )

            # Set the cache for the answers and formation state (a user has 24 hours to complete the game otherwise it resets)
            answers_key = f"answers_gts_{game_id}_{request.user.id}" # Cache key is based on game type -> game id -> user id (Always guarantees uniqueness)
            cache.set(answers_key, starting_eleven, timeout=86400)

            return JsonResponse({
                "message": "New Game Started",
                "session_id": guess_side_session.gameID,
                "teamName": club.team_name,
                "teamDescription": club.description,
                "starting_eleven": [{'position': f['position'], 'playerNames': f['player_names'] if f['guessed'] else [], 'guessed': f['guessed']} for f in starting_eleven],
                "guesses_left": 15,
            }, status=201) # Return initial game data


        completed_game = PlayedGames.objects.filter(user=request.user, game_id=game_id, game_type="formations").first()
        existing_session = GuessTheSide.objects.filter(user=request.user, gameID=game_id).first()

        if completed_game: # Check if the game is completed
            if completed_game.completed == True:
                correct_scores = existing_session.correct_scores
                if correct_scores == 11: # 11 players are to be guessed
                    result_message = 'Game over. You won!'
                else:
                    result_message = f'Game over. You lost. Correct Scores: {correct_scores}'

                finished_game = FormationBank.objects.filter(club_id=game_id).values('player_names', 'position')
                starting_eleven = [{"position": player["position"], "playerNames": player["player_names"]} for player in finished_game] # Return the entire eleven when the game is finished so the user knows
                club = ClubBank.objects.filter(id=game_id).first()

                return JsonResponse({
                    "message": result_message,
                    "game_over": True,
                    "correct_scores": correct_scores,
                    "teamName": club.team_name,
                    "teamDescription": club.description,
                    "starting_eleven": starting_eleven,
                    "guesses_left": 0,
                }) # Return the necessary data to view the players that weren't answered (if any)
            
            else:
                return JsonResponse({'error': 'Unfortunately, there was an error processing your request'})

        elif existing_session: # Check if the game has already been started before
            # Retrieve any previously stored cache values
            answers_key = f"answers_gts_{existing_session.gameID}_{request.user.id}"
            starting_eleven = cache.get(answers_key, [])

            if not starting_eleven:
                existing_session.delete() # Delete the row if the cache has expired, and restart
                return start_new_game(game_id)
            else:
                formation = [{'position': f['position'], 'playerNames': f['playerNames'] if f['guessed'] else [], 'guessed': f['guessed']} for f in starting_eleven]
                return continue_game(formation, existing_session) # Otherwise continue where the user left off
        else:
            return start_new_game(game_id) # Start a new session if the game has never been accessed or has expired

    def guess(self, request, session_id):
        ''' Handles the guess made by a user, updates the formation state, and returns a JSON response. '''
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        try:
            guess_side_session = GuessTheSide.objects.get(gameID=session_id, user=request.user) # Obtain the active session
            if guess_side_session.guesses >= 15: # Check if the maximum guesses have been reached (15)
                return JsonResponse({'game_over': True, 'message': 'Maximum guesses reached. Game over.'}, status=200)

            guess_data = json.loads(request.body)
            user_guess = guess_data.get('guess', '') # Retrieve the user's guess

            answers_key = f"answers_gts_{session_id}_{request.user.id}"
            starting_eleven = cache.get(answers_key) # Obtain the formation state in cache
            if not starting_eleven:
                return JsonResponse({'error': 'Game session expired or not found.'}, status=404)

            # Check if any player in the starting eleven matches the user's guess
            correct = False
            for player in starting_eleven: # Iterate over the players in the starting eleven
                if user_guess.lower() in (name.lower() for name in player['playerNames']): # Check the guess against the player's names in a case-insensitive manner
                    if player['guessed'] != True:
                        player['guessed'] = True
                        correct = True
                        guess_side_session.correct_scores += 1

            cache.set(answers_key, starting_eleven, timeout=86400) # Set the cache with the updated formation state for another 24 hours
            guess_side_session.guesses += 1
            guess_side_session.save()

            return_formation = [{'position': f['position'], 'playerNames': f['playerNames'] if f['guessed'] else [], 'guessed': f['guessed']} for f in starting_eleven] # Updated formation state

            game_over = guess_side_session.guesses >= 15 or guess_side_session.correct_scores==11 # Check if the maximum guesses have been reached or all players have been guessed
            response_data = {
                'correct': 'yes' if correct else 'no',
                'guesses_left': 15 - guess_side_session.guesses,
                'game_over': game_over,
                'guessed_players': return_formation
            }

            if game_over:
                if guess_side_session.correct_scores == 11: # Decide result based on the number of correct guesses
                    result_message = 'Game over. You won!'
                    guess_side_session.result = True
                    guess_side_session.save()
                else:
                    result_message = f'Game over. You lost. Correct Scores: {guess_side_session.correct_scores}'

                self.finalize_game(session_id, request.user)
                full_eleven = [{"position": player["position"], "playerNames": player["playerNames"]} for player in starting_eleven]

                response_data.update({
                    'message': result_message,
                    'game_over': True,
                    'guessed_players': full_eleven
                }) # Return final message and the full starting eleven to the user (regardless of the result)

            return JsonResponse(response_data)

        except GuessTheSide.DoesNotExist:
            return JsonResponse({'error': 'Game session not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def finalize_game(self, session_id, user):
        ''' Finalizes game completion and updates results. '''
        try:
            guess_side_session = GuessTheSide.objects.get(gameID=session_id, user=user) # Retrieve the relevant game session
            if guess_side_session.guesses < 15 and not guess_side_session.correct_scores == 11:
                return  # Ensure game is truly over before finalizing
            
            answers_key = f"answers_gts_{session_id}_{user.id}"
            PlayedGames.objects.update_or_create(
                user=user,
                game_id=session_id,
                game_type='formations',
                defaults={'completed': True}
            ) # Mark the game as completed
            user_history, created = UserHistory.objects.get_or_create(user=user)
            user_history.matches_played += 1
            if guess_side_session.result:
                user_history.matches_won += 1
            else:
                user_history.matches_lost += 1
            user_history.user_points += guess_side_session.points_received
            user_history.save()
            cache.delete(answers_key) # Remove the cache after the game is completed

        except GuessTheSide.DoesNotExist:
            pass

    def get(self, request):
        ''' Retrieve all games that can be played '''

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return HttpResponse(status=403)

        try:
            # Fetch all games from ClubBank (assuming each game corresponds to a club)
            all_clubs = ClubBank.objects.all()
            games_info = []

            for club in all_clubs:
                # Check if there's any PlayedGames record for this club
                played_games = PlayedGames.objects.filter(
                    user=request.user, 
                    game_type='formations', 
                    game_id=club.id  # Assuming the club.id serves as game_id
                )

                # Determine if the game has been played
                has_been_played = played_games.exists()
                if has_been_played:
                    message = "completed"
                else:
                    message = "available"

                games_info.append({
                    "game_id": club.id, 
                    "status": message
                })

            # Return the games as JSON response
            return JsonResponse({'games': games_info})

        except Exception as e:
            # Return error response if something goes wrong
            return JsonResponse({'error': 'An error occurred while fetching games: ' + str(e)}, status=500)

###########################################################################################
#Utility Functions

def leaderboard(request):
    ''' View based function to retrieve current leaderboard ranking '''

    # Fetch all users' history and calculate win percentage using django's expression wrapper
    users_history = UserHistory.objects.annotate(
        win_percentage=models.ExpressionWrapper(
            models.F('matches_won') * 100.0 / models.Case(
                models.When(matches_played=0, then=1),
                default=models.F('matches_played')
            ),
            output_field=models.FloatField()
        )
    ).order_by('-matches_won')  # Order by matches won in descending order

    # Generate each user data
    leaderboard_data = [{
        'username': history.user.username,
        'matches_played': history.matches_played,
        'matches_won': history.matches_won,
        'matches_drawn': history.matches_drawn,
        'matches_lost': history.matches_lost,
        'total_points': history.user_points,
        'win_percentage': round(history.win_percentage, 2) # Round to 2 decimal places
    } for history in users_history] # Creates an array entry for every user in the game

    return JsonResponse({'leaderboard': leaderboard_data})

def get_new_game(game_type, game_id):
    ''' Find the game of choice based on the game type'''
    try:
        game_file_path = os.path.join(settings.BASE_DIR, 'api', game_type, f'{game_id}.json') # Access the api directory in the application
        with open(game_file_path, 'r') as game_file:
            game_data = json.load(game_file) # Attempt to load the game data stored in JSON
        return game_data
    except FileNotFoundError:
        return None
    except Exception as e:
        print("An error occurred while fetching the game: ", str(e))


def get_all_games(request, game_type):
    '''Return all the games available for one type in JSON format'''

    if game_type not in ["box2box", "careerPath", "formations"]: # Must be one of these three game types
        return JsonResponse({'error': 'Invalid game type provided'}, status=400)

    try:
        game_files_dir = os.path.join(settings.BASE_DIR, "api", str(game_type)) # Access the directory for the game type
        game_files = glob.glob(os.path.join(game_files_dir, "*.json")) # Use glob to match file patterns
        if not game_files:
            return JsonResponse({'error': 'No games found'}, status=404)

        game_names = [os.path.splitext(os.path.basename(file))[0] for file in game_files]
        games_info = [] # Holds all info about each game

        for game in game_names:
            status = "available"  # Default status
            # Assuming user is authenticated and the user object is available
            if request.user.is_authenticated:
                played_games = PlayedGames.objects.filter(user=request.user, game_type=game_type, game_id=int(game))
                if played_games.exists():
                    played_game = played_games.first()
                    status = "completed" if played_game.completed else "pending"
            games_info.append({"game_id": game, "status": status}) # Games are either available or completed

        return JsonResponse({'games': games_info})

    except Exception as e:
        return JsonResponse({'error': 'An error occurred while fetching games: ' + str(e)}, status=500)

###########################################################################################
class UserViewSet(viewsets.ModelViewSet):
    ''' Custom user view set that serialises user data and allows for creation/updates of users'''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] # Only logged in users can access this view

    def get_queryset(self):
        ''' Return the user object for the current authenticated user '''
        return User.objects.filter(pk=self.request.user.pk)

    def create(self, request, *args, **kwargs):
        ''' Create a new user '''
        instance = self.request.user
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        ''' Update the user object '''
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        ''' Partially update the user object (i.e. just email or password) ''' 
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
