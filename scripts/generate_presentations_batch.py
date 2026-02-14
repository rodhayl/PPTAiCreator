from src.graph.build_graph import run_pipeline
from pathlib import Path
import json


def main() -> None:
    topics = [
        "Benefits of Renewable Energy for Cities",
        "Cybersecurity Essentials for Small Businesses",
        "Introduction to Photosynthesis for Grade 9",
        "Project Management Fundamentals for New Teams",
        "AI in Healthcare: Opportunities and Risks",
    ]

    results = []
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)
    report_path = artifacts / "generation_batch_report.json"
    print("Using configured model from ai_config.properties...")

    for index, topic in enumerate(topics, start=1):
        try:
            state = run_pipeline(topic, educational_mode=(index % 2 == 1))
            qa = state.qa_report
            item = {
                "topic": topic,
                "run_id": state.run_id,
                "pptx_path": state.pptx_path,
                "content_score": qa.content_score if qa else None,
                "design_score": qa.design_score if qa else None,
                "coherence_score": qa.coherence_score if qa else None,
                "errors": state.errors,
                "status": "ok" if state.pptx_path else "no_artifact",
            }
        except Exception as exc:
            item = {
                "topic": topic,
                "run_id": None,
                "pptx_path": None,
                "content_score": None,
                "design_score": None,
                "coherence_score": None,
                "errors": [str(exc)],
                "status": "exception",
            }
        results.append(item)
        print(f"[{index}/{len(topics)}] {item['status']} -> {item['pptx_path']}")

    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("---RESULTS_JSON---")
    print(json.dumps(results, indent=2))
    print(f"---REPORT_PATH---\n{report_path}")


if __name__ == "__main__":
    main()
