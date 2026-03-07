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


# Alias for backward compatibility
UnauthorizedException = AuthenticationException


class AuthorizationException(DreamDuelException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


# Alias for backward compatibility
ForbiddenException = AuthorizationException


class NotFoundException(DreamDuelException):
    """Exception for resource not found"""
    
    def __init__(self, resource_type: str = "Resource", resource_id: str = None):
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictException(DreamDuelException):
    """Exception for resource conflicts"""
    
    def __init__(self, resource_type: str = "Resource", field: str = None, value: str = None):
        if field and value:
            message = f"{resource_type} with {field} '{value}' already exists"
        elif field:
            message = f"{resource_type} {field} already exists"
        else:
            message = f"{resource_type} already exists"
        super().__init__(message, status.HTTP_409_CONFLICT)


class ValidationException(DreamDuelException):
    """Exception for validation errors"""
    
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class InsufficientCreditsException(DreamDuelException):
    """Exception for insufficient credits"""
    
    def __init__(self, required: int = 1, available: int = 0):
        message = f"Insufficient credits. Required: {required}, Available: {available}"
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


# Aliases for backward compatibility
CloudinaryException = ExternalServiceException
EmailException = ExternalServiceException


class PaymentException(DreamDuelException):
    """Exception for payment processing errors (PayPal)"""
    
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED)
