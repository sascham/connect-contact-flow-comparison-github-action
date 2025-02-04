import time
from unittest.mock import Mock

from botocore.exceptions import ClientError

from src.bedrock_utils import BedrockMetricsCollector, TokenRateLimiter, invoke_bedrock_with_retries


def test_token_rate_limiter():
    limiter = TokenRateLimiter(tokens_per_minute=100)
    start_time = time.time()
    limiter.wait_for_tokens(50)
    limiter.wait_for_tokens(60)  # Should trigger wait
    elapsed = time.time() - start_time
    assert elapsed >= 60  # Verify wait occurred

def test_bedrock_metrics_collector():
    collector = BedrockMetricsCollector()
    test_metadata = {
        'RequestId': 'test-id',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-bedrock-invocation-latency': '100',
            'x-amzn-bedrock-input-token-count': '50', 
            'x-amzn-bedrock-output-token-count': '75',
            'date': '2024-01-01'
        },
        'RetryAttempts': 1
    }
    collector.add_metric(test_metadata)
    summary = collector.get_summary()
    assert summary['total_api_calls'] == 1
    assert summary['average_latency_ms'] == 100
    assert summary['total_input_tokens'] == 50

def test_invoke_bedrock_with_retries():
    mock_bedrock = Mock()
    mock_bedrock.invoke_model.side_effect = [
        ClientError({'Error': {'Code': 'ThrottlingException'}}, 'operation'),
        {'body': 'success'}
    ]
    result = invoke_bedrock_with_retries(
        mock_bedrock, 
        '123456789012',
        {'test': 'request'},
        max_retries=2
    )
    assert result == {'body': 'success'}
    assert mock_bedrock.invoke_model.call_count == 2
