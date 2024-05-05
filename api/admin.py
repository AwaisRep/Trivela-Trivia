from django.contrib import admin
from .models import User, Trivia, TriviaBank, ClubBank, PlayerBank, CareerBank, FormationBank, DataLoadStatus
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    ''' Custom User Admin to inherit the user model '''
    model = User
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

class TriviaAdmin(admin.ModelAdmin):
    ''' Custom admin for the Trivia model '''
    list_display = ('gameID', 'statistics_updated', 'player_one', 'player_two', 'is_active', 'score_playerOne', 'score_playerTwo')
    search_fields = ('gameID', 'player_one', 'player_two')

class TriviaBankAdmin(admin.ModelAdmin):
    ''' Custom admin for the TriviaBank model '''
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')

class ClubBankAdmin(admin.ModelAdmin):
    ''' Custom admin for the ClubBank model '''
    list_display = ('team_name', 'description')
    search_fields = ('team_name',)

class PlayerBankAdmin(admin.ModelAdmin):
    ''' Custom admin for the PlayerBank model '''
    list_display = ('player_names',)
    search_fields = ('player_names',)

class CareerBankAdmin(admin.ModelAdmin):
    ''' Custom admin for the CareerBank model '''
    list_display = ('player', 'team_name', 'appearances')
    search_fields = ('player__player_names', 'team_name')

class FormationBankAdmin(admin.ModelAdmin):
    ''' Custom admin for the FormationBank model '''
    list_display = ('club', 'player_names', 'position')
    search_fields = ('player_names',)

class DataLoadStatusAdmin(admin.ModelAdmin):
    ''' Custom admin for the DataLoadStatus model '''
    list_display = ('data_loaded',)
    search_fields = ('data_loaded',)

admin.site.register(User, CustomUserAdmin)  # Register models with the custom admin site
admin.site.register(Trivia, TriviaAdmin)
admin.site.register(TriviaBank, TriviaBankAdmin)
admin.site.register(ClubBank, ClubBankAdmin)
admin.site.register(PlayerBank, PlayerBankAdmin)
admin.site.register(CareerBank, CareerBankAdmin)
admin.site.register(FormationBank, FormationBankAdmin)
admin.site.register(DataLoadStatus, DataLoadStatusAdmin)