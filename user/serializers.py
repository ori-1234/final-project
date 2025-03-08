from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, LoginHistory


# User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 
                  'phone_number', 'created_at',
                  'first_name', 'last_name')
        read_only_fields = ('created_at','id')