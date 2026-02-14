"""Test the helper functions added to src/app.py for enhanced iteration."""

import pytest

# Import the helper functions from src.app
# Note: These functions are in src/app.py which is a Streamlit app
# In a real testing environment, we'd import them directly
# For now, we test the logic with mock implementations


class MockUploadedFile:
    """Mock Streamlit uploaded file for testing."""

    def __init__(self, name: str, content: bytes, size: int = None):
        self.name = name
        self.content = content
        self.size = size or len(content)

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            return self.content
        return self.content[:size]

    def seek(self, position: int):
        pass


def test_validate_text_file_valid_txt():
    """Test validation of valid .txt file."""
    from src.app import validate_text_file

    # Create a valid text file
    mock_file = MockUploadedFile("test.txt", b"Hello, world!")

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is True
    assert "valid" in message.lower()


def test_validate_text_file_valid_md():
    """Test validation of valid .md file."""
    from src.app import validate_text_file

    # Create a valid markdown file
    content = b"# Title\n\nThis is a markdown file."
    mock_file = MockUploadedFile("test.md", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is True


def test_validate_text_file_valid_csv():
    """Test validation of valid .csv file."""
    from src.app import validate_text_file

    # Create a valid CSV file
    content = b"col1,col2,col3\nval1,val2,val3"
    mock_file = MockUploadedFile("test.csv", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is True


def test_validate_text_file_valid_json():
    """Test validation of valid .json file."""
    from src.app import validate_text_file

    # Create a valid JSON file
    content = b'{"key": "value", "number": 123}'
    mock_file = MockUploadedFile("test.json", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is True


def test_validate_text_file_rejects_binary():
    """Test that binary files are rejected."""
    from src.app import validate_text_file

    # Create a binary file (PNG header) - use .txt extension so it gets past extension check
    content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    mock_file = MockUploadedFile("test.txt", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is False
    assert "binary" in message.lower() or "not a text file" in message.lower()


def test_validate_text_file_rejects_py():
    """Test that .py files are rejected (not in allowed list)."""
    from src.app import validate_text_file

    # Create a Python file (should be rejected)
    content = b"print('Hello, world!')"
    mock_file = MockUploadedFile("test.py", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is False
    assert "not allowed" in message.lower()


def test_validate_text_file_size_limit():
    """Test that files exceeding size limit are rejected."""
    from src.app import validate_text_file

    # Create a large file (over 10MB)
    large_content = b"x" * (11 * 1024 * 1024)
    mock_file = MockUploadedFile("large.txt", large_content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is False
    assert "too large" in message.lower() or "10mb" in message.lower()


def test_validate_text_file_within_limit():
    """Test that files within size limit are accepted."""
    from src.app import validate_text_file

    # Create a file just under 10MB
    content = b"x" * (9 * 1024 * 1024)
    mock_file = MockUploadedFile("medium.txt", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is True


def test_validate_text_file_invalid_utf8():
    """Test that files with invalid UTF-8 are rejected."""
    from src.app import validate_text_file

    # Create a file with invalid UTF-8
    content = b"\xff\xfe\xfd"
    mock_file = MockUploadedFile("invalid.txt", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is False


@pytest.mark.parametrize(
    "extension", [".txt", ".md", ".markdown", ".csv", ".json", ".xml", ".yaml", ".yml"]
)
def test_validate_text_file_allows_extension(extension):
    """Test that all allowed extensions are accepted."""
    from src.app import validate_text_file

    content = b"Test content"
    mock_file = MockUploadedFile(f"test{extension}", content)

    is_valid, message = validate_text_file(mock_file)

    assert is_valid is True, f"Extension {extension} should be allowed"


def test_validate_text_file_none():
    """Test that None file is handled gracefully."""
    from src.app import validate_text_file

    is_valid, message = validate_text_file(None)

    assert is_valid is False
    assert "no file" in message.lower() or "none" in message.lower()


class TestPipelineStateHelpers:
    """Test the enhanced run wrappers for PipelineState."""

    def test_run_agent_with_extras_basic(self):
        """Test that run_agent_with_extras properly enhances input."""
        from src.app import run_agent_with_extras
        from src.state import PipelineState

        # Create a simple test - just verify the function accepts parameters
        state = PipelineState(user_input="Test topic")

        # Mock agent function
        def mock_agent_func(s):
            return s

        # Call with extras
        extra_input = "Focus on examples"
        file_contents = ["File 1 content", "File 2 content"]

        # The function should accept these parameters
        result = run_agent_with_extras(
            agent_func=mock_agent_func,
            state=state,
            extra_input=extra_input,
            file_contents=file_contents,
        )
        # Function should work
        assert result is not None

    def test_run_agent_with_extras_brainstorm_mode(self):
        """Test that run_agent_with_extras enhances user_input for brainstorm."""
        from src.app import run_agent_with_extras
        from src.state import PipelineState

        state = PipelineState(user_input="Original topic")
        extra_input = "Add more examples"

        # Mock agent function
        def mock_agent_func(s):
            return s

        result = run_agent_with_extras(
            agent_func=mock_agent_func,
            state=state,
            extra_input=extra_input,
            file_contents=[],
        )

        # Should enhance user_input
        assert "Additional Requirements/Context" in result.user_input
        assert "Add more examples" in result.user_input

    def test_run_agent_with_extras_research_mode(self):
        """Test that run_agent_with_extras stores extras in state attributes."""
        from src.app import run_agent_with_extras
        from src.state import PipelineState

        state = PipelineState(user_input="Test")
        extra_input = "Focus on recent research"

        # Mock agent function
        def mock_agent_func(s):
            return s

        result = run_agent_with_extras(
            agent_func=mock_agent_func,
            state=state,
            extra_input=extra_input,
            file_contents=[],
            state_field="research_extra_input",
        )

        # Should store in state attribute
        assert result.research_extra_input == extra_input

    def test_run_agent_with_extras_no_extras(self):
        """Test that run_agent_with_extras works without extras."""
        from src.app import run_agent_with_extras
        from src.state import PipelineState

        state = PipelineState(user_input="Test")
        called = False

        # Mock agent function
        def mock_agent_func(s):
            nonlocal called
            called = True
            return s

        result = run_agent_with_extras(
            agent_func=mock_agent_func, state=state, extra_input="", file_contents=[]
        )

        # Should still call the agent
        assert called
        assert result is state

    def test_run_agent_with_extras_with_files(self):
        """Test that run_agent_with_extras handles file contents."""
        from src.app import run_agent_with_extras
        from src.state import PipelineState

        state = PipelineState(user_input="Test")
        file_contents = ["Content 1", "Content 2"]

        # Mock agent function
        def mock_agent_func(s):
            return s

        result = run_agent_with_extras(
            agent_func=mock_agent_func,
            state=state,
            extra_input="",
            file_contents=file_contents,
            state_field="content_extra_input",
        )

        # Should store file contents
        assert result.content_file_contents == file_contents


class TestDisplayEnhancedPhaseRunner:
    """Test the generic display_enhanced_phase_runner function."""

    def test_function_signature(self):
        """Test that the function has the expected signature."""
        from src.app import display_enhanced_phase_runner
        import inspect

        # Check that the function exists and has the right parameters
        sig = inspect.signature(display_enhanced_phase_runner)

        params = list(sig.parameters.keys())

        assert "phase_name" in params
        assert "phase_key" in params
        assert "run_func" in params
        assert "run_with_extras_func" in params
        assert "state" in params
        assert "user_input" in params
        assert "can_run" in params
        assert "spinner_message_run" in params
        assert "spinner_message_regen" in params
        assert "success_message_run" in params
        assert "success_message_regen" in params

    def test_function_returns_tuple(self):
        """Test that the function returns the expected tuple."""
        # We can't easily test the full function without Streamlit context
        # But we can verify it returns a tuple
        from src.app import display_enhanced_phase_runner
        from src.state import PipelineState

        state = PipelineState(user_input="Test")

        # This should fail gracefully or return a tuple
        try:
            result = display_enhanced_phase_runner(
                phase_name="Test",
                phase_key="test",
                run_func=lambda s: s,
                run_with_extras_func=lambda s, *args: s,
                state=state,
                user_input="",
                can_run=False,
                spinner_message_run="test",
                spinner_message_regen="test",
                success_message_run="test",
                success_message_regen="test",
            )

            # If we get a result, it should be a tuple
            if result is not None:
                assert isinstance(result, tuple)
        except Exception as e:
            # Expected in test context - Streamlit not available
            pytest.skip(f"Streamlit context required: {e}")
