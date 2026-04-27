import hashlib
import uuid

from django.db import models
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from .settings import (
    EXPIRATION_DELTA,
    UPLOAD_TO,
    STORAGE,
    DEFAULT_MODEL_USER_FIELD_NULL,
    DEFAULT_MODEL_USER_FIELD_BLANK,
)
from .constants import CHUNKED_UPLOAD_CHOICES, UPLOADING


def generate_upload_id():
    return uuid.uuid4().hex


class AbstractChunkedUpload(models.Model):
    """
    Base chunked upload model. This model is abstract (doesn't create a table
    in the database).
    Inherit from this model to implement your own.
    """

    upload_id = models.CharField(
        max_length=32, unique=True, editable=False, default=generate_upload_id
    )
    file = models.FileField(max_length=255, upload_to=UPLOAD_TO, storage=STORAGE)
    filename = models.CharField(max_length=255)
    realname = models.CharField(max_length=255)
    offset = models.BigIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(
        choices=CHUNKED_UPLOAD_CHOICES, default=UPLOADING
    )
    completed_on = models.DateTimeField(null=True, blank=True)

    @property
    def expires_on(self):
        return self.created_on + EXPIRATION_DELTA

    @property
    def expired(self):
        return self.expires_on <= timezone.now()

    @property
    def md5(self):
        if getattr(self, "_md5", None) is None:
            md5 = hashlib.md5()
            for chunk in self.file.chunks():
                md5.update(chunk)
            self._md5 = md5.hexdigest()
        return self._md5

    def delete(self, delete_file=True, *args, **kwargs):
        if self.file:
            storage, path = self.file.storage, self.file.path
        super(AbstractChunkedUpload, self).delete(*args, **kwargs)
        if self.file and delete_file:
            storage.delete(path)

    def __str__(self):
        return "<%s - upload_id: %s - bytes: %s - status: %s>" % (
            self.filename,
            self.upload_id,
            self.offset,
            self.status,
        )

    def append_chunk(self, chunk, chunk_size=None, save=True):
        self.file.close()
        with open(self.file.path, mode="ab") as file_obj:  # mode = append+binary
            file_obj.write(
                chunk.read()
            )  # We can use .read() safely because chunk is already in memory

        if chunk_size is not None:
            self.offset += chunk_size
        elif hasattr(chunk, "size"):
            self.offset += chunk.size
        else:
            self.offset = self.file.size
        self._md5 = None  # Clear cached md5
        if save:
            self.save()
        self.file.close()  # Flush

    def get_uploaded_file(self):
        self.file.close()
        self.file.open(mode="rb")  # mode = read+binary
        return UploadedFile(file=self.file, name=self.filename, size=self.offset)

    class Meta:
        abstract = True


class ChunkedUpload(AbstractChunkedUpload):
    """
    Default chunked upload model.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chunked_uploads",
        null=DEFAULT_MODEL_USER_FIELD_NULL,
        blank=DEFAULT_MODEL_USER_FIELD_BLANK,
    )
    hash = models.CharField(max_length=32, db_index=True)


class FileProcessing(models.Model):
    """
    Tracks background processing state for a completed `ChunkedUpload`.
    Linked one-to-one so each upload has at most one processing record.
    """

    STATUS_QUEUED = 0
    STATUS_PROCESSING = 1
    STATUS_SUCCESS = 2
    STATUS_FAILED = 3

    STATUS_CHOICES = (
        (STATUS_QUEUED, "Queued"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    upload = models.OneToOneField(
        ChunkedUpload, on_delete=models.CASCADE, related_name="processing"
    )
    task_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_QUEUED)
    progress = models.PositiveSmallIntegerField(default=0)
    started_on = models.DateTimeField(null=True, blank=True)
    finished_on = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Processing(upload_id={self.upload.upload_id}, status={self.status}, task_id={self.task_id})"
