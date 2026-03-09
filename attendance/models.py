import uuid
from django.db import models
from django.utils import timezone

from employees.models import Employee


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("remote", "Remote"),
        ("Half leave", "Half Leave"),
        ("Medical leave", "Medical Leave"),
        ("Emergency", "Emergency"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendances"
    )
    date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    break_start_time = models.DateTimeField(null=True, blank=True)
    break_minutes = models.PositiveIntegerField(default=0)
    break_count = models.PositiveIntegerField(default=0)
    accumulated_gross_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Present")

    class Meta:
        db_table = "attendance"
        ordering = ["-date"]
        unique_together = ["employee", "date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

    @property
    def hours_worked(self):
        if not self.check_in_time and self.accumulated_gross_minutes == 0:
            return 0.0
        
        gross_minutes = self.accumulated_gross_minutes
        
        if self.check_in_time:
            end_time = self.check_out_time or timezone.now()
            delta = end_time - self.check_in_time
            gross_minutes += delta.total_seconds() / 60
            
        current_break_mins = 0
        if self.break_start_time and not self.check_out_time:
            current_break_mins = (timezone.now() - self.break_start_time).total_seconds() / 60
            
        net_minutes = max(gross_minutes - self.break_minutes - current_break_mins, 0)
        return round(net_minutes / 60, 1)


class LeaveRequest(models.Model):
    TYPE_CHOICES = [
        ("Sick", "Sick"),
        ("Annual", "Annual"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="leave_requests"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "leave_request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name}: {self.leave_type} ({self.start_date} - {self.end_date})"


class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="leave_balances"
    )
    month_year = models.DateField()
    leaves_availed_this_month = models.PositiveIntegerField(default=0)
    remaining_leaves = models.PositiveIntegerField(default=2)
    wfh_availed_this_month = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "leave_balance"
        unique_together = ["employee", "month_year"]
        ordering = ["-month_year"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.month_year.strftime('%B %Y')}"
