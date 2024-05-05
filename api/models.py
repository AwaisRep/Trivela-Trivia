from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import JSONField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

year_validator = RegexValidator(regex=r'^\d{4}$', message="Enter a valid year in YYYY format") # Simple regex pattern to validate the year of a club's season

class CustomUserManager(BaseUserManager):
    ''' Custom user model manager to create users/admins '''

    def create_user(self, username, email, password=None, **extra_fields):
        '''
        Create and save a User with the given username, email, and password.
        '''
        if not username:
            raise ValueError(_('The Username must be set'))
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        '''
        Create and save a SuperUser with the given username, email, and password.
        '''
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    ''' Custom user model where username is the primary identifier, not email '''

    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']  # Email is required, but not the primary identifier

    objects = CustomUserManager()

    def __str__(self):
        ''' String representation of the user '''
        return self.username
    
class UserHistory(models.Model):
    ''' Model to store user history information '''
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True) # User is the primary key

    # Fields all begin from 0
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    matches_drawn = models.IntegerField(default=0)
    matches_lost = models.IntegerField(default=0)

    user_points = models.IntegerField(default=0)


    def __str__(self):
        ''' String representation of the user history '''
        return f'{self.user.email} - History'

class UserChannel(models.Model):
    ''' Model to store the channel name for a user in a trivia session '''
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username + " - " + self.channel_name
        
class PlayedGames(models.Model):
    ''' Tracks which static games the user has played, to prevent point farming '''

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='played_games')
    game_type = models.CharField(max_length=100) # The particular type of game they played
    game_id = models.IntegerField() # The id of that game
    completed = models.BooleanField(default=False)  # Indicates if the game was completed

    class Meta:
        unique_together = ('user', 'game_type', 'game_id') # Ensure the user can only play a game once for that particular type (e.g. Box2Box)

    def __str__(self):
        completion_status = "completed" if self.completed else "in progress"
        return f'{self.user.username} - {self.game_type} Game ID {self.game_id} ({completion_status})'

    
class MatchmakingQueue(models.Model):
    ''' Model to store users in the matchmaking queue '''
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class Trivia(models.Model):
    ''' Model to store the trivia game session between two users '''

    created_at = models.DateTimeField(auto_now_add=True) # Creation time
    gameID = models.AutoField(primary_key=True)
    statistics_updated = models.BooleanField(default=False)  # Tracker to see if we've already finalised the game

    player_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playerOne")
    player_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playerTwo") # The two players against each other

    #Game state fields
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Point fields cannot exceed a maximum of 10 (otherwise we know there's tampering occuring)
    score_playerOne = models.IntegerField(default=0, validators=[MaxValueValidator(10)])
    score_playerTwo = models.IntegerField(default=0, validators=[MaxValueValidator(10)])

    result = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Winner", null=True, default=None)

    def __str__(self):
        ''' String representation of the game '''
        return f"Game {self.gameID}: {self.player_one.username} vs {self.player_two.username if self.player_two else 'CPU'}"

    def finalize_game(self):
        ''' Finalise the game statistics once the game is over '''
        if self.statistics_updated:  # If the statistics have already been updated, return immediately
            return
        self.statistics_updated = True  # Set the flag to True

        # Get the UserHistory models for player_one and player_two, creating them if they don't exist
        user_historyOne, created = UserHistory.objects.get_or_create(user=self.player_one)
        user_historyTwo, created = UserHistory.objects.get_or_create(user=self.player_two)

        # Determine the winner or a draw
        if self.score_playerOne > self.score_playerTwo:
            winner = user_historyOne
            loser = user_historyTwo
        elif self.score_playerOne < self.score_playerTwo:
            winner = user_historyTwo
            loser = user_historyOne
        else:
            winner = None  # It's a draw

        # Update the result
        self.result = winner.user if winner else None

        # Increase in matches played
        user_historyOne.matches_played += 1
        user_historyTwo.matches_played += 1

        if winner:
            # Relevant win increment
            winner.matches_won += 1
            # Increment in total points if they won
            winner.user_points += 2

            # Relevant loss increment
            loser.matches_lost += 1
        else:
            # It's a draw, increase draws for both players
            user_historyOne.matches_drawn += 1
            user_historyTwo.matches_drawn += 1
            # Increment in total points if it's a draw
            user_historyOne.user_points += 1
            user_historyTwo.user_points += 1

        # Save the changes
        user_historyOne.save()
        user_historyTwo.save()
        self.save()


class BoxToBox(models.Model):
    ''' Model to store the session of a box to box game '''

    gameID = models.IntegerField() #Game session id
    user = models.ForeignKey(User, on_delete=models.CASCADE) #User assigned to game session

    #Game fields - 6 clubs, 3 per axis
    club_x1 = models.CharField(max_length=100)
    club_x2 = models.CharField(max_length=100)
    club_x3 = models.CharField(max_length=100)
    club_y1 = models.CharField(max_length=100)
    club_y2 = models.CharField(max_length=100)
    club_y3 = models.CharField(max_length=100)

    correct_scores = models.IntegerField(default=0) #Amount guessed correctly
    guesses = models.IntegerField(default=0) #Amount of attempts used (lower is better)

    points_received = models.IntegerField(default=0, validators=[MaxValueValidator(10)]) #Amount of points earnt for the game

    def save(self, *args, **kwargs):
        ''' Ensure no tampering, as a user cannot achieve more than 10 points '''
        if self.points_received > 10:

            raise ValidationError("Points achieved cannot exceed 10")
        
        self.full_clean()
        super(BoxToBox, self).save(*args, **kwargs)

    def __str__(self):
        return f"BoxToBox session\n Correct: {self.correct_scores}\n Guesses: {self.guesses}"


class CareerPath(models.Model):
    ''' Model to store the session of a career path game '''

    gameID = models.IntegerField() #Game session id
    user = models.ForeignKey(User, on_delete=models.CASCADE) # User assigned to game session
    player_guess = models.CharField(max_length=100) # Player to be guessed
    guesses = models.IntegerField(default=0) # Amount of attempts used
    result = models.BooleanField(default=False)

    points_received = models.IntegerField(default=0, validators=[MaxValueValidator(1)]) # Points earned for the game

    def save(self, *args, **kwargs):
        ''' Ensure no tampering, as a user cannot achieve more than 1 point'''
        if self.points_received > 1:
            raise ValidationError("Points achieved cannot exceed 1")
        
        self.full_clean()
        super(CareerPath, self).save(*args, **kwargs)

    def __str__(self):
        return f"CareerPath - Player: {self.player_guess}, Guesses: {self.guesses}, Guessed: {self.result}"



class GuessTheSide(models.Model):
    ''' Model to store the session of a guess the side game '''
    gameID = models.IntegerField() #Game session id
    user = models.ForeignKey(User, on_delete=models.CASCADE) #User assigned to game session

    # Game fields
    team_guess = models.CharField(null=False, max_length=100)
    team_description = models.CharField(max_length=250)

    guesses = models.IntegerField(default=0) #Amount of attempts used (lower is better)
    correct_scores = models.IntegerField(default=0) #Amount guessed correctly
    result = models.BooleanField(default=False)

    points_received = models.IntegerField(default=0, validators=[MaxValueValidator(11)]) #Amount of points earnt for the game

    def save(self, *args, **kwargs):
        ''' Ensure no tampering, as a user cannot achieve more than 11 points '''
        if self.points_received > 11:
            raise ValidationError("Points achieved cannot exceed 11")
        
        self.full_clean()
        super(GuessTheSide, self).save(*args, **kwargs)

    def __str__(self):
        return f"GuessTheSide\n Team: {self.team_guess}\n Guesses: {self.guesses}\n Guessed: {self.result}"
    
#Answer models (Banks)
    
class TriviaBank(models.Model):
    ''' Model to store the trivia questions and answers '''
    question = models.CharField(max_length=250)
    answer = ArrayField(models.CharField(max_length=250), default=list, blank=True)

    def __str__(self):
        ''' String representation of the trivia question '''
        return self.question

class ClubBank(models.Model):
    ''' Model to store the club names for guess the side, and their description '''
    team_name = models.CharField(max_length=250)
    description = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.team_name} - {self.description}" 

class PlayerBank(models.Model):
    ''' Model to store the player names for career path '''
    player_names = ArrayField(models.CharField(max_length=250), default=list, blank=True) # A player can have multiple names they are known by

    def __str__(self):
        return ', '.join(self.player_names)
    
class CareerBank(models.Model):
    ''' Model to store the career path information for a single club '''

    player = models.ForeignKey(PlayerBank, related_name='careers', on_delete=models.CASCADE)
    team_name = models.CharField(max_length=250)
    appearances = models.IntegerField()
    goals = models.IntegerField()
    assists = models.IntegerField()
    is_loan = models.BooleanField(default=False)
    season = models.CharField(max_length=4, validators=[year_validator], help_text="Enter the year in YYYY")

    def __str__(self):
        return self.team_name
    
class FormationBank(models.Model):
    ''' Model to store the entire formations for guess the side '''
    club = models.ForeignKey(ClubBank, on_delete=models.CASCADE)
    player_names = ArrayField(models.CharField(max_length=250), default=list, blank=True)
    position = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.club} - {self.player_names}"
    
class DataLoadStatus(models.Model):
    ''' Simple model to determine whether the initial data required for the games has been read. 
    The loaddata function should only ever run once to populate the database with the required data '''
    data_loaded = models.BooleanField(default=False)