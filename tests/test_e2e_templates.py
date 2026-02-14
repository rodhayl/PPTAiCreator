"""End-to-end tests for template system with real AI generation.

These tests use the actual Ollama AI service to generate complete presentations
with different templates. This verifies the full pipeline works correctly.

Requirements:
- Ollama running at http://localhost:11434
- Model gpt-oss:20b-cloud available
- ai_config.properties configured for Ollama

Run with:
    python -m pytest tests/test_e2e_templates.py -v -s
Or directly:
    python tests/test_e2e_templates.py
"""

import json
import time
from pathlib import Path
from datetime import datetime

from src.graph.build_graph import run_pipeline
from src.models.ai_interface import get_ai_interface


class TestE2ETemplateGeneration:
    """End-to-end tests for template generation."""

    @staticmethod
    def verify_ollama_connection():
        """Verify Ollama is running and accessible."""
        print("\n[SETUP] Verifying Ollama connection...")
        try:
            ai = get_ai_interface()
            success, message = ai.test_connection(agent="content")
            if success:
                print(f"  [OK] Ollama connection successful: {message}")
                return True
            else:
                print(f"  [FAIL] Ollama connection failed: {message}")
                return False
        except Exception as e:
            print(f"  [FAIL] Error testing connection: {e}")
            return False

    @staticmethod
    def _run_scenario(topic: str, template: str, scenario_name: str):
        """Run a single test scenario (helper method, not a pytest test).

        Args:
            topic: Presentation topic
            template: Template name to use
            scenario_name: Name for logging

        Returns:
            Dict with results
        """
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario_name}")
        print(f"{'='*70}")
        print(f"Topic: {topic}")
        print(f"Template: {template}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        result = {
            "scenario": scenario_name,
            "topic": topic,
            "template": template,
            "start_time": datetime.now().isoformat(),
            "status": "FAILED",
            "message": "",
            "duration": 0,
            "pptx_path": None,
            "slides_count": 0,
        }

        try:
            print("\n[PHASE 1/2] Generating presentation with AI...")
            start = time.time()

            # Run full pipeline with template
            state = run_pipeline(topic, educational_mode=False, template_name=template)

            generation_time = time.time() - start

            # Check for errors
            if state.errors:
                print("  [WARNING] Pipeline had errors:")
                for error in state.errors:
                    print(f"    - {error}")
                result["message"] = "; ".join(state.errors)
                result["status"] = "PARTIAL"
            else:
                print("  [OK] Pipeline completed successfully")
                result["status"] = "SUCCESS"

            # Verify output
            print("\n[PHASE 2/2] Verifying output...")
            if state.pptx_path and Path(state.pptx_path).exists():
                pptx_file = Path(state.pptx_path)
                file_size = pptx_file.stat().st_size / 1024

                print(f"  [OK] PPTX created: {pptx_file.name}")
                print(f"  [OK] File size: {file_size:.1f} KB")

                if state.content:
                    slides_count = len(state.content)
                    print(f"  [OK] Generated {slides_count} slides")
                    result["slides_count"] = slides_count
                    result["pptx_path"] = state.pptx_path

                if state.qa_report:
                    print("  [OK] QA Report:")
                    print(
                        f"    - Content Score: {state.qa_report.content_score:.1f}/5.0"
                    )
                    print(f"    - Design Score: {state.qa_report.design_score:.1f}/5.0")
                    print(
                        f"    - Coherence Score: {state.qa_report.coherence_score:.1f}/5.0"
                    )
                    result["qa_scores"] = {
                        "content": state.qa_report.content_score,
                        "design": state.qa_report.design_score,
                        "coherence": state.qa_report.coherence_score,
                    }
                else:
                    print("  [WARNING] No QA report generated")

            else:
                result["message"] = "PPTX file not created"
                print("  [FAIL] PPTX file not created")

            result["duration"] = generation_time
            print(f"\n[RESULT] Generation took {generation_time:.1f} seconds")

        except Exception as e:
            result["message"] = str(e)
            result["status"] = "FAILED"
            print(f"  [FAIL] Exception: {e}")
            import traceback

            traceback.print_exc()

        result["end_time"] = datetime.now().isoformat()
        return result

    @staticmethod
    def run_all_scenarios():
        """Run all test scenarios."""
        print("\n" + "=" * 70)
        print("END-TO-END TEMPLATE SYSTEM TEST")
        print("=" * 70)

        # Verify connection first
        if not TestE2ETemplateGeneration.verify_ollama_connection():
            print("\n[ERROR] Cannot proceed without Ollama connection")
            return []

        # Define test scenarios
        scenarios = [
            {
                "name": "Scenario 1: Climate Change (Professional)",
                "topic": "Climate Change Impacts on Agriculture: Challenges and Solutions for Farmers in Developing Nations",
                "template": "professional",
            },
            {
                "name": "Scenario 2: AI/ML Basics (Academic)",
                "topic": "Introduction to Machine Learning: Algorithms, Applications, and Ethical Considerations in Modern Society",
                "template": "academic",
            },
            {
                "name": "Scenario 3: Startup Pitch (Creative)",
                "topic": "Revolutionary Sustainable Technology: How Our Solution Disrupts the Clean Energy Market",
                "template": "creative",
            },
            {
                "name": "Scenario 4: Minimal Tech Talk (Minimalist)",
                "topic": "Quantum Computing Fundamentals: Qubits, Superposition, and Real-World Applications",
                "template": "minimalist",
            },
            {
                "name": "Scenario 5: Default Template (Default)",
                "topic": "The Future of Remote Work: Trends, Technologies, and Best Practices for Global Teams",
                "template": "default",
            },
        ]

        results = []
        for scenario in scenarios:
            result = TestE2ETemplateGeneration._run_scenario(
                topic=scenario["topic"],
                template=scenario["template"],
                scenario_name=scenario["name"],
            )
            results.append(result)

        return results

    @staticmethod
    def save_results(results: list):
        """Save test results to JSON file."""
        results_path = Path("test_results_e2e.json")

        with open(results_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n[OK] Results saved to: {results_path}")

    @staticmethod
    def print_summary(results: list):
        """Print summary of all test results."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        successful = sum(1 for r in results if r["status"] == "SUCCESS")
        partial = sum(1 for r in results if r["status"] == "PARTIAL")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        total = len(results)

        print(f"\nTotal Scenarios: {total}")
        print(f"  Successful: {successful}")
        print(f"  Partial: {partial}")
        print(f"  Failed: {failed}")

        print("\nResults by Scenario:")
        for result in results:
            status_icon = (
                "[OK]"
                if result["status"] == "SUCCESS"
                else "[WARN]" if result["status"] == "PARTIAL" else "[FAIL]"
            )
            print(f"  {status_icon} {result['scenario']}")
            if result["slides_count"]:
                print(
                    f"    Slides: {result['slides_count']}, Duration: {result['duration']:.1f}s"
                )
            if result["qa_scores"]:
                scores = result["qa_scores"]
                avg = (scores["content"] + scores["design"] + scores["coherence"]) / 3
                print(
                    f"    QA: Content={scores['content']:.1f}, Design={scores['design']:.1f}, Coherence={scores['coherence']:.1f}, Avg={avg:.1f}"
                )
            if result["message"]:
                print(f"    Message: {result['message']}")

        print(f"\n{'='*70}")
        success_rate = (successful + partial) / total * 100 if total > 0 else 0
        print(f"Success Rate: {success_rate:.1f}% ({successful + partial}/{total})")
        print(f"{'='*70}")

        return {
            "total": total,
            "successful": successful,
            "partial": partial,
            "failed": failed,
            "success_rate": success_rate,
        }


def main():
    """Run all E2E tests."""
    print("\nStarting E2E Template System Tests...")

    # Run scenarios
    results = TestE2ETemplateGeneration.run_all_scenarios()

    # Save results
    TestE2ETemplateGeneration.save_results(results)

    # Print summary
    summary = TestE2ETemplateGeneration.print_summary(results)

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
