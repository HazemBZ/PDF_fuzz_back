from django.urls import path
from . import views


urlpatterns = [
    path("start", views.ChunkedUploadView.as_view()),
    path("complete", views.ChunkedUploadCompleteView.as_view()),
    path("check_uploads", views.ChunkedUploadCheck.as_view()),
]
