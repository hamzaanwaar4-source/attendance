from django.contrib import admin

from employees.models import Employee, Compensation, DisciplinaryRecord, Department, Batch


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "official_email", "role", "department", "employment_status"]
    list_filter = ["role", "employment_status", "department"]
    search_fields = ["full_name", "official_email", "cnic"]
    readonly_fields = ["id", "created_at", "updated_at"]


class CompensationAdmin(admin.ModelAdmin):
    list_display = ["employee", "basic_salary", "total_ctc", "tax_status"]
    search_fields = ["employee__full_name"]


class DisciplinaryRecordAdmin(admin.ModelAdmin):
    list_display = ["employee", "issue_date", "created_at"]
    list_filter = ["issue_date"]
    search_fields = ["employee__full_name"]


admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Compensation, CompensationAdmin)
admin.site.register(DisciplinaryRecord, DisciplinaryRecordAdmin)
admin.site.register(Department)
admin.site.register(Batch)
