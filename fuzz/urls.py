from django.urls import path

import fuzz.views as fuzz_views

urlpatterns = [
    path("file/delete", fuzz_views.delete_selected_files),
    path("file/names", fuzz_views.get_all_file_names),
    path("file/read/<document_name>", fuzz_views.read_file),
    path("image/all/<fileName>", fuzz_views.get_all_images_by_file_name),
    path("image/by/keyword", fuzz_views.get_images_by_keyword),
    path("image/path/<path:image_path>", fuzz_views.get_image_from_path),
]
