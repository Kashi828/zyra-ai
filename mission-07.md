# Mission 07 — Web Agent

ZYRA can now expose a protected web-agent tool layer using Playwright.

## Added tools
- `browser_available`: reports whether Playwright is installed.
- `browse_page`: open an HTTP/HTTPS page in a headless Chromium session and return title, URL, and body text.
- `take_browser_snapshot`: capture a full-page screenshot.
- `save_page_json`: persist extracted page metadata/text as JSON.

## Safety defaults
- Only HTTP/HTTPS URLs are accepted.
- Localhost and loopback browser targets are blocked by default.
- Browser capabilities are allow-listed through the existing policy/permission engine.
- Browser capture/save operations are confirmation-gated.

## Install
```powershell
python -m pip install playwright
python -m playwright install chromium
```

## Example
```powershell
python -c "from tools.browser import browse_page; print(browse_page({'url':'https://example.com'}))"
```
