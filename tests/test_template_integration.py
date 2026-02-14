"""Integration tests for template system with pptx_builder.

Tests:
- Template application to content
- pptx_builder with templates
- Content serialization
- File generation with templates
"""

from pathlib import Path
import tempfile

from src.tools.template_manager import TemplateManager
from src.tools.pptx_builder import build_presentation
from src.schemas import SlideContent


class TestTemplateApplication:
    """Test applying templates to content."""

    @staticmethod
    def create_sample_content():
        """Create sample slide content for testing."""
        return [
            SlideContent(
                title="Introduction to Climate Change",
                bullets=[
                    "Global temperature rising 1.1°C since pre-industrial times",
                    "Primary cause: greenhouse gas emissions",
                    "Impacts visible across all continents",
                ],
                speaker_notes="Introduce the topic and set context for the presentation.",
                citations=[],
            ),
            SlideContent(
                title="Agricultural Impacts",
                bullets=[
                    "Soil degradation and water scarcity",
                    "Changing precipitation patterns",
                    "Pest and disease outbreaks",
                    "Reduced crop yields in tropical regions",
                ],
                speaker_notes="Discuss specific impacts on farming communities.",
                citations=["IPCC 2021", "FAO Climate Report 2023"],
            ),
            SlideContent(
                title="Solutions and Adaptation",
                bullets=[
                    "Sustainable farming practices",
                    "Crop diversification strategies",
                    "Water management technologies",
                    "Community-based resilience programs",
                ],
                speaker_notes="Present practical solutions farmers can implement.",
                citations=["World Bank Agriculture Study"],
            ),
        ]

    @staticmethod
    def create_sample_references():
        """Create sample references for testing."""
        return [
            "IPCC, 2021: Sixth Assessment Report",
            "FAO Climate Report, 2023: Agricultural Adaptation",
            "World Bank Agriculture Study, 2022",
        ]

    @staticmethod
    def test_apply_template_default():
        """Test applying default template."""
        print("\n[TEST] Applying default template...")

        content = TestTemplateApplication.create_sample_content()
        references = TestTemplateApplication.create_sample_references()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_default.pptx"

            build_presentation(
                slides=content,
                references=references,
                output_path=output_path,
                template_name="default",
            )

            assert output_path.exists(), "File not created"
            file_size = output_path.stat().st_size / 1024
            print(f"  [OK] Generated with default template: {file_size:.1f} KB")

    @staticmethod
    def test_apply_template_professional():
        """Test applying professional template."""
        print("\n[TEST] Applying professional template...")

        content = TestTemplateApplication.create_sample_content()
        references = TestTemplateApplication.create_sample_references()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_professional.pptx"

            build_presentation(
                slides=content,
                references=references,
                output_path=output_path,
                template_name="professional",
            )

            assert output_path.exists(), "File not created"
            file_size = output_path.stat().st_size / 1024
            print(f"  [OK] Generated with professional template: {file_size:.1f} KB")

    @staticmethod
    def test_apply_template_academic():
        """Test applying academic template."""
        print("\n[TEST] Applying academic template...")

        content = TestTemplateApplication.create_sample_content()
        references = TestTemplateApplication.create_sample_references()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_academic.pptx"

            build_presentation(
                slides=content,
                references=references,
                output_path=output_path,
                template_name="academic",
            )

            assert output_path.exists(), "File not created"
            file_size = output_path.stat().st_size / 1024
            print(f"  [OK] Generated with academic template: {file_size:.1f} KB")

    @staticmethod
    def test_apply_all_templates():
        """Test applying all available templates."""
        print("\n[TEST] Applying all templates...")

        tm = TemplateManager()
        templates = tm.list_templates()
        content = TestTemplateApplication.create_sample_content()
        references = TestTemplateApplication.create_sample_references()

        results = {}
        for template_name in templates:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    output_path = Path(tmpdir) / f"test_{template_name}.pptx"

                    build_presentation(
                        slides=content,
                        references=references,
                        output_path=output_path,
                        template_name=template_name,
                    )

                    if output_path.exists():
                        file_size = output_path.stat().st_size / 1024
                        results[template_name] = f"OK ({file_size:.1f} KB)"
                        print(f"  [OK] {template_name}: {file_size:.1f} KB")
                    else:
                        results[template_name] = "FAIL (file not created)"
                        print(f"  [FAIL] {template_name}: file not created")

            except Exception as e:
                results[template_name] = f"ERROR ({str(e)[:50]})"
                print(f"  [ERROR] {template_name}: {e}")

        assert all(result.startswith("OK") for result in results.values()), results

    @staticmethod
    def test_generation_without_template():
        """Test that generation works without template (backward compat)."""
        print("\n[TEST] Generation without template (backward compatibility)...")

        content = TestTemplateApplication.create_sample_content()
        references = TestTemplateApplication.create_sample_references()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_no_template.pptx"

            build_presentation(
                slides=content,
                references=references,
                output_path=output_path,
                template_name=None,
            )

            assert output_path.exists(), "File not created"
            file_size = output_path.stat().st_size / 1024
            print(f"  [OK] Generated without template: {file_size:.1f} KB")

    @staticmethod
    def test_template_fallback_on_error():
        """Test that system falls back to default on template error."""
        print("\n[TEST] Template fallback on error...")

        content = TestTemplateApplication.create_sample_content()
        references = TestTemplateApplication.create_sample_references()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_fallback.pptx"

            # Try with non-existent template - should fall back to default
            build_presentation(
                slides=content,
                references=references,
                output_path=output_path,
                template_name="nonexistent_template",
            )

            # Should still create file (with default)
            assert output_path.exists(), "Fallback failed - no file created"
            file_size = output_path.stat().st_size / 1024
            print(f"  [OK] Fallback to default worked: {file_size:.1f} KB")


def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("TEMPLATE INTEGRATION TESTS")
    print("=" * 70)

    test = TestTemplateApplication()

    results = {
        "apply_default": test.test_apply_template_default(),
        "apply_professional": test.test_apply_template_professional(),
        "apply_academic": test.test_apply_template_academic(),
        "apply_all": test.test_apply_all_templates(),
        "no_template": test.test_generation_without_template(),
        "fallback": test.test_template_fallback_on_error(),
    }

    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)

    print(f"\nBasic Tests: {passed} passed, {failed} failed")
    print(f"Template Coverage: {len(results['apply_all'])} templates tested")

    print("\n" + "=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
