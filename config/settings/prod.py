from boto3.s3.transfer import TransferConfig

from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("S3_BUCKET")
AWS_S3_ENDPOINT_URL = env("S3_ENDPOINT", default=None)
AWS_S3_REGION_NAME = env("S3_REGION", default=None)
AWS_S3_ADDRESSING_STYLE = "path"
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_CUSTOM_DOMAIN = env("S3_PUBLIC_DOMAIN", default=None)

# The container has 256 MB, two Django workers take ~160 MB of it. Defaults of boto3 and
# django-storages are tuned for big servers and kept whole files in memory:
# - an upload read up to 10 parts of 8 MB ahead: +103 MB for a 126 MB file, now +26 MB;
_upload_config = TransferConfig(max_concurrency=2)
_upload_config.max_in_memory_upload_chunks = 2
AWS_S3_TRANSFER_CONFIG = _upload_config
# - a file opened for reading was downloaded into memory (0 = never spill to disk)
AWS_S3_MAX_MEMORY_SIZE = 1024 * 1024
