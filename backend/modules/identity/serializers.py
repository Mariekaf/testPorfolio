from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .managers import normalize_identity_email


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError({'non_field_errors': ['Champs de formulaire invalides.']})
        return super().to_internal_value(data)


class EmailSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return normalize_identity_email(value)


class PasswordFields(StrictSerializer):
    password = serializers.CharField(min_length=1, max_length=128, trim_whitespace=False, write_only=True)
    password_confirmation = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({'password_confirmation': ['Les mots de passe ne correspondent pas.']})
        user = self.context.get('user')
        if user is None:
            user = get_user_model()(email=attrs.get('email',''), first_name=attrs.get('first_name',''), last_name=attrs.get('last_name',''))
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'password': list(error.messages)}) from None
        return attrs


class RegistrationSerializer(EmailSerializer, PasswordFields):
    first_name = serializers.CharField(min_length=1, max_length=100)
    last_name = serializers.CharField(min_length=1, max_length=100)

    def validate_email(self, value):
        value = super().validate_email(value)
        if get_user_model().objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Cette adresse e-mail est déjà utilisée.')
        return value


class LoginSerializer(EmailSerializer):
    password = serializers.CharField(min_length=1, max_length=128, trim_whitespace=False, write_only=True)


class ResetConfirmSerializer(PasswordFields):
    uid = serializers.CharField(max_length=100, write_only=True)
    token = serializers.CharField(max_length=200, write_only=True)
