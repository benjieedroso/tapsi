from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['restaurant_id'] = user.restaurant.id if user.restaurant else None
        token['display_name'] = user.display_name

        return token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'restaurant', 'display_name']