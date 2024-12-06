from django.urls import path
from workspace import views

urlpatterns = [
    path('workspaces', views.Workspaces.as_view()),
    path('workspaces/price_create', views.WorkspacePriceCreate.as_view()),
    path('workspaces/<int:pk>', views.WorkspaceDetail.as_view()),
    path('workspaces/check_require', views.WorkspaceCheck.as_view()),
    path('role/list', views.RoleAPI.as_view()),

    path('workspaces/admin/list', views.WorkspacesAdmin.as_view()),
    path('workspaces/admin/action/<int:pk>', views.WorkspacesAdminAction.as_view()),
]
