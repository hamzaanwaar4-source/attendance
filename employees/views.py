from collections import deque

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.permissions import IsAdminOrHOD, IsOwnerOrSuperior, CanViewCompensation
from attendance.models import Attendance, LeaveRequest
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



class StandardPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"


class DepartmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    def post(self, request):
        self.check_permissions(request)
        IsAdminOrHOD().has_permission(request, self)
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, pk):
        return get_object_or_404(Department, pk=pk)

    def get(self, request, pk):
        department = self.get_target(pk)
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)

    def put(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        department = self.get_target(pk)
        serializer = DepartmentSerializer(department, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        department = self.get_target(pk)
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        batches = Batch.objects.all()
        serializer = BatchSerializer(batches, many=True)
        return Response(serializer.data)

    def post(self, request):
        IsAdminOrHOD().has_permission(request, self)
        serializer = BatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BatchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, pk):
        return get_object_or_404(Batch, pk=pk)

    def get(self, request, pk):
        batch = self.get_target(pk)
        serializer = BatchSerializer(batch)
        return Response(serializer.data)

    def put(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        batch = self.get_target(pk)
        serializer = BatchSerializer(batch, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        batch = self.get_target(pk)
        batch.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def apply_filters(self, queryset, params):
        search = params.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(official_email__icontains=search)
                | Q(id__icontains=search)
            )

        status_filter = params.get("status", "")
        if status_filter and status_filter != "All":
            queryset = queryset.filter(employment_status=status_filter)

        role_filter = params.get("role", "")
        if role_filter and role_filter != "All":
            queryset = queryset.filter(role=role_filter)

        department_filter = params.get("department", "")
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)

        return queryset

    def scope_by_role(self, queryset, user):
        if user.is_superuser:
            return queryset

        if not hasattr(user, "employee"):
            return queryset.none()

        employee = user.employee
        if employee.role in ("CEO", "CTO", "COO", "Director", "HOD"):
            return queryset

        if employee.role == "PM":
            visible_ids = set()
            queue = deque([employee])
            while queue:
                current = queue.popleft()
                for emp in Employee.objects.filter(reports_to=current).only("id"):
                    if emp.id not in visible_ids:
                        visible_ids.add(emp.id)
                        queue.append(emp)
            visible_ids.add(employee.id)
            return queryset.filter(id__in=visible_ids)

        return queryset.filter(id=employee.id)

    def get(self, request):
        queryset = Employee.objects.select_related("department", "batch", "reports_to").all()
        queryset = self.apply_filters(queryset, request.query_params)
        queryset = self.scope_by_role(queryset, request.user)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = EmployeeListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        IsAdminOrHOD().has_permission(request, self)
        # Pass request.FILES explicitly to ensure profile_picture is captured
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, pk):
        return get_object_or_404(
            Employee.objects.select_related("department", "batch", "reports_to"),
            pk=pk,
        )

    def get(self, request, pk):
        employee = self.get_target(pk)
        serializer = EmployeeDetailSerializer(employee)
        return Response(serializer.data)

    def put(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        employee = self.get_target(pk)
        serializer = EmployeeUpdateSerializer(employee, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        employee = self.get_target(pk)
        serializer = EmployeeUpdateSerializer(employee, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        IsAdminOrHOD().has_permission(request, self)
        employee = self.get_target(pk)
        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeProfileView(generics.RetrieveUpdateAPIView):
    queryset = Employee.objects.select_related("department", "batch", "reports_to").all()
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperior]
    lookup_field = "pk"

class ProfilePictureUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not hasattr(request.user, "employee"):
            return Response({"detail": "Employee profile required."}, status=status.HTTP_400_BAD_REQUEST)
        
        employee = request.user.employee
        if "profile_picture" not in request.FILES:
            return Response({"detail": "No profile_picture file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        employee.profile_picture = request.FILES["profile_picture"]
        employee.save()
        
        return Response({
            "detail": "Profile picture updated successfully.",
            "profile_picture": request.build_absolute_uri(employee.profile_picture.url) if employee.profile_picture else None
        })


class CompensationView(generics.RetrieveUpdateAPIView):
    queryset = Compensation.objects.select_related("employee").all()
    serializer_class = CompensationSerializer
    permission_classes = [IsAuthenticated, CanViewCompensation]
    lookup_field = "employee_id"
    lookup_url_kwarg = "employee_pk"


class DisciplinaryRecordListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    def get(self, request, employee_pk):
        records = DisciplinaryRecord.objects.filter(
            employee_id=employee_pk
        ).select_related("employee")
        serializer = DisciplinaryRecordSerializer(records, many=True)
        return Response(serializer.data)

    def post(self, request, employee_pk):
        employee = get_object_or_404(Employee, pk=employee_pk)
        serializer = DisciplinaryRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(employee=employee)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DisciplinaryRecordDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHOD]

    def get_target(self, employee_pk, pk):
        return get_object_or_404(
            DisciplinaryRecord.objects.select_related("employee"),
            employee_id=employee_pk,
            pk=pk,
        )

    def get(self, request, employee_pk, pk):
        record = self.get_target(employee_pk, pk)
        serializer = DisciplinaryRecordSerializer(record)
        return Response(serializer.data)

    def put(self, request, employee_pk, pk):
        record = self.get_target(employee_pk, pk)
        serializer = DisciplinaryRecordSerializer(record, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, employee_pk, pk):
        record = self.get_target(employee_pk, pk)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

        present_percentage = (
            round((present_count / total_employees * 100), 1) if total_employees else 0
        )

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
        for role_code, _ in Employee.ROLE_CHOICES:
            count = Employee.active_employees.filter(role=role_code).count()
            if count > 0:
                role_distribution[role_code] = count

        recent_data = EmployeeListSerializer(
            Employee.objects.order_by("-created_at")[:5], many=True
        ).data

        data = {
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
        }
        return Response(data)


class TeamStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "employee"):
            return Response(
                {"detail": "No employee profile linked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        manager = request.user.employee
        subordinate_ids = set()
        queue = deque([manager])
        while queue:
            current = queue.popleft()
            for emp in Employee.objects.filter(reports_to=current).only("id"):
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

        team_members = list(Employee.objects.filter(id__in=subordinate_ids).values(
            "id", "full_name", "role", "job_title", "employment_status"
        ))

        data = {
            "team_size": team_size,
            "present_today": today_present,
            "absent_today": team_size - today_present,
            "team_members": team_members,
        }
        return Response(data)


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

        data = {"period_days": days, "start_date": str(start_date), "end_date": str(today), "daily_summary": list(daily_summary)}
        return Response(data)


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

        data = {"pending": pending_count, "approved": approved_count, "by_type": list(by_type)}
        return Response(data)
