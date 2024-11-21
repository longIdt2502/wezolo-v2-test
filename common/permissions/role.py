from typing import Any
from rest_framework import permissions

from common.permissions.base_response import UserDoesNotPermission
from workspace.models import Workspace
from employee.models import Employee


class RolePermissions(permissions.BasePermission):
    def __init__(self, role_get=None, role_post=None, role_put=None, role_patch=None, role_delete=None):
        self.role_get = role_get
        self.role_post = role_post
        self.role_put = role_put
        self.role_patch = role_patch
        self.role_delete = role_delete

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self

    def has_permission(self, request, view):
        # company_id = request.META.get("HTTP_WORKSPACE_ID")
        # if not company_id:
        #     raise UserDoesNotPermission()
        # role = WorkspaceUser.objects.filter(workspace_id=company_id, user=request.user).first()
        # workspace = Workspace.objects.get(id=company_id)
        # role_in_parent = WorkspaceUser.objects.filter(workspace=workspace.parent, user=request.user).first()
        # if not role and not role_in_parent:
        #     raise UserDoesNotPermission()
        # if role and role.status != "ACTIVE":
        #     raise UserDoesNotPermission()
        # if role_in_parent and role_in_parent.status != "ACTIVE":
        #     raise UserDoesNotPermission()
        return True
    