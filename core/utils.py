from django.utils import timezone


def get_current_month_start():
    today = timezone.localdate()
    return today.replace(day=1)


def calculate_working_days(start_date, end_date):
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current += timezone.timedelta(days=1)
    return count


def format_hours(total_minutes):
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours}h {minutes}m"
