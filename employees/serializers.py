from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model

from employees.models import Employee, Compensation, DisciplinaryRecord, Department, Batch


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "employee_count"]

    def get_employee_count(self, obj):
        return obj.employees.count()


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ["id", "name"]


class BaseEmployeeSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    def get_profile_picture(self, obj):
        if not obj.profile_picture:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.profile_picture.url)
        return obj.profile_picture.url


class EmployeeListSerializer(BaseEmployeeSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    batch_name = serializers.CharField(source="batch.name", read_only=True, default=None)
    reports_to_name = serializers.CharField(source="reports_to.full_name", read_only=True, default=None)
    employee_id_display = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = [
            "id", "employee_id_display", "official_email", "full_name", "role",
            "department", "department_name", "batch", "batch_name",
            "job_title", "employment_status", "join_date",
            "reports_to", "reports_to_name", "profile_picture",
        ]


class EmployeeCreateSerializer(BaseEmployeeSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Employee
        fields = [
            "official_email", "full_name", "father_name", "role",
            "department", "batch", "reports_to",
            "dob", "gender", "cnic", "blood_group", "marital_status",
            "personal_phone", "personal_email",
            "current_address", "permanent_address",
            "emergency_contact_name", "emergency_contact_number", "emergency_contact_relation",
            "job_title", "employment_status", "join_date",
            "highest_qualification", "field_of_study", "institution", "graduation_year",
            "prev_company", "prev_designation", "years_experience",
            "profile_picture", "password",
        ]

    def validate_official_email(self, value):
        User = get_user_model()
        if Employee.objects.filter(official_email=value).exists() or User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        User = get_user_model()
        password = validated_data.pop("password", None)
        official_email = validated_data.get("official_email")

        user = User.objects.create_user(
            email=official_email,
            password=password,
        )
        validated_data["user"] = user

        employee = super().create(validated_data)

        Compensation.objects.get_or_create(employee=employee)
        return employee


class EmployeeDetailSerializer(BaseEmployeeSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    batch_name = serializers.CharField(source="batch.name", read_only=True, default=None)
    reports_to_name = serializers.CharField(source="reports_to.full_name", read_only=True, default=None)
    employee_id_display = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = [
            "id", "employee_id_display", "official_email", "full_name", "father_name",
            "role", "department", "department_name", "batch", "batch_name",
            "reports_to", "reports_to_name",
            "dob", "gender", "cnic", "blood_group", "marital_status", "profile_picture",
            "personal_phone", "personal_email",
            "current_address", "permanent_address",
            "emergency_contact_name", "emergency_contact_number", "emergency_contact_relation",
            "job_title", "employment_status", "join_date", "exit_date",
            "highest_qualification", "field_of_study", "institution", "graduation_year",
            "prev_company", "prev_designation", "years_experience",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "employee_id_display", "created_at", "updated_at"]


class EmployeeProfileSerializer(BaseEmployeeSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    batch_name = serializers.CharField(source="batch.name", read_only=True, default=None)
    reports_to_name = serializers.CharField(source="reports_to.full_name", read_only=True, default=None)
    employee_id_display = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = [
            "id", "employee_id_display", "official_email", "full_name", "father_name",
            "role", "department_name", "batch_name", "reports_to_name",
            "dob", "gender", "cnic", "blood_group", "marital_status", "profile_picture",
            "personal_phone", "personal_email",
            "current_address", "permanent_address",
            "emergency_contact_name", "emergency_contact_number", "emergency_contact_relation",
            "job_title", "employment_status", "join_date", "exit_date",
            "highest_qualification", "field_of_study", "institution", "graduation_year",
            "prev_company", "prev_designation", "years_experience",
        ]
        read_only_fields = [
            "id", "employee_id_display", "official_email", "role",
            "department_name", "batch_name", "reports_to_name",
            "job_title", "employment_status", "join_date", "exit_date",
        ]


class EmployeeUpdateSerializer(BaseEmployeeSerializer):
    class Meta:
        model = Employee
        fields = [
            "full_name", "father_name", "dob", "gender", "cnic",
            "blood_group", "marital_status", "profile_picture",
            "personal_phone", "personal_email",
            "current_address", "permanent_address",
            "emergency_contact_name", "emergency_contact_number", "emergency_contact_relation",
            "role", "department", "batch", "reports_to",
            "job_title", "employment_status", "join_date", "exit_date",
            "highest_qualification", "field_of_study", "institution", "graduation_year",
            "prev_company", "prev_designation", "years_experience",
        ]


class CompensationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = Compensation
        fields = [
            "id", "employee", "employee_name",
            "basic_salary", "allowances", "total_ctc",
            "bank_name", "bank_account_number", "iban", "tax_status",
        ]
        read_only_fields = ["id", "employee"]


class DisciplinaryRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = DisciplinaryRecord
        fields = [
            "id", "employee", "employee_name",
            "issue_date", "warning_description", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrgChartSerializer(BaseEmployeeSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    subordinate_count = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id", "full_name", "role", "job_title",
            "department_name", "profile_picture",
            "reports_to", "subordinate_count",
        ]

    def get_subordinate_count(self, obj):
        return obj.subordinates.count()
