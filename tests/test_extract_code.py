
from src.get_flows import extract_code_simple


def test_extract_code_simple_with_valid_blocks():
    response = """
    Here's some text
    ```python
    def test():
        pass
    ```
    More text
    ```json
    {"key": "value"}
    ```
    """
    result = extract_code_simple(response)
    assert len(result) == 2
    assert "def test():" in result[0]
    assert '{"key": "value"}' in result[1]

def test_extract_code_simple_with_no_blocks():
    response = "Plain text without code blocks"
    result = extract_code_simple(response)
    assert result == []

def test_extract_code_simple_with_empty_blocks():
    response = "```\n```"
    result = extract_code_simple(response)
    assert result == ['']
    
    
