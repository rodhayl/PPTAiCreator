from __future__ import annotations

import json
import os
from pathlib import Path

from src.graph.build_graph import run_pipeline


def main() -> None:
    topics = [
        "Modern Supply Chain Resilience Strategies for Global Operations",
        "Practical Zero Trust Security for Enterprise IT Teams",
        "Data Storytelling with Dashboards for Business Stakeholders",
        "Sustainable Urban Mobility Planning for Smart Cities",
        "AI Governance and Risk Management for Executive Leaders",
    ]

    os.environ.setdefault("MODEL_REQUEST_TIMEOUT_SECONDS", "180")

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    final_results: list[dict] = []

    for idx, topic in enumerate(topics, start=1):
        success_record: dict | None = None
        last_errors: list[str] = []

        for attempt in range(1, 3):
            state = run_pipeline(topic, educational_mode=False)
            path = state.pptx_path
            exists = bool(path and Path(path).exists())
            last_errors = state.errors or []

            if exists:
                success_record = {
                    "topic": topic,
                    "run_id": state.run_id,
                    "pptx_path": path,
                    "status": "ok",
                }
                break

        if success_record is None:
            success_record = {
                "topic": topic,
                "run_id": None,
                "pptx_path": None,
                "status": "failed",
                "errors": last_errors,
            }

        final_results.append(success_record)
        print(
            f"[{idx}/{len(topics)}] {success_record['status']} -> {success_record['pptx_path']}"
        )

    report = {
        "provider": "configured in ai_config.properties",
        "requested_topics": topics,
        "results": final_results,
    }

    report_path = artifacts_dir / "fresh_topic_set_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("REPORT:", report_path)


if __name__ == "__main__":
    main()
