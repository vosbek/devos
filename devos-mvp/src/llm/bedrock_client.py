"""
AWS Bedrock client for LLM integration
"""

import json
import boto3
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
import logging
import time

class BedrockClient:
    """AWS Bedrock client for LLM model access"""
    
    def __init__(self, region: str, access_key: str, secret_key: str):
        self.region = region
        self.logger = logging.getLogger(__name__)
        
        # Initialize Bedrock client
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Model configurations
        self.models = {
            'titan-text-lite': {
                'model_id': 'amazon.titan-text-lite-v1',
                'max_tokens': 512,
                'cost_per_1k_tokens': 0.0003
            },
            'claude-3-haiku': {
                'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
                'max_tokens': 2048,
                'cost_per_1k_tokens': 0.0015
            },
            'claude-3.5-sonnet': {
                'model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'max_tokens': 4096,
                'cost_per_1k_tokens': 0.015
            }
        }
    
    async def invoke_model(self, model_name: str, prompt: str, context: Dict) -> Dict:
        """Invoke a Bedrock model with the given prompt"""
        
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_config = self.models[model_name]
        start_time = time.time()
        
        try:
            if model_name.startswith('claude'):
                response = await self._invoke_claude(model_config, prompt, context)
            elif model_name.startswith('titan'):
                response = await self._invoke_titan(model_config, prompt, context)
            else:
                raise ValueError(f"Unsupported model type: {model_name}")
            
            # Add timing information
            response['latency_ms'] = (time.time() - start_time) * 1000
            
            return response
            
        except ClientError as e:
            self.logger.error(f"AWS Bedrock error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Model invocation error: {e}")
            raise
    
    async def _invoke_claude(self, model_config: Dict, prompt: str, context: Dict) -> Dict:
        """Invoke Claude model through Bedrock"""
        
        # Construct Claude-specific request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": model_config['max_tokens'],
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "top_p": 0.9
        }
        
        response = self.bedrock.invoke_model(
            modelId=model_config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'content': response_body['content'][0]['text'],
            'usage': response_body.get('usage', {}),
            'model_id': model_config['model_id']
        }
    
    async def _invoke_titan(self, model_config: Dict, prompt: str, context: Dict) -> Dict:
        """Invoke Titan model through Bedrock"""
        
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": model_config['max_tokens'],
                "temperature": 0.1,
                "topP": 0.9,
                "stopSequences": ["```"]
            }
        }
        
        response = self.bedrock.invoke_model(
            modelId=model_config['model_id'],
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'content': response_body['results'][0]['outputText'],
            'usage': {
                'input_tokens': response_body.get('inputTextTokenCount', 0),
                'output_tokens': response_body.get('outputTextTokenCount', 0),
                'total_tokens': response_body.get('inputTextTokenCount', 0) + response_body.get('outputTextTokenCount', 0)
            },
            'model_id': model_config['model_id']
        }
    
    def estimate_cost(self, model_name: str, prompt_length: int) -> float:
        """Estimate the cost of a model invocation"""
        
        if model_name not in self.models:
            return 0.0
        
        # Rough estimation: prompt + expected response
        estimated_tokens = prompt_length + 500
        cost_per_1k = self.models[model_name]['cost_per_1k_tokens']
        
        return (estimated_tokens / 1000) * cost_per_1k
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get model configuration information"""
        
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        return self.models[model_name].copy()
    
    def list_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())