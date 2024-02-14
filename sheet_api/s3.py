import os

import boto3
import uuid

BUCKET_NAME = "sheet-musicle"
CLOUDFRONT_DISTRO = os.getenv("CLOUDFRONT_DISTRO")


def upload_sheet_music_file(filename, contents) -> str:
    s3 = boto3.client("s3")
    extension = filename.split(".")[-1]
    uuid_filename = str(uuid.uuid4())

    new_filename = f"{uuid_filename}.{extension}"

    s3.upload_fileobj(contents, BUCKET_NAME, new_filename)
    print("Upload Successful")

    cloudfront_path = CLOUDFRONT_DISTRO + "/" + new_filename
    return cloudfront_path
