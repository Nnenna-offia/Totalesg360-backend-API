from .frameworks import FRAMEWORKS
from .gri_305 import GRI_305

# Register all framework module datasets here.
# Command logic is generic and iterates this list.
FRAMEWORK_DATASETS = [
    GRI_305,
]

__all__ = ["FRAMEWORKS", "FRAMEWORK_DATASETS", "GRI_305"]
