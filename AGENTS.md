# AGENTS Notes

## Browser tab count validation

- For the backend browser tab count work in `src/browser.py`, validation was done with:
  - `.\venv\Scripts\python.exe -m pytest tests/test_browser.py tests/test_window.py`
  - direct Python probes against `uiautomation`
  - direct checks against `http://localhost:8080/api/snapshot`
- `docs/PLAYWRIGHT_CLI_GUIDE.md` was not used for those backend tests.
- Use `docs/PLAYWRIGHT_CLI_GUIDE.md` only when the task is UI/E2E exploration or Playwright CLI usage.

## Current observed UI state

- Edge badge for `tab_count` is rendering correctly.
- Comet badge is still not rendering correctly and should be treated as an open validation/debug item.
