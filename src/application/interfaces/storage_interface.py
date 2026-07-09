from abc import ABC, abstractmethod

class IStorageService(ABC):
    @abstractmethod
    def upload_file(self, file_data: bytes, destination_path: str) -> str:
        """Uploads file data and returns a unique path or URI."""
        pass

    @abstractmethod
    def download_file(self, file_path: str) -> bytes:
        """Downloads and returns file data in bytes."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """Deletes file from storage."""
        pass
