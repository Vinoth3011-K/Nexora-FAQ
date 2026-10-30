from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Public representation of the authenticated user.
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'email', 'name', 'first_name', 'last_name', 'date_joined']

    def get_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if full_name:
            return full_name
        return obj.first_name or obj.username or obj.email.split('@')[0]


class RegisterSerializer(serializers.Serializer):
    """
    Serializer for user registration with field and password confirmation validation.
    """
    name = serializers.CharField(
        required=True, 
        max_length=150, 
        allow_blank=False,
        trim_whitespace=True,
        error_messages={'blank': 'Full name is required.', 'required': 'Full name is required.'}
    )
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={'blank': 'Email address is required.', 'invalid': 'Please enter a valid email address.'}
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'blank': 'Password is required.',
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'blank': 'Please confirm your password.'}
    )

    def validate_email(self, value):
        clean_email = value.strip().lower()
        if User.objects.filter(email__iexact=clean_email).exists() or User.objects.filter(username__iexact=clean_email).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return clean_email

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        # Validate password strength with Django built-in validators
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "password": list(e.messages)
            })

        return data

    def create(self, validated_data):
        name = validated_data['name'].strip()
        email = validated_data['email'].strip().lower()
        password = validated_data['password']

        # Split full name into first_name and last_name
        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Securely create user using create_user which hashes passwords with PBKDF2/Argon2
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer validating login credentials via email and password.
    """
    email = serializers.CharField(
        required=True, 
        allow_blank=False,
        error_messages={'blank': 'Email address is required.'}
    )
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'},
        error_messages={'blank': 'Password is required.'}
    )

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            raise serializers.ValidationError("Please provide both email address and password.")

        # Find user by case-insensitive email or username
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            user = User.objects.filter(username__iexact=email).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid email address or password.")

        if not user.is_active:
            raise serializers.ValidationError("Your account has been disabled. Please contact support.")

        data['user'] = user
        return data
