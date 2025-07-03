"""
Model router for selecting appropriate LLM based on command complexity
"""

import json
import logging
from typing import Dict, List, Any
from .bedrock_client import BedrockClient
from .prompt_templates import PromptTemplates

class ModelRouter:
    """Routes commands to appropriate LLM models based on complexity and context"""
    
    def __init__(self, bedrock_client: BedrockClient, config: Dict):
        self.bedrock_client = bedrock_client
        self.config = config
        self.prompt_templates = PromptTemplates()
        self.logger = logging.getLogger(__name__)
        
        # Command complexity scoring weights
        self.complexity_weights = {
            'file_operations': 1,
            'git_operations': 2,
            'process_management': 3,
            'code_analysis': 4,
            'multi_step': 6,
            'context_size': 2
        }
    
    async def select_model(self, command: str, context: Dict) -> Dict:
        """Select appropriate model based on command complexity"""
        
        complexity_score = self.analyze_complexity(command, context)
        
        if complexity_score < 3:
            model_name = "titan-text-lite"
        elif complexity_score < 7:
            model_name = "claude-3-haiku"
        else:
            model_name = "claude-3.5-sonnet"
        
        # Override with config default if specified
        if 'default_model' in self.config:
            default_model = self.config['default_model']
            if default_model in self.bedrock_client.list_available_models():
                model_name = default_model
        
        model_info = self.bedrock_client.get_model_info(model_name)
        estimated_cost = self.bedrock_client.estimate_cost(model_name, len(command))
        
        return {
            'model_name': model_name,
            'complexity_score': complexity_score,
            'estimated_cost': estimated_cost,
            **model_info
        }
    
    def analyze_complexity(self, command: str, context: Dict) -> int:
        """Analyze command complexity and return score"""
        
        score = 0
        command_lower = command.lower()
        
        # File operation complexity
        file_ops = ['list', 'copy', 'move', 'delete', 'organize', 'find']
        if any(op in command_lower for op in file_ops):
            score += self.complexity_weights['file_operations']
        
        # Git operation complexity
        git_ops = ['git', 'commit', 'branch', 'merge', 'push', 'pull']
        if any(op in command_lower for op in git_ops):
            score += self.complexity_weights['git_operations']
        
        # Process management complexity
        process_ops = ['process', 'kill', 'start', 'stop', 'monitor']
        if any(op in command_lower for op in process_ops):
            score += self.complexity_weights['process_management']
        
        # Code analysis complexity
        code_ops = ['analyze', 'refactor', 'debug', 'test', 'review']
        if any(op in command_lower for op in code_ops):
            score += self.complexity_weights['code_analysis']
        
        # Multi-step operation complexity
        multi_step_indicators = ['and', 'then', 'after', 'setup', 'configure', 'deploy']
        if any(indicator in command_lower for indicator in multi_step_indicators):
            score += self.complexity_weights['multi_step']
        
        # Context size complexity
        context_size = len(str(context))
        if context_size > 10000:  # Large context
            score += self.complexity_weights['context_size']
        
        return score
    
    async def process_command(self, command: str, context: Dict, model_info: Dict) -> Dict:
        """Process command using selected LLM model"""
        
        # Build system prompt with context
        system_prompt = self.prompt_templates.build_system_prompt(command, context)
        
        try:
            # Invoke the LLM
            response = await self.bedrock_client.invoke_model(
                model_name=model_info['model_name'],
                prompt=system_prompt,
                context=context
            )
            
            # Parse the LLM response
            parsed_response = self._parse_llm_response(response['content'])
            
            # Add metadata
            parsed_response.update({
                'model_used': model_info['model_name'],
                'usage': response.get('usage', {}),
                'latency_ms': response.get('latency_ms', 0)
            })
            
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"Error processing command with LLM: {e}")
            raise
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM response and extract command information"""
        
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text)
            
            # If not JSON, create a structured response
            lines = response_text.strip().split('\n')
            
            commands = []
            interpretation = ""
            explanation = ""
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('Commands:') or line.startswith('```bash'):
                    current_section = 'commands'
                    continue
                elif line.startswith('Interpretation:'):
                    current_section = 'interpretation'
                    interpretation = line.replace('Interpretation:', '').strip()
                    continue
                elif line.startswith('Explanation:'):
                    current_section = 'explanation'
                    explanation = line.replace('Explanation:', '').strip()
                    continue
                elif line.startswith('```'):
                    current_section = None
                    continue
                
                if current_section == 'commands' and line:
                    # Extract command from line
                    if line.startswith('$') or line.startswith('#'):
                        line = line[1:].strip()
                    if line:
                        commands.append({
                            'type': 'bash',
                            'command': line,
                            'description': f"Execute: {line}",
                            'safety_level': 'safe'
                        })
                elif current_section == 'interpretation':
                    interpretation += " " + line
                elif current_section == 'explanation':
                    explanation += " " + line
            
            return {
                'interpretation': interpretation or "Execute the requested command",
                'commands': commands,
                'explanation': explanation or "Command will be executed as requested",
                'risks': []
            }
            
        except json.JSONDecodeError:
            # Fallback: treat entire response as a single bash command
            return {
                'interpretation': "Execute user command",
                'commands': [{
                    'type': 'bash',
                    'command': response_text.strip(),
                    'description': "Execute user command",
                    'safety_level': 'safe'
                }],
                'explanation': "Executing user command as interpreted",
                'risks': []
            }
    
    def get_model_recommendation(self, command: str, context: Dict) -> str:
        """Get model recommendation without executing"""
        
        complexity_score = self.analyze_complexity(command, context)
        
        if complexity_score < 3:
            return "titan-text-lite (fast, cheap)"
        elif complexity_score < 7:
            return "claude-3-haiku (balanced)"
        else:
            return "claude-3.5-sonnet (advanced reasoning)"