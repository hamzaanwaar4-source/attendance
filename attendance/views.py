from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrHOD, IsOwnerOrSuperior
from attendance.models import Attendance, LeaveRequest, LeaveBalance
from attendance.serializers import (
    AttendanceSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    BreakSerializer,
    AttendanceTodaySerializer,
    AttendanceHistorySerializer,
    LeaveRequestSerializer,
    LeaveRequestApprovalSerializer,
    LeaveBalanceSerializer,
    AdminAttendanceOverviewSerializer,
)
from employees.models import Employee


class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = request.user.employee
        today = timezone.localdate()

        existing = Attendance.objects.filter(employee=employee, date=today).first()
        if existing and existing.check_in_time:
            if existing.break_start_time:
                delta = timezone.now() - existing.break_start_time
                existing.break_minutes += int(delta.total_seconds() / 60)
                existing.break_start_time = None
                existing.save()
                return Response(
                    AttendanceTodaySerializer(existing).data,
                    status=status.HTTP_200_OK,
                )
            
            return Response(
                {"detail": "Already checked in today and not on a break."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if existing:
            existing.check_in_time = timezone.now()
            existing.status = serializer.validated_data.get("status", "Present")
            existing.save()
            attendance = existing
        else:
            attendance = Attendance.objects.create(
                employee=employee,
                date=today,
                check_in_time=timezone.now(),
                status=serializer.validated_data.get("status", "Present"),
            )

        return Response(
            AttendanceTodaySerializer(attendance).data,
            status=status.HTTP_201_CREATED,
        )


class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = request.user.employee
        today = timezone.localdate()

        attendance = Attendance.objects.filter(employee=employee, date=today).first()
        if not attendance or not attendance.check_in_time:
            return Response(
                {"detail": "You have not checked in today."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attendance.check_out_time:
            return Response(
                {"detail": "Already checked out today."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attendance.break_start_time:
            delta = timezone.now() - attendance.break_start_time
            attendance.break_minutes += int(delta.total_seconds() / 60)
            attendance.break_start_time = None

        attendance.check_out_time = timezone.now()
        attendance.save()

        return Response(AttendanceTodaySerializer(attendance).data)


class TodayAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = request.user.employee
        today = timezone.localdate()
        attendance = Attendance.objects.filter(employee=employee, date=today).first()

        if not attendance:
            data = {"checked_in": False, "on_break": False, "date": str(today), "check_in_time": None, "check_out_time": None, "break_start_time": None, "break_minutes": 0, "break_count": 0, "hours_worked": 0.0, "status": "Not checked in"}
            return Response(data)
        
        data = AttendanceTodaySerializer(attendance).data
        data["checked_in"] = attendance.check_in_time is not None
        data["on_break"] = attendance.break_start_time is not None
        return Response(data)


class BreakView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = request.user.employee
        today = timezone.localdate()
        attendance = Attendance.objects.filter(employee=employee, date=today).first()

        if not attendance or not attendance.check_in_time:
            return Response(
                {"detail": "You must check in before taking a break."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attendance.check_out_time:
            return Response(
                {"detail": "Cannot take a break after checking out."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attendance.break_start_time:
            return Response(
                {"detail": "You are already on a break."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BreakSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attendance.break_start_time = timezone.now()
        attendance.break_count += 1
        attendance.save()

        return Response(AttendanceTodaySerializer(attendance).data)


class MonthlyAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = request.user.employee
        period = request.query_params.get("period", "7")
        try:
            days = int(period)
        except ValueError:
            days = 7

        today = timezone.localdate()
        start_date = today - timezone.timedelta(days=days)

        records = Attendance.objects.filter(
            employee=employee, date__gte=start_date, date__lte=today
        ).order_by("-date")

        history_data = AttendanceHistorySerializer(records, many=True).data

        aggregates = records.aggregate(
            total_break_minutes=Sum("break_minutes"),
            total_records=Count("id"),
        )

        total_hours = sum(r.hours_worked for r in records)
        working_days_in_period = self._count_working_days(start_date, today)
        required_hours = working_days_in_period * 8
        remaining_hours = max(required_hours - total_hours, 0)

        data = {
            "period_days": days,
            "start_date": str(start_date),
            "end_date": str(today),
            "working_days": f"{aggregates['total_records'] or 0} / {working_days_in_period}",
            "required_hours": f"{required_hours}h",
            "worked_hours": f"{round(total_hours, 1)}h",
            "remaining_hours": f"{round(remaining_hours, 1)}h",
            "total_breaks": aggregates["total_break_minutes"] or 0,
            "records": history_data,
        }
        return Response(data)

    def _count_working_days(self, start, end):
        count = 0
        current = start
        while current <= end:
            if current.weekday() < 5:
                count += 1
            current += timezone.timedelta(days=1)
        return count


class EmployeeAttendanceHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_pk):
        try:
            target_employee = Employee.objects.get(pk=employee_pk)
        except Employee.DoesNotExist:
            return Response(
                {"detail": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        requesting_employee = getattr(request.user, "employee", None)
        if not request.user.is_superuser:
            if requesting_employee is None:
                return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
            if requesting_employee.id != target_employee.id:
                if requesting_employee.role not in ("CEO", "CTO", "COO", "Director", "HOD", "PM"):
                    return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        period = request.query_params.get("period", "30")
        try:
            days = int(period)
        except ValueError:
            days = 30

        today = timezone.localdate()
        start_date = today - timezone.timedelta(days=days)

        records = Attendance.objects.filter(
            employee=target_employee, date__gte=start_date, date__lte=today
        ).order_by("-date")

        history_data = AdminAttendanceOverviewSerializer(records, many=True).data

        total_hours = sum(r.hours_worked for r in records)
        total_breaks = records.aggregate(total=Sum("break_minutes"))["total"] or 0
        avg_hours = round(total_hours / records.count(), 1) if records.count() else 0.0

        data = {
            "employee_id": str(target_employee.id),
            "employee_name": target_employee.full_name,
            "period_days": days,
            "days_this_month": records.count(),
            "hours_worked": f"{round(total_hours, 1)}h",
            "total_breaks": total_breaks,
            "avg_hours_per_day": f"{avg_hours}h",
            "records": history_data,
        }
        return Response(data)


class LeaveRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return LeaveRequest.objects.select_related("employee").all()
        if hasattr(user, "employee"):
            employee = user.employee
            if employee.role in ("CEO", "CTO", "COO", "Director", "HOD", "PM"):
                return LeaveRequest.objects.select_related("employee").all()
            return LeaveRequest.objects.filter(employee=employee).select_related("employee")
        return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)


class LeaveRequestDetailView(generics.RetrieveAPIView):
    queryset = LeaveRequest.objects.select_related("employee").all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]


class LeaveRequestApprovalView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    @transaction.atomic
    def post(self, request, pk):
        try:
            leave_request = LeaveRequest.objects.select_for_update().get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response(
                {"detail": "Leave request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if leave_request.status != "Pending":
            return Response(
                {"detail": "This leave request has already been processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LeaveRequestApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        leave_request.status = serializer.validated_data["action"]
        leave_request.save()

        if leave_request.status == "Approved":
            month_start = leave_request.start_date.replace(day=1)
            balance, _ = LeaveBalance.objects.get_or_create(
                employee=leave_request.employee,
                month_year=month_start,
                defaults={"remaining_leaves": 2},
            )
            leave_days = (leave_request.end_date - leave_request.start_date).days + 1
            balance.leaves_availed_this_month += leave_days
            balance.remaining_leaves = max(balance.remaining_leaves - leave_days, 0)
            balance.save()

        return Response(LeaveRequestSerializer(leave_request).data)


class LeaveBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = request.user.employee
        employee_id = request.query_params.get("employee_id", None)

        if employee_id and employee_id != str(employee.id):
            if employee.role not in ("CEO", "CTO", "COO", "Director", "HOD"):
                return Response(
                    {"detail": "Forbidden."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            try:
                employee = Employee.objects.get(pk=employee_id)
            except Employee.DoesNotExist:
                return Response(
                    {"detail": "Employee not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        balances = LeaveBalance.objects.filter(employee=employee)
        return Response(LeaveBalanceSerializer(balances, many=True).data)
