from django.core.files.storage import default_storage
from django.conf import settings
import boto3

from wezolo.settings import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME
)


class AwsS3:
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )

    @staticmethod
    def upload_file(file, path):
        file_name = file.name
        if path:
            file_name = path + file.name

        bucket_name = AWS_STORAGE_BUCKET_NAME
        AwsS3.s3.upload_fileobj(file, bucket_name, file_name,
                                {"ContentType": f"image/{file.name.split('.')[-1].lower()}"})
        s3_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
        if s3_domain:
            file_url = f"https://{s3_domain}/{file_name}"
        else:
            file_url = default_storage.url(file_name)
        return file_url

    @staticmethod
    def get_file(file_name):
        file = default_storage.open(file_name)
        content = file.read()
        file.close()
        return content

    @staticmethod
    def delete_file(file_name):
        default_storage.delete(file_name)
