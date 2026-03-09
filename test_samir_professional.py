import os
import django
import datetime
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendox.settings")
django.setup()

from django.test import Client
from attendance.models import Attendance
from django.utils import timezone
from employees.models import Employee
from django.contrib.auth import get_user_model

client = Client()

# Setup Samir
User = get_user_model()
User.objects.filter(email='samir@attendox.com').delete()
user = User.objects.create_user(email='samir@attendox.com', password='ProfessionalPassword123!')
samir = Employee.objects.create(
    user=user, 
    official_email='samir@attendox.com', 
    full_name='Samir Professional', 
    role='Employee',
    join_date=timezone.localdate() - timedelta(days=30)
)

print(f"\n--- SAMIR'S PROFESSIONAL WEEK SIMULATION ---")

# Login as Samir
response = client.post('/api/v1/auth/token/', {'email': 'samir@attendox.com', 'password': 'ProfessionalPassword123!'}, content_type='application/json')
token = response.json()['access']
auth_header = {'HTTP_AUTHORIZATION': f'Bearer {token}', 'CONTENT_TYPE': 'application/json'}

# Simulation Dates (Last Week)
today = timezone.localdate()
last_monday = today - timedelta(days=today.weekday() + 7)
last_tuesday = last_monday + timedelta(days=1)
last_wednesday = last_monday + timedelta(days=2)
last_thursday = last_monday + timedelta(days=3)
last_friday = last_monday + timedelta(days=4)

# 1. MONDAY: Productive 8.5 Hours
print("Logging Monday: Productive 8.5 Hours...")
Attendance.objects.create(
    employee=samir, 
    date=last_monday, 
    check_in_time=timezone.make_aware(datetime.datetime.combine(last_monday, datetime.time(9, 0))),
    check_out_time=timezone.make_aware(datetime.datetime.combine(last_monday, datetime.time(17, 30))),
    status="Present"
)

# 2. TUESDAY: Absent (We leave it empty)
print("Tuesday: Left blank (Should show as Absent in history)...")

# 3. WEDNESDAY: Accidental Checkout & Resume
print("Wednesday: Accidental Checkout & Resume...")
att_wed = Attendance.objects.create(
    employee=samir,
    date=last_wednesday,
    check_in_time=timezone.make_aware(datetime.datetime.combine(last_wednesday, datetime.time(9, 0))),
    check_out_time=timezone.make_aware(datetime.datetime.combine(last_wednesday, datetime.time(13, 0))),
    status="Present"
)
# Resumed at 1:15pm
att_wed.accumulated_gross_minutes = 240 # 4 hours worked
att_wed.check_in_time = timezone.make_aware(datetime.datetime.combine(last_wednesday, datetime.time(13, 15)))
att_wed.check_out_time = timezone.make_aware(datetime.datetime.combine(last_wednesday, datetime.time(17, 15)))
att_wed.break_minutes = 15
att_wed.break_count = 1
att_wed.save()

# 4. THURSDAY: Late Arrival (Tested via logic or manual creation)
print("Thursday: Late Arrival (9:45 AM)...")
Attendance.objects.create(
    employee=samir,
    date=last_thursday,
    check_in_time=timezone.make_aware(datetime.datetime.combine(last_thursday, datetime.time(9, 45))),
    check_out_time=timezone.make_aware(datetime.datetime.combine(last_thursday, datetime.time(18, 0))),
    status="Late"
)

# 5. FRIDAY: Early Exit / Half Day
print("Friday: Early Exit (Half Day)...")
Attendance.objects.create(
    employee=samir,
    date=last_friday,
    check_in_time=timezone.make_aware(datetime.datetime.combine(last_friday, datetime.time(9, 0))),
    check_out_time=timezone.make_aware(datetime.datetime.combine(last_friday, datetime.time(12, 30))), # 3.5 hours
    status="Half leave"
)

# Fetch History
print("\nFETCHING SAMIR'S HISTORY...")
# Ensure server is running or use client directly. Client uses internal routing.
response = client.get(f'/api/v1/attendance/monthly/?period=14', **auth_header)
res_data = response.json()

if 'records' in res_data:
    print(f"\nSAMIR'S STATS:")
    print(f"Worked: {res_data.get('worked_hours')} | Required: {res_data.get('required_hours')} | Remaining: {res_data.get('remaining_hours')}")

    print(f"\nDAILY RECORDS:")
    for rec in res_data['records']:
        # Sort display by date ascending for readability in terminal
        pass
    
    # Sort for print
    res_data['records'].sort(key=lambda x: x['date'])
    
    for rec in res_data['records']:
        if rec['date'] >= str(last_monday) and rec['date'] <= str(today):
            print(f"Date: {rec['date']} ({rec['day_of_week']}) | Status: {rec['status']:<10} | Hours: {rec['hours_worked']:>4} | Req: {rec['required_hours']}")
else:
    print("Error fetching records:", res_data)

print("\n--- SIMULATION COMPLETE ---")
