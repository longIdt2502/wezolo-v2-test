from rest_framework import status
from rest_framework.exceptions import APIException


class UserDoesNotPermission(APIException):
    """Custom exception for unauthenticated access."""
    status_code = status.HTTP_200_OK
    default_detail = {
        'code': 403,
        'message': 'You do not have permission to access this action',
        'details': None,
    }
    default_code = 'not_authenticated'


class WorkspaceLockedException(APIException):
    """Custom exception for locked workspace."""
    status_code = status.HTTP_200_OK
    default_detail = {
        'code': 403,
        'message': 'Workspace is locked',
        'details': None,
    }
    default_code = 'workspace_locked'
