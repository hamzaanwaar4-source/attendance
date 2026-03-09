from rest_framework import serializers

from attendance.models import Attendance, LeaveRequest, LeaveBalance


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    hours_worked = serializers.ReadOnlyField()

    class Meta:
        model = Attendance
        fields = [
            "id", "employee", "employee_name", "date",
            "check_in_time", "check_out_time",
            "break_start_time", "break_minutes", "break_count",
            "status", "hours_worked",
        ]
        read_only_fields = ["id"]


class CheckInSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Attendance.STATUS_CHOICES, default="Present"
    )


class CheckOutSerializer(serializers.Serializer):
    pass


class BreakSerializer(serializers.Serializer):
    pass


class AttendanceTodaySerializer(serializers.ModelSerializer):
    hours_worked = serializers.ReadOnlyField()
    required_hours = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            "id", "date", "check_in_time", "check_out_time",
            "break_start_time", "break_minutes", "break_count", "status", "hours_worked", "required_hours"
        ]

    def get_required_hours(self, obj):
        return 8.0


class AttendanceHistorySerializer(serializers.ModelSerializer):
    hours_worked = serializers.ReadOnlyField()
    day_of_week = serializers.SerializerMethodField()
    required_hours = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            "id", "date", "day_of_week",
            "check_in_time", "check_out_time",
            "break_start_time", "break_minutes", "break_count",
            "status", "hours_worked", "required_hours"
        ]

    def get_day_of_week(self, obj):
        return obj.date.strftime("%A")

    def get_required_hours(self, obj):
        return 8.0


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "employee", "employee_name",
            "start_date", "end_date", "leave_type", "status",
            "created_at",
        ]
        read_only_fields = ["id", "employee", "status", "created_at"]

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError("Start date must be before end date.")
        return data


class LeaveRequestApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["Approved", "Rejected"])


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = LeaveBalance
        fields = [
            "id", "employee", "employee_name",
            "month_year", "leaves_availed_this_month",
            "remaining_leaves", "wfh_availed_this_month",
        ]
        read_only_fields = ["id", "employee"]


class AdminAttendanceOverviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_id_display = serializers.CharField(source="employee.employee_id_display", read_only=True)
    hours_worked = serializers.ReadOnlyField()
    day_of_week = serializers.SerializerMethodField()
    required_hours = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            "id", "employee", "employee_name", "employee_id_display",
            "date", "day_of_week",
            "check_in_time", "check_out_time",
            "break_start_time", "break_minutes", "break_count",
            "status", "hours_worked", "required_hours"
        ]

    def get_day_of_week(self, obj):
        return obj.date.strftime("%A")

    def get_required_hours(self, obj):
        return 8.0
