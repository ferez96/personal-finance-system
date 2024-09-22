from django.urls import path
from . import views

app_name = 'editor'

urlpatterns = [
    path('', views.list_documents, name='list_documents'),
    path('upload/', views.upload_document, name='upload_document'),
    path('edit/<int:doc_id>/', views.edit_document, name='edit_document'),
    path('update_heading/', views.update_heading, name='update_heading'),
    path('apply_format/<int:doc_id>/', views.apply_format, name='apply_format'),
    path('download/<int:doc_id>/', views.download_document, name='download_document'),
]