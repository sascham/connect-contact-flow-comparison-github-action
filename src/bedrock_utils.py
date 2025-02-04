import json
import logging
import random
import time
from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TokenRateLimiter:
    """Rate limiter for Bedrock API token usage.
    
    Implements a sliding window rate limiting algorithm to ensure
    API token usage stays within specified limits.
    
    Args:
        tokens_per_minute (int): Maximum tokens allowed per minute
        
    Example:
        >>> limiter = TokenRateLimiter(400000)
        >>> limiter.wait_for_tokens(1000)
    """
    def __init__(self, tokens_per_minute=400000):
        self.tokens_per_minute = tokens_per_minute
        self.tokens_per_second = tokens_per_minute / 60
        self.last_request_time = 0
        self.used_tokens = 0
        self.window_start_time = time.time()

    def wait_for_tokens(self, tokens_needed):
        current_time = time.time()
        
        # Reset window if a minute has passed
        if current_time - self.window_start_time >= 60:
            self.used_tokens = 0
            self.window_start_time = current_time

        # Check if we would exceed the rate limit
        if self.used_tokens + tokens_needed > self.tokens_per_minute:
            sleep_time = 60 - (current_time - self.window_start_time)
            time.sleep(max(0, sleep_time))
            self.used_tokens = 0
            self.window_start_time = time.time()

        self.used_tokens += tokens_needed

@dataclass
class BedrockMetric:
    request_id: str
    http_status: int
    latency_ms: int
    input_tokens: int
    output_tokens: int
    retry_attempts: int
    timestamp: str
    
class BedrockMetricsCollector:
    """Collects and analyzes Bedrock API usage metrics.
    
    Tracks API calls, latency, token usage and generates
    reports and visualizations.
    
    Methods:
        add_metric: Add single API call metrics
        get_summary: Generate statistical summary
        save_metrics: Save metrics to JSON
        generate_html_report: Create HTML visualization
    """
    def __init__(self):
        self.metrics = []
        
    def add_metric(self, response_metadata):
        """Add a single API call metadata to metrics collection"""
        headers = response_metadata['HTTPHeaders']
        metric = {
            'request_id': response_metadata['RequestId'],
            'http_status': response_metadata['HTTPStatusCode'],
            'latency_ms': int(headers.get('x-amzn-bedrock-invocation-latency', 0)),
            'input_tokens': int(headers.get('x-amzn-bedrock-input-token-count', 0)),
            'output_tokens': int(headers.get('x-amzn-bedrock-output-token-count', 0)),
            'retry_attempts': response_metadata['RetryAttempts'],
            'timestamp': headers.get('date')
        }
        self.metrics.append(metric)
        
    def get_summary(self):
        """Generate summary statistics from collected metrics"""
        if not self.metrics:
            return "No metrics collected"
            
        total_calls = len(self.metrics)
        total_latency = sum(m['latency_ms'] for m in self.metrics)
        total_input_tokens = sum(m['input_tokens'] for m in self.metrics)
        total_output_tokens = sum(m['output_tokens'] for m in self.metrics)
        total_retries = sum(m['retry_attempts'] for m in self.metrics)
        
        summary = {
            'total_api_calls': total_calls,
            'average_latency_ms': total_latency / total_calls,
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'average_input_tokens': total_input_tokens / total_calls,
            'average_output_tokens': total_output_tokens / total_calls,
            'total_retry_attempts': total_retries,
            'success_rate': sum(1 for m in self.metrics if m['http_status'] == 200) / total_calls * 100
        }
        
        return summary
    
    def save_metrics(self, filename='bedrock_metrics.json'):
        """Save detailed metrics to a JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'detailed_metrics': self.metrics,
                'summary': self.get_summary()
            }, f, indent=2)
            
    def generate_html_report(self, filename='bedrock_metrics.html'):
        """Generate an HTML report with metrics visualization"""
        summary = self.get_summary()
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bedrock API Metrics Report</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metrics-container {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                .metric-card {{ 
                    background: #f5f5f5; 
                    padding: 15px; 
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .chart-container {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h1>Bedrock API Metrics Summary</h1>
            
            <div class="metrics-container">
                <div class="metric-card">
                    <h3>General Statistics</h3>
                    <p>Total API Calls: {summary['total_api_calls']}</p>
                    <p>Success Rate: {summary['success_rate']:.2f}%</p>
                    <p>Total Retry Attempts: {summary['total_retry_attempts']}</p>
                </div>
                
                <div class="metric-card">
                    <h3>Latency</h3>
                    <p>Average Latency: {summary['average_latency_ms']:.2f}ms</p>
                </div>
                
                <div class="metric-card">
                    <h3>Token Usage</h3>
                    <p>Total Input Tokens: {summary['total_input_tokens']}</p>
                    <p>Total Output Tokens: {summary['total_output_tokens']}</p>
                    <p>Average Input Tokens: {summary['average_input_tokens']:.2f}</p>
                    <p>Average Output Tokens: {summary['average_output_tokens']:.2f}</p>
                </div>
            </div>
            
            <div class="chart-container">
                <canvas id="latencyChart"></canvas>
            </div>
            
            <script>
                const latencies = {[m['latency_ms'] for m in self.metrics]};
                const requestIds = {[m['request_id'] for m in self.metrics]};
                
                new Chart(document.getElementById('latencyChart'), {{
                    type: 'line',
                    data: {{
                        labels: requestIds,
                        datasets: [{{
                            label: 'Latency (ms)',
                            data: latencies,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'API Call Latencies'
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)

def get_aws_clients():
    """Initialize and return AWS clients"""
    botoConfig = Config(
        region_name = 'us-east-1',
        retries = {
            'max_attempts': 10,
            'mode': 'adaptive'
        }
    )
    
    bedrock_runtime = boto3.client('bedrock-runtime', config=botoConfig)
    sts_client = boto3.client('sts')
    response = sts_client.get_caller_identity()
    account_id = response["Account"]
    
    return bedrock_runtime, account_id

def invoke_bedrock_with_retries(bedrock_runtime, account_id, request, max_retries=10, rate_limiter=None):
    """Invoke Bedrock with retries and exponential backoff"""
    base_delay = 1  # Start with 1 second delay
    
    # Estimate tokens in request (rough estimation)
    estimated_tokens = len(str(request)) / 4  # Rough estimation of tokens
    
    for attempt in range(max_retries):
        try:
            if rate_limiter:
                rate_limiter.wait_for_tokens(estimated_tokens)
                
            response = bedrock_runtime.invoke_model(
                modelId=f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                body=json.dumps(request)
            )
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries - 1:
                    raise  # Re-raise the exception if we're out of retries
                    
                # Calculate delay with exponential backoff and jitter
                delay = (base_delay * (2 ** attempt)) + (random.random() * 0.1)
                time.sleep(delay)
                continue
            else:
                raise
            

       
