class DanceAvatarError(RuntimeError):
    """Base error for user-facing pipeline failures."""


class DependencyError(DanceAvatarError):
    """Raised when an external dependency is missing."""
