from pathlib import Path
import json
import os

from src.graph.build_graph import run_pipeline


def main() -> None:
    topics = [
        "Digital Transformation Roadmap for Mid-Sized Companies",
        "Fundamentals of Data Visualization for Analysts",
        "Zero Trust Security Architecture Overview",
        "Customer Journey Mapping Best Practices",
    ]

    os.environ.setdefault("MODEL_REQUEST_TIMEOUT_SECONDS", "180")

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    results: list[dict] = []

    for topic in topics:
        success = None
        for attempt in range(1, 3):
            state = run_pipeline(topic, educational_mode=False)
            pptx_path = state.pptx_path
            pptx_exists = bool(pptx_path and Path(pptx_path).exists())

            record = {
                "topic": topic,
                "attempt": attempt,
                "run_id": state.run_id,
                "pptx_path": pptx_path,
                "pptx_exists": pptx_exists,
                "errors": state.errors,
            }
            results.append(record)

            if pptx_exists:
                success = record
                break

        if success is None:
            continue

    report = {
        "configured_provider": "from ai_config.properties",
        "success_count": sum(1 for item in results if item["pptx_exists"]),
        "results": results,
    }

    report_path = artifacts_dir / "several_presentations_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(str(report_path))


if __name__ == "__main__":
    main()
