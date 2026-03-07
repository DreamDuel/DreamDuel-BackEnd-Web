"""Custom exceptions for DreamDuel API"""

from fastapi import status


class DreamDuelException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(DreamDuelException):
    def __init__(self, resource_type: str = "Resource", resource_id: str = None):
        msg = f"{resource_type} with ID '{resource_id}' not found" if resource_id else f"{resource_type} not found"
        super().__init__(msg, status.HTTP_404_NOT_FOUND)


class PaymentException(DreamDuelException):
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED)


class RateLimitException(DreamDuelException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


class ExternalServiceException(DreamDuelException):
    def __init__(self, message: str = "External service error", service: str = "unknown"):
        self.service = service
        super().__init__(f"{service}: {message}", status.HTTP_502_BAD_GATEWAY)


class InsufficientCreditsException(DreamDuelException):
    def __init__(self, required: int = 1, available: int = 0):
        super().__init__(
            f"Insufficient credits. Required: {required}, Available: {available}",
            status.HTTP_402_PAYMENT_REQUIRED
        )
