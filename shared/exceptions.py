class SafeSenseError(Exception):
    """Base exception for application-level errors."""


class ConfigurationError(SafeSenseError):
    """Raised when required configuration is missing."""
