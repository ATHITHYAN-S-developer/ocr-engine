import os
import boto3
from botocore.config import Config
from src.application.interfaces.storage_interface import IStorageService
from src.config import settings

class LocalStorageService(IStorageService):
    def __init__(self):
        self.base_dir = os.path.abspath(settings.STORAGE_LOCAL_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_data: bytes, destination_path: str) -> str:
        full_path = os.path.join(self.base_dir, destination_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_data)
        return destination_path

    def download_file(self, file_path: str) -> bytes:
        full_path = os.path.join(self.base_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(full_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> None:
        full_path = os.path.join(self.base_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)


class S3StorageService(IStorageService):
    def __init__(self):
        self.bucket = settings.AWS_S3_BUCKET_NAME
        
        # Configure client options (supports custom endpoints like MinIO)
        aws_config = Config(signature_version="s3v4")
        session_kwargs = {}
        if settings.AWS_ACCESS_KEY_ID:
            session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        if settings.AWS_SECRET_ACCESS_KEY:
            session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=aws_config,
            **session_kwargs
        )

    def upload_file(self, file_data: bytes, destination_path: str) -> str:
        self.s3.put_object(
            Bucket=self.bucket,
            Key=destination_path,
            Body=file_data
        )
        return destination_path

    def download_file(self, file_path: str) -> bytes:
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=file_path)
            return response["Body"].read()
        except Exception as e:
            raise FileNotFoundError(f"S3 Object not found: {file_path}. Details: {str(e)}")

    def delete_file(self, file_path: str) -> None:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=file_path)
        except Exception:
            pass


def get_storage_service() -> IStorageService:
    if settings.STORAGE_PROVIDER.lower() == "s3":
        return S3StorageService()
    return LocalStorageService()
