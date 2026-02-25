"""Custom exceptions for DreamDuel API"""

from fastapi import status


class DreamDuelException(Exception):
    """Base exception for DreamDuel"""
    
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(DreamDuelException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(DreamDuelException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundException(DreamDuelException):
    """Exception for resource not found"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictException(DreamDuelException):
    """Exception for resource conflicts"""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class ValidationException(DreamDuelException):
    """Exception for validation errors"""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class InsufficientCreditsException(DreamDuelException):
    """Exception for insufficient credits"""
    
    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED)


class RateLimitException(DreamDuelException):
    """Exception for rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


class ExternalServiceException(DreamDuelException):
    """Exception for external service errors"""
    
    def __init__(self, message: str = "External service error", service: str = "unknown"):
        self.service = service
        super().__init__(f"{service}: {message}", status.HTTP_502_BAD_GATEWAY)


class PaymentException(DreamDuelException):
    """Exception for payment processing errors (PayPal)"""
    
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED)
