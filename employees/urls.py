from django.urls import path, include
from rest_framework.routers import DefaultRouter

from employees.views import (
    EmployeeViewSet,
    EmployeeProfileView,
    CompensationView,
    DisciplinaryRecordViewSet,
    DepartmentViewSet,
    BatchViewSet,
    OrgChartView,
    AdminDashboardStatsView,
    TeamStatsView,
    AttendanceSummaryStatsView,
    LeaveSummaryStatsView,
)

router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"batches", BatchViewSet, basename="batch")

urlpatterns = [
    path("", include(router.urls)),
    path("employees/<uuid:pk>/profile/", EmployeeProfileView.as_view(), name="employee-profile",),
    path("employees/<uuid:employee_pk>/compensation/", CompensationView.as_view(), name="employee-compensation",),
    path("employees/<uuid:employee_pk>/disciplinary/", DisciplinaryRecordViewSet.as_view({"get": "list", "post": "create"}), name="employee-disciplinary-list",),
    path("employees/<uuid:employee_pk>/disciplinary/<uuid:pk>/", DisciplinaryRecordViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),name="employee-disciplinary-detail",),
    path("org-chart/", OrgChartView.as_view(), name="org-chart"),
    path("stats/dashboard/", AdminDashboardStatsView.as_view(), name="stats-dashboard"),
    path("stats/team/", TeamStatsView.as_view(), name="stats-team"),
    path("stats/attendance-summary/", AttendanceSummaryStatsView.as_view(), name="stats-attendance-summary"),
    path("stats/leave-summary/", LeaveSummaryStatsView.as_view(), name="stats-leave-summary"),
]
