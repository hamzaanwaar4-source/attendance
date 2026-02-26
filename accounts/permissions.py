from rest_framework import permissions


class IsAdminOrHOD(permissions.BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, "employee"):
            return request.user.is_superuser
        employee = request.user.employee
        return employee.role in ("CEO", "CTO", "COO", "Director", "HOD") or request.user.is_superuser


class IsOwnerOrSuperior(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, "employee"):
            return False

        requesting_employee = request.user.employee
        target_employee = obj if hasattr(obj, "official_email") else getattr(obj, "employee", None)

        if target_employee is None:
            return False

        if requesting_employee.id == target_employee.id:
            return True

        return self._is_superior(requesting_employee, target_employee)

    def _is_superior(self, superior, subordinate):
        current = subordinate.reports_to
        visited = set()
        while current is not None:
            if current.id in visited:
                break
            if current.id == superior.id:
                return True
            visited.add(current.id)
            current = current.reports_to
        return False


class CanViewCompensation(permissions.BasePermission):
    PRIVILEGED_ROLES = ("CEO", "CTO", "COO", "Director", "HOD")

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, "employee"):
            return False

        requesting_employee = request.user.employee
        target_employee = getattr(obj, "employee", obj)

        if requesting_employee.id == target_employee.id:
            return True

        if requesting_employee.role in self.PRIVILEGED_ROLES:
            return True

        return False


class IsReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
