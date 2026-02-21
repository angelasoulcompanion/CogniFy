"""
CogniFy Domain Exceptions
Centralized error hierarchy for clean error handling
"""


class CogniFyError(Exception):
    """Base exception for all CogniFy domain errors"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(CogniFyError):
    """Resource not found (404)"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(CogniFyError):
    """Invalid input or business rule violation (400)"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)


class ConflictError(CogniFyError):
    """Resource conflict — duplicate or state mismatch (409)"""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class AuthenticationError(CogniFyError):
    """Authentication failure (401)"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(CogniFyError):
    """Insufficient permissions (403)"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)
