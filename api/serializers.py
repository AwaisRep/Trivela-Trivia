from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import User, UserHistory, Trivia

class UserSerializer(serializers.ModelSerializer):
    ''' Serializer to allow for user creation and updating '''
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'password']

    def update(self, instance, validated_data):
        ''' Allow partial updates of the user, such as email and password '''
        instance.email = validated_data.get('email', instance.email)

        if 'password' in validated_data:
            password = validated_data['password']
            if password:  # Check if password is not empty.
                instance.password = make_password(password)

        instance.save()
        return instance

class HistorySerializer(serializers.ModelSerializer):
    ''' Serializer to retrieve a user's history '''
    username = serializers.SerializerMethodField()

    class Meta:
        model = UserHistory
        fields = ['username', 'matches_played', 'matches_won', 'matches_drawn', 'matches_lost', 'user_points'] # Attributes to return

    def get_username(self, obj):
        return obj.user.username