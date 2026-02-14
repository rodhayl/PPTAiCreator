"""Verification script for template system installation.

This script checks that all template system components are properly installed.

Usage:
    python scripts/verify_template_installation.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def verify_files():
    """Verify all required files exist."""
    print("[1/6] Verifying file structure...")

    required_files = {
        "Core System": [
            "src/tools/template_manager.py",
            "src/tools/pptx_builder.py",
            "src/agents/design.py",
            "src/state.py",
            "src/graph/build_graph.py",
        ],
        "GUI Components": [
            "src/app.py",
            "src/app_settings_helpers.py",
        ],
        "Scripts": [
            "scripts/create_default_templates.py",
            "scripts/verify_template_installation.py",
        ],
        "Documentation": [
            "README.md",
            "docs/README.md",
            "docs/guides/settings_guide.md",
            "docs/operations/production_readiness.md",
            "templates/README.md",
        ],
        "Templates": [
            "templates/default.pptx",
            "templates/professional.pptx",
            "templates/academic.pptx",
            "templates/creative.pptx",
            "templates/minimalist.pptx",
        ],
        "Directories": [
            "templates/",
            "templates/custom/",
        ],
    }

    all_good = True
    for category, files in required_files.items():
        print(f"\n  Checking {category}:")
        for file_path in files:
            path = REPO_ROOT / file_path
            if path.exists():
                print(f"    [OK] {file_path}")
            else:
                print(f"    [MISSING] {file_path}")
                all_good = False

    return all_good


def verify_imports():
    """Verify Python modules can be imported."""
    print("\n[2/6] Verifying Python imports...")

    imports_to_test = [
        ("src.tools.template_manager", "TemplateManager"),
        ("src.tools.pptx_builder", "build_presentation"),
        ("src.state", "PipelineState"),
        ("src.app", "tab_run_history"),
        ("src.app_settings_helpers", "_display_template_management"),
    ]

    all_good = True
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  [OK] {module_name}.{class_name}")
        except Exception as e:
            print(f"  [FAIL] {module_name}.{class_name}: {e}")
            all_good = False

    return all_good


def verify_templates():
    """Verify templates are valid."""
    print("\n[3/6] Verifying template files...")

    try:
        from src.tools.template_manager import TemplateManager

        tm = TemplateManager()
        templates = tm.list_templates()

        print(f"  Found {len(templates)} templates:")
        for template in templates:
            print(f"    • {template}")

        if not templates:
            print(
                "  [WARNING] No templates found. Run: python scripts/create_default_templates.py"
            )
            return False

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def verify_template_validation():
    """Verify template validation works."""
    print("\n[4/6] Verifying template validation...")

    try:
        from src.tools.template_manager import TemplateManager

        tm = TemplateManager()
        templates = tm.list_templates()

        if not templates:
            print("  [SKIP] No templates to validate")
            return False

        template = templates[0]
        print(f"  Testing template: {template}")

        prs = tm.load_template(template)
        valid, errors = tm.validate_template(prs)

        if valid:
            print("  [OK] Template validation passed")
            return True
        else:
            print(f"  [WARNING] Validation issues: {', '.join(errors)}")
            return True  # Warning, not failure
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def verify_state_field():
    """Verify PipelineState has template_name field."""
    print("\n[5/6] Verifying PipelineState template field...")

    try:
        from src.state import PipelineState

        state = PipelineState(user_input="test", template_name="test_template")

        if hasattr(state, "template_name"):
            print(f"  [OK] template_name field exists: {state.template_name}")
            return True
        else:
            print("  [FAIL] template_name field missing")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def verify_pipeline_parameter():
    """Verify run_pipeline accepts template_name."""
    print("\n[6/6] Verifying pipeline template parameter...")

    try:
        from src.graph.build_graph import run_pipeline
        import inspect

        sig = inspect.signature(run_pipeline)
        params = list(sig.parameters.keys())

        if "template_name" in params:
            print("  [OK] run_pipeline has template_name parameter")
            print(f"  [OK] Signature: {sig}")
            return True
        else:
            print("  [FAIL] template_name parameter missing")
            print(f"  Current params: {params}")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Template System Installation Verification")
    print("=" * 60)
    print()

    results = {
        "File Structure": verify_files(),
        "Python Imports": verify_imports(),
        "Templates Available": verify_templates(),
        "Template Validation": verify_template_validation(),
        "State Field": verify_state_field(),
        "Pipeline Parameter": verify_pipeline_parameter(),
    }

    print()
    print("=" * 60)
    print("Verification Summary")
    print("=" * 60)
    print()

    for check, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {check}")

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    print()
    print(f"Results: {passed_count}/{total_count} checks passed")

    if passed_count == total_count:
        print()
        print("[SUCCESS] Template system is fully installed and operational!")
        print()
        print("Next steps:")
        print("  1. Run: python -m pytest tests/test_template_integration.py -q")
        print("  2. Start GUI: start.bat or streamlit run src/app.py")
        print("  3. Navigate to Quick Generate and try a template!")
        print()
        return 0
    else:
        print()
        print("[WARNING] Some checks failed")
        print()
        print("Common fixes:")
        print("  - Missing templates: Run 'python scripts/create_default_templates.py'")
        print("  - Import errors: Check Python path and dependencies")
        print("  - File missing: Re-download or restore from backup")
        print()
        return 1


if __name__ == "__main__":
    exit(main())
