from django.db import models


class ActiveEmployeeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            employment_status__in=["Active", "Probation", "Confirmed"]
        )


class DepartmentEmployeeManager(models.Manager):
    def for_department(self, department):
        return self.get_queryset().filter(department=department)


class SubordinateManager(models.Manager):
    def direct_reports(self, manager_employee):
        return self.get_queryset().filter(reports_to=manager_employee)

    def all_subordinates(self, manager_employee):
        result = []
        self._collect_subordinates(manager_employee, result, set())
        return self.get_queryset().filter(id__in=[e.id for e in result])

    def _collect_subordinates(self, manager, result, visited):
        if manager.id in visited:
            return
        visited.add(manager.id)
        direct = self.get_queryset().filter(reports_to=manager)
        for emp in direct:
            result.append(emp)
            self._collect_subordinates(emp, result, visited)
