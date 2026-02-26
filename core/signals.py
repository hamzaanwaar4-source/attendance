from django.db.models.signals import post_save
from django.dispatch import receiver

from employees.models import Employee, Compensation
from accounts.models import CustomUser


@receiver(post_save, sender=Employee)
def create_user_and_compensation_for_employee(sender, instance, created, **kwargs):
    if created:
        if not instance.user_id:
            username = instance.official_email.split("@")[0]
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = CustomUser.objects.create_user(
                username=username,
                email=instance.official_email,
                password=instance.official_email,
            )
            instance.user = user
            instance.save(update_fields=["user"])

        if not hasattr(instance, "compensation") or instance.compensation is None:
            try:
                Compensation.objects.get(employee=instance)
            except Compensation.DoesNotExist:
                Compensation.objects.create(employee=instance)
