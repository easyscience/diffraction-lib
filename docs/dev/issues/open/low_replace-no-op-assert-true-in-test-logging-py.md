# 160. Replace No-Op `assert True` in `test_logging.py`

**Priority:** `[priority] low`

**Type:** Test coverage

`test_logger_configure_and_warn_reaction` exercises logger
configure/level/mode calls but ends with `assert True` ("absence of
exception is success"), so it asserts nothing about behaviour — a
regression that changed log routing or level handling would not be
caught.

**Fix:** assert on captured log records/levels (e.g. via `caplog`)
instead of `assert True`.

**TODOs / locations:**

- [test_logging.py](../../../../tests/unit/easydiffraction/utils/test_logging.py#L13)

**Depends on:** nothing.
