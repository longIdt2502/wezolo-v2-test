from django.urls import path
from .views import *

urlpatterns = [
    path('create', CustomerCreate.as_view()),
    path('list', CustomerList.as_view()),
    path('detail/<int:pk>', CustomerDetail.as_view()),


    path('export_file_example', ExportFileImportCustomer.as_view()),
    path('upload_file_import', UploadFileImport.as_view())
]
