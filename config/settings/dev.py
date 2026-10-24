import importlib.util

from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

if importlib.util.find_spec("debug_toolbar") is not None:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]

USE_S3 = env.bool("USE_S3", default=False)

if USE_S3:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", default="minioadmin")
    AWS_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY", default="minioadmin")
    AWS_STORAGE_BUCKET_NAME = env("S3_BUCKET", default="meridian")
    AWS_S3_ENDPOINT_URL = env("S3_ENDPOINT", default="http://minio:9000")
    AWS_S3_REGION_NAME = env("S3_REGION", default="us-east-1")
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_S3_USE_SSL = not AWS_S3_ENDPOINT_URL.startswith("http://")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"
