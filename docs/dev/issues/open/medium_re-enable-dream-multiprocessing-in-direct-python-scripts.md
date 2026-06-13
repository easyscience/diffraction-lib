# 95. Re-Enable DREAM Multiprocessing in Direct Python Scripts

**Priority:** `[priority] medium`

**Type:** Performance / Script runtime

On macOS and other spawn-based platforms, direct Bayesian tutorial
execution via `python script.py` or wrappers such as
`pixi run tutorial docs/docs/tutorials/ed-21.py` can fail during BUMPS
`MPMapper` startup because worker processes re-import `__main__` and
re-execute top-level tutorial code. The current defensive workaround is
to fall back to serial execution for these direct-script entry points,
which avoids the crash but disables DREAM multiprocessing and causes a
large performance drop.

Observed behavior for `ed-21` today:

- Jupyter execution and `easydiffraction PROJECT_DIR fit` both appear to
  use working parallel DREAM and complete `361/361` in about 40 seconds.
- Direct Python-script execution of the same tutorial runs `361/361` in
  about 220 seconds, consistent with the serial fallback path.

**Possible solution:** keep the existing tracker-state cleanup before
pickling and mapper startup, but replace the blanket serial fallback
with an EasyDiffraction-controlled multiprocessing context policy. For
direct Python script entry points, prefer a `fork` context when
available so workers do not re-import the tutorial top level. Keep the
existing behavior for import-safe module entry points such as
`easydiffraction PROJECT_DIR fit` and for platforms where `fork` is
unavailable. Document the tradeoff clearly because `fork` on macOS is
less conservative than `spawn`.

**Depends on:** related to issue 89, but independent.
