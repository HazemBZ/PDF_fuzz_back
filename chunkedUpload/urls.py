from django.urls import path
from . import views


urlpatterns = [
    path('start', views.ChunkedUploadView.as_view()),
    path('complete', views.ChunkedUploadCompleteView.as_view())
]
