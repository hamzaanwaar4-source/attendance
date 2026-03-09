from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get("email", "")
        password = attrs.get("password", "")

        user = User.objects.filter(email=email).first()

        if user is None:
            raise serializers.ValidationError(
                {"detail": "No account found with this email address."}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"detail": "Invalid password. Please enter the correct password."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "This account has been deactivated. Contact your administrator."}
            )

        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        if hasattr(user, "employee"):
            token["employee_id"] = str(user.employee.id)
            token["role"] = user.employee.role
            token["full_name"] = user.employee.full_name
        return token


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
