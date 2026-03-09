from django.urls import path

from employees.views import (
    EmployeeListView,
    EmployeeDetailView,
    EmployeeProfileView,
    ProfilePictureUpdateView,
    CompensationView,
    DisciplinaryRecordListView,
    DisciplinaryRecordDetailView,
    DepartmentListView,
    DepartmentDetailView,
    BatchListView,
    BatchDetailView,
    OrgChartView,
    AdminDashboardStatsView,
    TeamStatsView,
    AttendanceSummaryStatsView,
    LeaveSummaryStatsView,
)

urlpatterns = [
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("departments/<uuid:pk>/", DepartmentDetailView.as_view(), name="department-detail"),

    path("batches/", BatchListView.as_view(), name="batch-list"),
    path("batches/<uuid:pk>/", BatchDetailView.as_view(), name="batch-detail"),

    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    path("employees/<uuid:pk>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("employees/<uuid:pk>/profile/", EmployeeProfileView.as_view(), name="employee-profile"),
    path("employees/profile-picture/", ProfilePictureUpdateView.as_view(), name="profile-picture-update"),
    path("employees/<uuid:employee_pk>/compensation/", CompensationView.as_view(), name="employee-compensation"),
    path("employees/<uuid:employee_pk>/disciplinary/", DisciplinaryRecordListView.as_view(), name="employee-disciplinary-list"),
    path("employees/<uuid:employee_pk>/disciplinary/<uuid:pk>/", DisciplinaryRecordDetailView.as_view(), name="employee-disciplinary-detail"),

    path("org-chart/", OrgChartView.as_view(), name="org-chart"),
    path("stats/dashboard/", AdminDashboardStatsView.as_view(), name="stats-dashboard"),
    path("stats/team/", TeamStatsView.as_view(), name="stats-team"),
    path("stats/attendance-summary/", AttendanceSummaryStatsView.as_view(), name="stats-attendance-summary"),
    path("stats/leave-summary/", LeaveSummaryStatsView.as_view(), name="stats-leave-summary"),
]
