import uuid
from django.db import models
from django.conf import settings

from employees.managers import ActiveEmployeeManager


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "department"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Batch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "batch"
        ordering = ["name"]
        verbose_name_plural = "batches"

    def __str__(self):
        return self.name


class Employee(models.Model):
    ROLE_CHOICES = [
        ("CEO", "CEO"),
        ("CTO", "CTO"),
        ("COO", "COO"),
        ("Director", "Director"),
        ("HOD", "HOD"),
        ("PM", "PM"),
        ("Employee", "Employee"),
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ("Active", "Active"),
        ("Probation", "Probation"),
        ("Confirmed", "Confirmed"),
        ("Resigned", "Resigned"),
        ("Terminated", "Terminated"),
    ]

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
    ]

    MARITAL_STATUS_CHOICES = [
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced"),
        ("Widowed", "Widowed"),
    ]

    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee",
        null=True, blank=True,
    )
    official_email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Employee")
    reports_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subordinates"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees"
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees"
    )

    full_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    cnic = models.CharField(max_length=15, unique=True, blank=True, null=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    personal_phone = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True)
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)

    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    job_title = models.CharField(max_length=100, blank=True)
    employment_status = models.CharField(
        max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default="Active"
    )
    join_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)

    highest_qualification = models.CharField(max_length=100, blank=True)
    field_of_study = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)

    prev_company = models.CharField(max_length=200, blank=True)
    prev_designation = models.CharField(max_length=100, blank=True)
    years_experience = models.DecimalField(max_digits=4, decimal_places=1, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active_employees = ActiveEmployeeManager()

    class Meta:
        db_table = "employee"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.official_email})"

    @property
    def employee_id_display(self):
        short_id = str(self.id).split("-")[0].upper()
        return f"EMP-{short_id}"


class Compensation(models.Model):
    TAX_STATUS_CHOICES = [
        ("Filer", "Filer"),
        ("Non-Filer", "Non-Filer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="compensation"
    )
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    tax_status = models.CharField(max_length=20, choices=TAX_STATUS_CHOICES, default="Filer")

    class Meta:
        db_table = "compensation"

    def __str__(self):
        return f"Compensation: {self.employee.full_name}"


class DisciplinaryRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="disciplinary_records"
    )
    issue_date = models.DateField()
    warning_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "disciplinary_record"
        ordering = ["-issue_date"]

    def __str__(self):
        return f"Warning: {self.employee.full_name} on {self.issue_date}"
