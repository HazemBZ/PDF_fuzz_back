from django.urls import path

from fuzz.views import (
    get_all_file_names,
    get_all_images_by_file_name,
    get_image_from_path,
    get_images_by_keyword,
)

urlpatterns = [
    path("file/names", get_all_file_names),
    path("image/all/<fileName>", get_all_images_by_file_name),
    path("image/by/keyword", get_images_by_keyword),
    path("image/path/<path:image_path>", get_image_from_path),
]
