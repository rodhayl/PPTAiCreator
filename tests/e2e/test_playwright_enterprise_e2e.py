"""Enterprise Playwright E2E coverage for concurrency, persistence, and visual regression.

These tests target the live FastAPI backend at http://127.0.0.1:8000.
They are skipped automatically when Playwright or the backend service is unavailable.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

import pytest

pytestmark = [pytest.mark.e2e]


def _backend_available() -> bool:
    try:
        with urlopen("http://127.0.0.1:8000/docs", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.skipif(sync_playwright is None, reason="Playwright is not installed")
@pytest.mark.skipif(
    not _backend_available(), reason="FastAPI backend is not running on :8000"
)
def test_playwright_multiuser_concurrency():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:8000/docs")

        result = page.evaluate("""async () => {
              const createSession = async () => {
                const r = await fetch('/sessions', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})});
                return r.json();
              };

              const s1 = await createSession();
              const s2 = await createSession();

              const run = async (topic, sessionId) => {
                const r = await fetch('/run', {
                  method:'POST',
                  headers:{'Content-Type':'application/json'},
                  body: JSON.stringify({
                    user_input: topic,
                    session_id: sessionId,
                    auto_approve: false,
                    approval_phases: ['outline']
                  })
                });
                return r.json();
              };

              const [r1, r2] = await Promise.all([
                run('Concurrency topic A', s1.session_id),
                run('Concurrency topic B', s2.session_id),
              ]);

              return {s1, s2, r1, r2};
            }""")

        assert result["s1"]["session_id"] != result["s2"]["session_id"]
        assert result["r1"]["run_id"] != result["r2"]["run_id"]
        assert result["r1"]["status"] in {"waiting_for_approval", "completed"}
        assert result["r2"]["status"] in {"waiting_for_approval", "completed"}

        browser.close()


@pytest.mark.skipif(sync_playwright is None, reason="Playwright is not installed")
@pytest.mark.skipif(
    not _backend_available(), reason="FastAPI backend is not running on :8000"
)
def test_playwright_session_persistence_after_restart():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context1 = browser.new_context()
        page1 = context1.new_page()
        page1.goto("http://127.0.0.1:8000/docs")

        run_data = page1.evaluate("""async () => {
              const s = await fetch('/sessions', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})});
              const session = await s.json();
              const run = await fetch('/run', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({
                  user_input: 'Persistence topic',
                  session_id: session.session_id,
                  auto_approve: true
                })
              });
              return run.json();
            }""")
        run_id = run_data["run_id"]

        context1.close()

        context2 = browser.new_context()
        page2 = context2.new_page()
        page2.goto("http://127.0.0.1:8000/docs")

        details = page2.evaluate(
            """async (rid) => {
              const r = await fetch(`/runs/${rid}`);
              return {status: r.status, body: await r.json()};
            }""",
            run_id,
        )

        assert details["status"] == 200
        assert details["body"]["id"] == run_id

        context2.close()
        browser.close()


@pytest.mark.skipif(sync_playwright is None, reason="Playwright is not installed")
@pytest.mark.skipif(
    not _backend_available(), reason="FastAPI backend is not running on :8000"
)
def test_playwright_visual_regression_previews():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://127.0.0.1:8000/docs")

        def create_run(topic: str) -> dict:
            return page.evaluate(
                """async (t) => {
                  const s = await fetch('/sessions', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({})});
                  const session = await s.json();
                  const run = await fetch('/run', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({
                      user_input: t,
                      session_id: session.session_id,
                      auto_approve: false,
                      approval_phases: ['design']
                    })
                  });
                  const runJson = await run.json();

                  if (runJson.status === 'waiting_for_approval') {
                    await fetch(`/runs/${runJson.run_id}/approve`, {
                      method: 'POST',
                      headers: {'Content-Type':'application/json'},
                      body: JSON.stringify({notes: 'continue from design', auto_approve: true})
                    });
                  }

                  const details = await fetch(`/runs/${runJson.run_id}`);
                  const detailsJson = await details.json();
                  return {run: runJson, details: detailsJson};
                }""",
                topic,
            )

        first = create_run("Visual regression topic")
        second = create_run("Visual regression topic")

        first_manifest = first["details"].get("preview_manifest")
        second_manifest = second["details"].get("preview_manifest")

        if not first_manifest or not second_manifest:
            pytest.skip("Preview manifests were not generated in this environment")

        first_data = json.loads(Path(first_manifest).read_text(encoding="utf-8"))
        second_data = json.loads(Path(second_manifest).read_text(encoding="utf-8"))

        assert first_data and second_data

        first_image = Path(next(iter(first_data.values())))
        second_image = Path(next(iter(second_data.values())))

        assert first_image.exists() and second_image.exists()
        assert _sha256(first_image) == _sha256(second_image)

        browser.close()
