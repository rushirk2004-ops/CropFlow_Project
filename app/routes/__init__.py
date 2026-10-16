"""CropFlow routes package."""

from .dashboard import dashboard_bp
from .farms import farms_bp
from .optimization import optimization_bp
from .reports import reports_bp

__all__ = ["dashboard_bp", "farms_bp", "optimization_bp", "reports_bp"]
