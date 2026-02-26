from django.urls import path

from attendance.views import (
    CheckInView,
    CheckOutView,
    TodayAttendanceView,
    MonthlyAttendanceView,
    BreakView,
    EmployeeAttendanceHistoryView,
    LeaveRequestListCreateView,
    LeaveRequestDetailView,
    LeaveRequestApprovalView,
    LeaveBalanceView,
)

urlpatterns = [
    path("attendance/checkin/", CheckInView.as_view(), name="attendance-checkin"),
    path("attendance/checkout/", CheckOutView.as_view(), name="attendance-checkout"),
    path("attendance/today/", TodayAttendanceView.as_view(), name="attendance-today"),
    path("attendance/monthly/", MonthlyAttendanceView.as_view(), name="attendance-monthly"),
    path("attendance/break/", BreakView.as_view(), name="attendance-break"),
    path("attendance/employee/<uuid:employee_pk>/", EmployeeAttendanceHistoryView.as_view(), name="attendance-employee-history",),
    path("leave-requests/", LeaveRequestListCreateView.as_view(), name="leave-request-list"),
    path("leave-requests/<uuid:pk>/", LeaveRequestDetailView.as_view(), name="leave-request-detail"),
    path("leave-requests/<uuid:pk>/approve/",LeaveRequestApprovalView.as_view(),name="leave-request-approve",),
    path("leave-balance/", LeaveBalanceView.as_view(), name="leave-balance"),
]
