from django.db.models import Q
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from attendance.models import Attendance
from django.utils import timezone
from attendance.models import LeaveRequest
from django.db.models import Count
from accounts.permissions import IsAdminOrHOD, IsOwnerOrSuperior, CanViewCompensation
from employees.models import Employee, Compensation, DisciplinaryRecord, Department, Batch
from employees.serializers import (
    EmployeeListSerializer,
    EmployeeCreateSerializer,
    EmployeeDetailSerializer,
    EmployeeProfileSerializer,
    EmployeeUpdateSerializer,
    CompensationSerializer,
    DisciplinaryRecordSerializer,
    DepartmentSerializer,
    BatchSerializer,
    OrgChartSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminOrHOD()]
        return [IsAuthenticated()]


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminOrHOD()]
        return [IsAuthenticated()]


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("department", "batch", "reports_to").all()

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action == "list":
            return EmployeeListSerializer
        if self.action in ["update", "partial_update"]:
            return EmployeeUpdateSerializer
        return EmployeeDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsAdminOrHOD()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminOrHOD()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        search = self.request.query_params.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(official_email__icontains=search) |
                Q(id__icontains=search)
            )

        status_filter = self.request.query_params.get("status", "")
        if status_filter and status_filter != "All":
            queryset = queryset.filter(employment_status=status_filter)

        role_filter = self.request.query_params.get("role", "")
        if role_filter and role_filter != "All":
            queryset = queryset.filter(role=role_filter)

        department_filter = self.request.query_params.get("department", "")
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)

        if not user.is_superuser and hasattr(user, "employee"):
            employee = user.employee
            if employee.role in ("CEO", "CTO", "COO", "Director", "HOD"):
                return queryset
            if employee.role == "PM":
                subordinate_ids = self._get_all_subordinate_ids(employee)
                subordinate_ids.add(employee.id)
                return queryset.filter(id__in=subordinate_ids)
            return queryset.filter(id=employee.id)

        return queryset

    def _get_all_subordinate_ids(self, manager):
        result = set()
        queue = [manager]
        while queue:
            current = queue.pop(0)
            direct = Employee.objects.filter(reports_to=current)
            for emp in direct:
                if emp.id not in result:
                    result.add(emp.id)
                    queue.append(emp)
        return result

    def perform_create(self, serializer):
        password = serializer.validated_data.pop("password", None)
        employee = serializer.save()
        if password:
            employee.user.set_password(password)
            employee.user.save()


class EmployeeProfileView(generics.RetrieveUpdateAPIView):
    queryset = Employee.objects.select_related("department", "batch", "reports_to").all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperior]
    lookup_field = "pk"


class CompensationView(generics.RetrieveUpdateAPIView):
    queryset = Compensation.objects.select_related("employee").all()
    serializer_class = CompensationSerializer
    permission_classes = [IsAuthenticated, CanViewCompensation]
    lookup_field = "employee_id"
    lookup_url_kwarg = "employee_pk"


class DisciplinaryRecordViewSet(viewsets.ModelViewSet):
    serializer_class = DisciplinaryRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    def get_queryset(self):
        employee_pk = self.kwargs.get("employee_pk")
        return DisciplinaryRecord.objects.filter(employee_id=employee_pk).select_related("employee")

    def perform_create(self, serializer):
        employee_pk = self.kwargs.get("employee_pk")
        employee = Employee.objects.get(pk=employee_pk)
        serializer.save(employee=employee)


class OrgChartView(generics.ListAPIView):
    queryset = Employee.objects.select_related("department").filter(
        employment_status__in=["Active", "Probation", "Confirmed"]
    )
    serializer_class = OrgChartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    def get(self, request):

        today = timezone.localdate()
        total_employees = Employee.active_employees.count()
        today_attendance = Attendance.objects.filter(date=today)
        present_count = today_attendance.filter(
            status__in=["Present", "remote"]
        ).count()
        absent_count = total_employees - present_count
        leave_count = today_attendance.filter(
            status__in=["Half leave", "Medical leave"]
        ).count()
        wfh_count = today_attendance.filter(status="remote").count()

        present_percentage = round((present_count / total_employees * 100), 1) if total_employees else 0

        status_counts = {
            "Active": Employee.objects.filter(employment_status="Active").count(),
            "Terminated": Employee.objects.filter(employment_status="Terminated").count(),
            "On Leave": Employee.objects.filter(employment_status="Resigned").count(),
        }

        department_distribution = {}
        for dept in Department.objects.all():
            department_distribution[dept.name] = dept.employees.filter(
                employment_status__in=["Active", "Probation", "Confirmed"]
            ).count()

        role_distribution = {}
        for role_choice in Employee.ROLE_CHOICES:
            count = Employee.active_employees.filter(role=role_choice[0]).count()
            if count > 0:
                role_distribution[role_choice[0]] = count

        recent_employees = Employee.objects.order_by("-created_at")[:5]
        recent_data = EmployeeListSerializer(recent_employees, many=True).data

        return Response({
            "total_employees": total_employees,
            "present": present_count,
            "present_percentage": present_percentage,
            "absent": absent_count,
            "leave": leave_count,
            "work_from_home": wfh_count,
            "status_summary": status_counts,
            "department_distribution": department_distribution,
            "role_distribution": role_distribution,
            "recent_employees": recent_data,
        })


class TeamStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not hasattr(request.user, "employee"):
            return Response({"detail": "No employee profile linked."}, status=400)

        manager = request.user.employee
        subordinate_ids = set()
        queue = [manager]
        while queue:
            current = queue.pop(0)
            direct = Employee.objects.filter(reports_to=current)
            for emp in direct:
                if emp.id not in subordinate_ids:
                    subordinate_ids.add(emp.id)
                    queue.append(emp)

        today = timezone.localdate()
        team_size = len(subordinate_ids)
        today_present = Attendance.objects.filter(
            employee_id__in=subordinate_ids,
            date=today,
            status__in=["Present", "remote"],
        ).count()

        team_members = Employee.objects.filter(id__in=subordinate_ids).values(
            "id", "full_name", "role", "job_title", "employment_status"
        )

        return Response({
            "team_size": team_size,
            "present_today": today_present,
            "absent_today": team_size - today_present,
            "team_members": list(team_members),
        })


class AttendanceSummaryStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    def get(self, request):

        today = timezone.localdate()
        period = request.query_params.get("period", "7")
        try:
            days = int(period)
        except ValueError:
            days = 7

        start_date = today - timezone.timedelta(days=days)
        records = Attendance.objects.filter(date__gte=start_date, date__lte=today)

        daily_summary = (
            records.values("date")
            .annotate(
                total=Count("id"),
                present=Count("id", filter=Q(status__in=["Present", "remote"])),
            )
            .order_by("date")
        )

        return Response({
            "period_days": days,
            "start_date": str(start_date),
            "end_date": str(today),
            "daily_summary": list(daily_summary),
        })


class LeaveSummaryStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    def get(self, request):

        pending_count = LeaveRequest.objects.filter(status="Pending").count()
        approved_count = LeaveRequest.objects.filter(status="Approved").count()

        by_type = (
            LeaveRequest.objects.values("leave_type")
            .annotate(count=Count("id"))
            .order_by("leave_type")
        )

        return Response({
            "pending": pending_count,
            "approved": approved_count,
            "by_type": list(by_type),
        })
