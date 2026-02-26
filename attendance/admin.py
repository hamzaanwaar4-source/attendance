from django.contrib import admin

from attendance.models import Attendance, LeaveRequest, LeaveBalance


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "check_in_time", "check_out_time", "status"]
    list_filter = ["status", "date"]
    search_fields = ["employee__full_name"]


class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "status"]
    list_filter = ["status", "leave_type"]
    search_fields = ["employee__full_name"]


class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "month_year", "leaves_availed_this_month", "remaining_leaves"]
    list_filter = ["month_year"]
    search_fields = ["employee__full_name"]


admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(LeaveRequest, LeaveRequestAdmin)
admin.site.register(LeaveBalance, LeaveBalanceAdmin)
