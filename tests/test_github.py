from unittest.mock import Mock, patch

import pytest

from src.get_flows import get_file_paths, get_file_versions, save_versions


@pytest.fixture
def mock_github_api():
    mock_api = Mock()
    mock_api.repos.get_commit.return_value = Mock(
        files=[
            Mock(
                filename='contact-flows/flow1.json',
                status='modified'
            )
        ],
        parents=[Mock(sha='parent_sha')]
    )
    return mock_api

def test_get_file_paths(mock_github_api):
    with patch('src.get_flows.GhApi', return_value=mock_github_api):
        paths = get_file_paths(
            token='test-token',
            owner='test-owner',
            repo='test-repo',
            commit_sha='test-sha',
            contact_flow_path='contact-flows'
        )
        
        assert len(paths) == 1
        assert paths[0] == 'contact-flows/flow1.json'

def test_get_file_versions(mock_github_api):
    mock_content = Mock(content='eyJ0ZXN0IjogInZhbHVlIn0=')  # Base64 encoded {"test": "value"}
    mock_github_api.repos.get_content.return_value = mock_content
    
    with patch('src.get_flows.GhApi', return_value=mock_github_api):
        original, modified = get_file_versions(
            token='test-token',
            owner='test-owner',
            repo='test-repo',
            commit_sha='test-sha',
            file_path='test-path'
        )
        
        assert original == '{"test": "value"}'
        assert modified == '{"test": "value"}'

def test_get_file_versions_new_file(mock_github_api):
    class NotFoundError(Exception):
        status = 404

    mock_github_api.repos.get_content.side_effect = [
        NotFoundError(),  # Original file not found
        Mock(content='eyJ0ZXN0IjogInZhbHVlIn0=')  # Modified file exists
    ]
    
    with patch('src.get_flows.GhApi', return_value=mock_github_api):
        original, modified = get_file_versions(
            token='test-token',
            owner='test-owner',
            repo='test-repo',
            commit_sha='test-sha',
            file_path='test-path'
        )
        
        assert original == "{}"
        assert modified == '{"test": "value"}'

def test_save_versions(tmp_path):
    original_path = tmp_path / "original.json"
    modified_path = tmp_path / "modified.json"
    
    save_versions(
        original='{"test": "original"}',
        modified='{"test": "modified"}',
        original_path=str(original_path),
        modified_path=str(modified_path)
    )
    
    assert original_path.read_text() == '{"test": "original"}'
    assert modified_path.read_text() == '{"test": "modified"}'

def test_save_versions_error():
    with pytest.raises(OSError) as exc_info:  # Use specific exception type
        save_versions(
            original='test',
            modified='test',
            original_path='/nonexistent/path/original.json',
            modified_path='/nonexistent/path/modified.json'
        )
    assert "No such file or directory" in str(exc_info.value)
