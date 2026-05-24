# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Environment-aware activity indicator for long-running tasks."""

from __future__ import annotations

import html
import uuid
from contextlib import AbstractContextManager
from contextlib import suppress
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING
from typing import Self

if TYPE_CHECKING:
    from types import TracebackType

try:
    from IPython.display import HTML
    from IPython.display import DisplayHandle
    from IPython.display import Javascript
    from IPython.display import display
except ImportError:  # pragma: no cover - optional dependency
    HTML = None
    DisplayHandle = None
    Javascript = None
    display = None

from rich.console import Group
from rich.live import Live
from rich.protocol import is_renderable
from rich.text import Text

from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import ConsoleManager

ACTIVITY_LABEL_BURN_IN = 'Burn-in...'
ACTIVITY_LABEL_FITTING = 'Fitting...'
ACTIVITY_LABEL_POST_PROCESSING = 'Post-processing...'
ACTIVITY_LABEL_PRE_PROCESSING = 'Pre-processing...'
ACTIVITY_LABEL_PROCESSING = 'Processing...'
ACTIVITY_LABEL_SAMPLING = 'Sampling...'
ACTIVITY_ACCENT_COLOR = '#d97706'
ACTIVITY_TERMINAL_STYLE = ACTIVITY_ACCENT_COLOR
ACTIVITY_TERMINAL_FALLBACK_STYLE = 'bold yellow'

SPINNER_FRAMES: tuple[str, ...] = (
    '⠋',
    '⠙',
    '⠹',
    '⠸',
    '⠼',
    '⠴',
    '⠦',
    '⠧',
    '⠇',
    '⠏',
)
_SPINNER_FRAME_SECONDS = 0.1
_JUPYTER_SPINNER_SECONDS = 1.0


def resolve_activity_terminal_style(console: object | None = None) -> str:
    """
    Return a terminal-safe activity indicator style.

    Parameters
    ----------
    console : object | None, default=None
        Console-like object whose ``color_system`` determines whether
        the accent color can be rendered directly.

    Returns
    -------
    str
        The preferred terminal style for the current console.
    """
    color_system = getattr(console, 'color_system', None)
    if color_system in {'standard', 'windows'}:
        return ACTIVITY_TERMINAL_FALLBACK_STYLE
    return ACTIVITY_TERMINAL_STYLE


class _TerminalLiveHandle:
    """
    Adapter exposing update()/close() for terminal live updates.

    Wraps a ``rich.live.Live`` instance so callers can treat terminal
    and notebook handles through a single update-oriented interface.
    """

    def __init__(self, *, console: object, auto_refresh: bool = True) -> None:
        self._renderable: object = Text('')
        self._live = Live(
            console=console,
            auto_refresh=auto_refresh,
            refresh_per_second=1 / _SPINNER_FRAME_SECONDS,
            get_renderable=self._get_renderable,
            vertical_overflow='visible',
        )
        self._live.start()

    def _get_renderable(self) -> object:
        renderable = self._renderable
        if callable(renderable):
            return renderable()
        return renderable

    def update(self, renderable: object) -> None:
        """
        Refresh the live display with a new renderable.

        Parameters
        ----------
        renderable : object
            A Rich-compatible renderable to display.
        """
        self._renderable = renderable
        self._live.refresh()

    def close(self) -> None:
        """Stop the live display, suppressing any errors."""
        with suppress(Exception):
            self._live.stop()


def make_display_handle(*, auto_refresh: bool = True) -> object | None:
    """
    Create a generic in-place display handle for the active environment.

    Parameters
    ----------
    auto_refresh : bool, default=True
        Whether a terminal live handle should refresh continuously.

    Returns
    -------
    object | None
        An IPython ``DisplayHandle`` in notebooks, a terminal live
        handle in the console, or ``None`` if neither is available.
    """
    if in_jupyter() and DisplayHandle is not None and HTML is not None:
        handle = DisplayHandle()
        with suppress(Exception):
            handle.display(HTML(''))
        return handle

    return _TerminalLiveHandle(console=ConsoleManager.get(), auto_refresh=auto_refresh)


class ActivityIndicator:
    """
    Render a live activity indicator for long-running work.

    Parameters
    ----------
    label : str, default=ACTIVITY_LABEL_PROCESSING
        User-facing activity label.
    verbosity : VerbosityEnum
        Output verbosity controlling whether live display is shown.
    display_handle : object | None, default=None
        Optional existing live display handle to reuse.
    animated : bool, default=True
        Whether to animate the spinner label continuously.
    refresh_per_second : float | None, default=None
        Optional override for the Rich Live refresh rate. When ``None``,
        defaults to one refresh per spinner frame. Lower values reduce
        terminal flicker for multi-line live regions.
    """

    def __init__(
        self,
        label: str = ACTIVITY_LABEL_PROCESSING,
        *,
        verbosity: VerbosityEnum,
        display_handle: object | None = None,
        animated: bool = True,
        refresh_per_second: float | None = None,
    ) -> None:
        self._label = label
        self._verbosity = verbosity
        self._content: object | None = None
        self._provided_display_handle = display_handle
        self._refresh_per_second = (
            refresh_per_second if refresh_per_second is not None else 1 / _SPINNER_FRAME_SECONDS
        )
        self._animated = animated
        self._display_handle: object | None = None
        self._live: object | None = None
        self._running = False
        self._keep_stopped_label = False
        self._started_at = monotonic()

    def start(self) -> None:
        """
        Start the live activity indicator.

        Returns
        -------
        None
            Starts live rendering unless verbosity is silent.
        """
        if self._verbosity is VerbosityEnum.SILENT or self._running:
            return

        self._running = True
        self._keep_stopped_label = False
        self._started_at = monotonic()

        if self._provided_display_handle is not None:
            self._display_handle = self._provided_display_handle
            self._refresh()
            return

        if in_jupyter() and DisplayHandle is not None and HTML is not None:
            handle = DisplayHandle()
            self._display_handle = handle
            with suppress(Exception):
                handle.display(HTML(self._render_html()))
            return

        live = Live(
            console=ConsoleManager.get(),
            auto_refresh=self._animated,
            refresh_per_second=self._refresh_per_second,
            get_renderable=self._terminal_renderable,
            vertical_overflow='visible',
        )
        live.start()
        self._live = live

    def update(
        self,
        *,
        label: str | None = None,
        content: object | None = None,
    ) -> None:
        """
        Refresh the current label and optional rendered content.

        Parameters
        ----------
        label : str | None, default=None
            Replacement activity label. When ``None``, keep the current
            label.
        content : object | None, default=None
            Optional content rendered above the indicator. When
            ``None``, keep the current content.
        """
        if label is not None:
            self._label = label
        if content is not None:
            self._content = content
        self._refresh()

    def stop(self, *, final_label: str | None = None) -> None:
        """
        Stop live rendering and keep optional final content visible.

        Parameters
        ----------
        final_label : str | None, default=None
            Optional final label to leave in place after stopping. When
            omitted, only the current content remains visible.
        """
        self._running = False
        self._keep_stopped_label = final_label is not None
        if final_label is not None:
            self._label = final_label

        self._refresh()

        if self._live is not None:
            with suppress(Exception):
                self._live.stop()
        self._live = None
        self._display_handle = None

    def _terminal_renderable(self) -> object:
        """Return the terminal renderable for the current state."""
        renderables: list[object] = []
        content = self._terminal_content()
        if content is not None:
            renderables.append(content)

        indicator_line = self._terminal_indicator_line()
        if indicator_line is not None:
            renderables.append(indicator_line)

        if not renderables:
            return Text('')

        if len(renderables) == 1:
            return renderables[0]

        return Group(*renderables)

    def _refresh(self) -> None:
        if self._verbosity is VerbosityEnum.SILENT:
            return

        if self._display_handle is not None:
            self._refresh_display_handle()
            return

        if self._live is not None:
            with suppress(Exception):
                self._live.refresh()

    def _refresh_display_handle(self) -> None:
        if self._display_handle is None:
            return

        if (
            HTML is not None
            and DisplayHandle is not None
            and isinstance(self._display_handle, DisplayHandle)
        ):
            with suppress(Exception):
                self._display_handle.update(HTML(self._render_html()))
            return

        renderable: object = self._terminal_renderable()
        if isinstance(self._display_handle, _TerminalLiveHandle):
            renderable = self._terminal_renderable
        with suppress(Exception):
            self._display_handle.update(renderable)

    def _terminal_content(self) -> object | None:
        if self._content is None:
            return None
        if is_renderable(self._content):
            return self._content
        return Text(str(self._content))

    def _terminal_indicator_line(self) -> Text | None:
        style = resolve_activity_terminal_style(ConsoleManager.get())
        if self._running:
            if self._animated:
                frame = self._current_frame()
                return Text(f'{frame} {self._label}', style=style)
            return Text(self._label, style=style)
        if self._keep_stopped_label:
            return Text(self._label, style=style)
        return None

    def _current_frame(self) -> str:
        elapsed = monotonic() - self._started_at
        frame_index = int(elapsed / _SPINNER_FRAME_SECONDS) % len(SPINNER_FRAMES)
        return SPINNER_FRAMES[frame_index]

    def _render_html(self) -> str:
        content_html = self._html_content()
        indicator_html = self._html_indicator()

        sections = [section for section in (content_html, indicator_html) if section]
        if not sections:
            return ''

        body = ''.join(sections)
        return f'{self._html_style()}<div class="ed-activity-stack">{body}</div>'

    def _html_content(self) -> str:
        if self._content is None:
            return ''
        if isinstance(self._content, str):
            return self._content

        data = getattr(self._content, 'data', None)
        if isinstance(data, str):
            return data

        text = html.escape(str(self._content))
        return f'<pre class="ed-activity-pre">{text}</pre>'

    def _html_indicator(self) -> str:
        safe_label = html.escape(self._label)

        if self._running:
            if not self._animated:
                return (
                    '<div class="ed-activity">'
                    f'<span class="ed-activity-label">{safe_label}</span>'
                    '</div>'
                )
            return (
                '<div class="ed-activity">'
                '<span class="ed-activity-spinner" aria-hidden="true"></span>'
                f'<span class="ed-activity-label">{safe_label}</span>'
                '</div>'
            )

        if self._keep_stopped_label:
            return (
                '<div class="ed-activity">'
                f'<span class="ed-activity-label">{safe_label}</span>'
                '</div>'
            )

        return ''

    @staticmethod
    def _html_style() -> str:
        keyframes = []
        total_frames = len(SPINNER_FRAMES)
        for index, frame in enumerate(SPINNER_FRAMES):
            percent = int(index * 100 / total_frames)
            keyframes.append(f'{percent}% {{ content: "{frame}"; }}')
        keyframes.append(f'100% {{ content: "{SPINNER_FRAMES[0]}"; }}')
        keyframe_css = ' '.join(keyframes)

        return (
            '<style>'
            '.ed-activity-stack {'
            'display: flex;'
            'flex-direction: column;'
            'align-items: flex-start;'
            'gap: 0.35rem;'
            'margin-top: 0.5rem;'
            '}'
            '.ed-activity {'
            'display: inline-flex;'
            'align-items: center;'
            'gap: 0.45rem;'
            f'color: {ACTIVITY_ACCENT_COLOR};'
            'font-size: 0.95rem;'
            'font-weight: 400;'
            'line-height: 1.1;'
            '}'
            '.ed-activity-label {'
            'font-family: var(--jp-ui-font-family, -apple-system, BlinkMacSystemFont, '
            '"Segoe UI", sans-serif);'
            '}'
            '.ed-activity-pre {'
            'margin: 0;'
            'font-family: ui-monospace, SFMono-Regular, Menlo, monospace;'
            'white-space: pre-wrap;'
            '}'
            '.ed-activity-spinner {'
            'font-family: ui-monospace, SFMono-Regular, Menlo, monospace;'
            '}'
            '.ed-activity-spinner::before {'
            f'animation: ed-activity-frames {_JUPYTER_SPINNER_SECONDS}s steps(1) infinite;'
            'content: "⠋";'
            'display: inline-block;'
            'width: 1ch;'
            '}'
            f'@keyframes ed-activity-frames {{ {keyframe_css} }}'
            '</style>'
        )


class _ActivityIndicatorContext(AbstractContextManager[ActivityIndicator]):
    """Context manager wrapper for ``ActivityIndicator``."""

    def __init__(self, *, label: str, verbosity: VerbosityEnum) -> None:
        self._indicator = ActivityIndicator(label, verbosity=verbosity)

    def __enter__(self) -> ActivityIndicator:
        self._indicator.start()
        return self._indicator

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type
        del exc_value
        del traceback
        self._indicator.stop()


def activity_indicator(
    label: str = ACTIVITY_LABEL_PROCESSING,
    *,
    verbosity: VerbosityEnum,
) -> AbstractContextManager[ActivityIndicator]:
    """
    Manage an activity indicator around a block of work.

    Parameters
    ----------
    label : str, default=ACTIVITY_LABEL_PROCESSING
        User-facing activity label.
    verbosity : VerbosityEnum
        Output verbosity controlling whether live display is shown.

    Returns
    -------
    AbstractContextManager[ActivityIndicator]
        Context manager that starts the indicator on entry and stops it
        on exit.
    """
    return _ActivityIndicatorContext(label=label, verbosity=verbosity)


class NotebookFitStopControl(AbstractContextManager):
    """Display a Jupyter stop button for fitting runs."""

    def __init__(self, *, verbosity: VerbosityEnum) -> None:
        self._verbosity = verbosity
        self._display_handle: object | None = None
        self._element_id = f'ed-fit-stop-{uuid.uuid4().hex}'
        self._kernel_id = self._current_kernel_id()

    def __enter__(self) -> Self:
        """Show the stop button."""
        self.show()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Update or clear the stop button when leaving the context."""
        del exc_type
        del exc_value
        del traceback
        self.close()

    def show(self) -> None:
        """Render the stop button when running in a notebook."""
        if not self._can_display():
            return

        handle = DisplayHandle()
        self._display_handle = handle
        with suppress(Exception):
            handle.display(HTML(self._active_html()))
            display(Javascript(self._interrupt_javascript()))

    def close(self) -> None:
        """Clear the stop button when fitting ends."""
        if self._display_handle is None or HTML is None:
            return

        with suppress(Exception):
            self._display_handle.update(HTML(''))
        self._display_handle = None

    def _can_display(self) -> bool:
        return (
            self._verbosity is not VerbosityEnum.SILENT
            and in_jupyter()
            and DisplayHandle is not None
            and HTML is not None
            and Javascript is not None
            and display is not None
        )

    def _active_html(self) -> str:
        return (
            '<style>'
            '.ed-fit-stop-control {'
            'display: inline-flex;'
            'align-items: center;'
            'gap: 0.5rem;'
            'margin: 0.35rem 0 0.45rem 0;'
            'font-family: var(--jp-ui-font-family, -apple-system, BlinkMacSystemFont, '
            '"Segoe UI", sans-serif);'
            '}'
            '.ed-fit-stop-button {'
            'border: 1px solid #b91c1c;'
            'border-radius: 4px;'
            'background: #dc2626;'
            'color: white;'
            'font-size: 0.9rem;'
            'line-height: 1.1;'
            'padding: 0.35rem 0.65rem;'
            'cursor: pointer;'
            '}'
            '.ed-fit-stop-button:disabled {'
            'cursor: default;'
            'opacity: 0.65;'
            '}'
            '.ed-fit-stop-status {'
            'color: var(--jp-ui-font-color2, #6b7280);'
            'font-size: 0.85rem;'
            '}'
            '</style>'
            f'<div id="{self._element_id}" class="ed-fit-stop-control">'
            f'<button id="{self._element_id}-button" '
            'class="ed-fit-stop-button" type="button">Stop fitting</button>'
            f'<span id="{self._element_id}-status" class="ed-fit-stop-status"></span>'
            '</div>'
        )

    def _interrupt_javascript(self) -> str:
        button_id = f'{self._element_id}-button'
        status_id = f'{self._element_id}-status'
        kernel_id = self._kernel_id
        return f"""
(function() {{
  const button = document.getElementById({button_id!r});
  const status = document.getElementById({status_id!r});
  const kernelId = {kernel_id!r};
  if (!button) {{
    return;
  }}

  function setStatus(text) {{
    if (status) {{
      status.textContent = text;
    }}
  }}

  function pageConfig() {{
    const element = document.getElementById('jupyter-config-data');
    if (!element || !element.textContent) {{
      return {{}};
    }}
    try {{
      return JSON.parse(element.textContent);
    }} catch (error) {{
      return {{}};
    }}
  }}

  function baseUrl(config) {{
    const configured = config.baseUrl || config.base_url ||
      (window.Jupyter && Jupyter.notebook && Jupyter.notebook.base_url);
    if (configured) {{
      return configured.endsWith('/') ? configured : configured + '/';
    }}
    const markers = ['/lab/', '/notebooks/', '/tree/'];
    for (const marker of markers) {{
      const index = window.location.pathname.indexOf(marker);
      if (index >= 0) {{
        return window.location.pathname.slice(0, index + 1);
      }}
    }}
    return '/';
  }}

  function token(config) {{
    return config.token || new URLSearchParams(window.location.search).get('token') || '';
  }}

  function cookie(name) {{
    const prefix = name + '=';
    for (const part of document.cookie.split(';')) {{
      const trimmed = part.trim();
      if (trimmed.startsWith(prefix)) {{
        return decodeURIComponent(trimmed.slice(prefix.length));
      }}
    }}
    return '';
  }}

  function notebookPath() {{
    const decoded = decodeURIComponent(window.location.pathname);
    const markers = ['/lab/tree/', '/notebooks/', '/tree/'];
    for (const marker of markers) {{
      const index = decoded.indexOf(marker);
      if (index >= 0) {{
        return decoded.slice(index + marker.length);
      }}
    }}
    return '';
  }}

  async function kernelFromSessions(config) {{
    const url = new URL(baseUrl(config) + 'api/sessions', window.location.origin);
    const authToken = token(config);
    if (authToken) {{
      url.searchParams.set('token', authToken);
    }}
    const response = await fetch(url, {{credentials: 'same-origin'}});
    if (!response.ok) {{
      return '';
    }}
    const sessions = await response.json();
    const path = notebookPath();
    const session = sessions.find((item) => item.path === path) || sessions[0];
    return session && session.kernel ? session.kernel.id : '';
  }}

  async function interruptKernel(config, resolvedKernelId) {{
    const url = new URL(
      baseUrl(config) + 'api/kernels/' + resolvedKernelId + '/interrupt',
      window.location.origin
    );
    const authToken = token(config);
    if (authToken) {{
      url.searchParams.set('token', authToken);
    }}
    const xsrfToken = cookie('_xsrf');
    const headers = {{}};
    if (xsrfToken) {{
      headers['X-XSRFToken'] = xsrfToken;
    }}
    const response = await fetch(url, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: headers
    }});
    return response.ok;
  }}

  button.addEventListener('click', async function() {{
    button.disabled = true;
    setStatus('Stopping...');
    const config = pageConfig();
    try {{
      const resolvedKernelId = kernelId || await kernelFromSessions(config);
      if (!resolvedKernelId) {{
        throw new Error('Could not resolve the current kernel id.');
      }}
      const interrupted = await interruptKernel(config, resolvedKernelId);
      if (!interrupted) {{
        throw new Error('Jupyter Server rejected the interrupt request.');
      }}
      setStatus('Interrupt sent...');
    }} catch (error) {{
      button.disabled = false;
      setStatus('Use Kernel > Interrupt to stop this fit.');
    }}
  }});
}})();
"""

    @staticmethod
    def _current_kernel_id() -> str:
        """Return the active ipykernel id when available."""
        try:
            from IPython import get_ipython  # type: ignore[import-not-found]  # noqa: PLC0415
        except ImportError:  # pragma: no cover - optional dependency
            return ''

        shell = get_ipython()
        kernel = getattr(shell, 'kernel', None)
        kernel_id = getattr(kernel, 'kernel_id', None)
        if kernel_id:
            return str(kernel_id)

        try:
            from ipykernel.connect import (  # type: ignore[import-not-found]  # noqa: PLC0415
                get_connection_file,
            )
        except ImportError:  # pragma: no cover - optional dependency
            return ''

        with suppress(Exception):
            return NotebookFitStopControl._kernel_id_from_connection_file(
                get_connection_file()
            )
        return ''

    @staticmethod
    def _kernel_id_from_connection_file(connection_file: str) -> str:
        """Extract the kernel id from an ipykernel connection file."""
        file_name = Path(connection_file).name
        prefix = 'kernel-'
        suffix = '.json'
        if not file_name.startswith(prefix) or not file_name.endswith(suffix):
            return ''
        return file_name[len(prefix) : -len(suffix)]


def notebook_fit_stop_control(
    *,
    verbosity: VerbosityEnum,
) -> NotebookFitStopControl:
    """Return a notebook stop-control context for fitting runs."""
    return NotebookFitStopControl(verbosity=verbosity)
