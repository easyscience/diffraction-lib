from __future__ import annotations

from typing import ClassVar

from easydiffraction import log
from easydiffraction.utils.environment import in_jupyter

# Optional import – safe even if IPython is not installed
try:
    from IPython.display import HTML
    from IPython.display import display
except Exception:
    display = None
    HTML = None


class JupyterScrollManager:
    """Ensures that Jupyter output cells are not scrollable (applied
    once).
    """

    _applied: ClassVar[bool] = False

    @classmethod
    def disable_jupyter_scroll(cls) -> None:
        """Inject CSS to prevent output cells from being scrollable."""
        if cls._applied or not in_jupyter() or display is None or HTML is None:
            return

        css = """
        <style>
        /* Disable scrolling (already present) */
        .jp-OutputArea,
        .jp-OutputArea-child,
        .jp-OutputArea-scrollable,
        .output_scroll {
            max-height: none !important;
            overflow-y: visible !important;
        }
        """
        try:
            display(HTML(css))
            cls._applied = True
        except Exception:
            log.debug('Failed to inject Jupyter CSS to disable scrolling.')
