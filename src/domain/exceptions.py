class DomainException(Exception):
    """Base exception class for all domain exceptions."""
    pass

class EntityNotFoundException(DomainException):
    """Raised when a requested domain entity is not found."""
    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(f"{entity_name} with ID {entity_id} was not found.")

class InvalidCredentialsException(DomainException):
    """Raised when authentication credentials are invalid."""
    pass

class UnauthorizedException(DomainException):
    """Raised when an operation is unauthorized."""
    pass

class InvalidEntityException(DomainException):
    """Raised when a domain entity is invalid."""
    pass

class OcrProcessingException(DomainException):
    """Raised when OCR processing fails."""
    pass
