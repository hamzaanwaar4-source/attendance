from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import CustomTokenObtainPairSerializer, ChangePasswordSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated successfully."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {"id": user.id, "email": user.email, "is_superuser": user.is_superuser}
        if hasattr(user, "employee"):
            emp = user.employee
            data.update({
                "employee_id": str(emp.id),
                "full_name": emp.full_name,
                "role": emp.role,
                "department": emp.department.name if emp.department else None,
                "job_title": emp.job_title,
                "profile_picture": request.build_absolute_uri(emp.profile_picture.url) if emp.profile_picture else None,
            })
        return Response(data)
