#!/usr/bin/env python3
"""
Inter-Agent Coordinator
Manages communication and coordination between multiple agents
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json

from database.mongodb_manager import mongodb_manager

class InterAgentCoordinator:
    """Coordinates communication between multiple agents."""
    
    def __init__(self):
        self.logger = logging.getLogger("inter_agent_coordinator")
        self.mongodb = mongodb_manager
        
        # Agent registry
        self.registered_agents = {}
        self.agent_capabilities = {}
        
        # Workflow patterns for multi-agent tasks
        self.workflow_patterns = {
            'weather_email': {
                'description': 'Check weather and send email based on conditions',
                'agents': ['weather_agent', 'email_agent'],
                'flow': 'sequential'
            },
            'ocr_document_analysis': {
                'description': 'Extract text from image and analyze document',
                'agents': ['image_ocr_agent', 'document_agent'],
                'flow': 'sequential'
            },
            'math_email_report': {
                'description': 'Calculate values and email results',
                'agents': ['math_agent', 'email_agent'],
                'flow': 'sequential'
            },
            'document_summary_email': {
                'description': 'Analyze document and email summary',
                'agents': ['document_agent', 'email_agent'],
                'flow': 'sequential'
            }
        }
        
        self.logger.info("Inter-Agent Coordinator initialized")
    
    async def register_agent(self, agent_id: str, agent_instance: Any, 
                           capabilities: List[str]) -> bool:
        """Register an agent with the coordinator."""
        try:
            self.registered_agents[agent_id] = agent_instance
            self.agent_capabilities[agent_id] = capabilities
            
            self.logger.info(f"Registered agent: {agent_id} with capabilities: {capabilities}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent {agent_id}: {e}")
            return False
    
    async def coordinate_multi_agent_task(self, task_description: str, 
                                        user_id: str, session_id: str,
                                        context: Dict = None) -> Dict[str, Any]:
        """Coordinate a task that requires multiple agents."""
        try:
            self.logger.info(f"Coordinating multi-agent task: {task_description}")
            
            # Identify workflow pattern
            workflow = self._identify_workflow_pattern(task_description)
            
            if not workflow:
                return await self._handle_single_agent_task(task_description, user_id, session_id)
            
            # Execute workflow
            result = await self._execute_workflow(workflow, task_description, user_id, session_id, context)
            
            # Log the coordination
            await self._log_coordination(task_description, workflow, result, user_id, session_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error coordinating multi-agent task: {e}")
            return {
                "status": "error",
                "message": f"Error coordinating agents: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _identify_workflow_pattern(self, task_description: str) -> Optional[Dict]:
        """Identify which workflow pattern matches the task."""
        task_lower = task_description.lower()
        
        # Weather + Email patterns
        if any(weather_word in task_lower for weather_word in ['weather', 'rain', 'sunny', 'storm']) and \
           any(email_word in task_lower for email_word in ['email', 'send', 'notify', 'alert']):
            return self.workflow_patterns['weather_email']
        
        # OCR + Document analysis
        if any(ocr_word in task_lower for ocr_word in ['extract text', 'read image', 'ocr']) and \
           any(doc_word in task_lower for doc_word in ['analyze', 'summarize', 'document']):
            return self.workflow_patterns['ocr_document_analysis']
        
        # Math + Email
        if any(math_word in task_lower for math_word in ['calculate', 'math', 'percentage']) and \
           any(email_word in task_lower for email_word in ['email', 'send', 'report']):
            return self.workflow_patterns['math_email_report']
        
        # Document + Email
        if any(doc_word in task_lower for doc_word in ['document', 'pdf', 'analyze']) and \
           any(email_word in task_lower for email_word in ['email', 'send', 'summary']):
            return self.workflow_patterns['document_summary_email']
        
        return None
    
    async def _execute_workflow(self, workflow: Dict, task_description: str,
                              user_id: str, session_id: str, context: Dict = None) -> Dict[str, Any]:
        """Execute a multi-agent workflow."""
        try:
            workflow_results = []
            current_context = context or {}
            
            self.logger.info(f"Executing workflow: {workflow['description']}")
            
            if workflow['flow'] == 'sequential':
                # Execute agents in sequence, passing results between them
                for i, agent_id in enumerate(workflow['agents']):
                    self.logger.info(f"Executing agent {i+1}/{len(workflow['agents'])}: {agent_id}")
                    
                    # Prepare input for this agent
                    agent_input = self._prepare_agent_input(
                        agent_id, task_description, current_context, workflow_results
                    )
                    
                    # Execute agent
                    agent_result = await self._execute_agent(agent_id, agent_input, user_id, session_id)
                    
                    # Store result and update context
                    workflow_results.append({
                        "agent_id": agent_id,
                        "result": agent_result,
                        "step": i + 1
                    })
                    
                    # Update context with this agent's output
                    current_context.update(self._extract_context_from_result(agent_result))
                    
                    # If any agent fails, stop the workflow
                    if agent_result.get("status") != "success":
                        return {
                            "status": "error",
                            "message": f"Workflow failed at step {i+1} ({agent_id}): {agent_result.get('message', 'Unknown error')}",
                            "workflow_results": workflow_results,
                            "timestamp": datetime.utcnow().isoformat()
                        }
            
            # Combine results into final response
            final_response = self._combine_workflow_results(workflow, workflow_results, task_description)
            
            return {
                "status": "success",
                "message": final_response,
                "workflow": workflow['description'],
                "agents_used": workflow['agents'],
                "workflow_results": workflow_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            return {
                "status": "error",
                "message": f"Workflow execution failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _prepare_agent_input(self, agent_id: str, original_task: str, 
                           context: Dict, previous_results: List[Dict]) -> str:
        """Prepare input for a specific agent based on context and previous results."""
        
        if agent_id == 'weather_agent':
            # Extract location from original task or context
            return self._extract_weather_query(original_task, context)
        
        elif agent_id == 'email_agent':
            # Prepare email based on previous results
            return self._prepare_email_content(original_task, context, previous_results)
        
        elif agent_id == 'math_agent':
            # Extract mathematical query
            return self._extract_math_query(original_task, context)
        
        elif agent_id == 'image_ocr_agent':
            # Extract image processing request
            return self._extract_ocr_query(original_task, context)
        
        elif agent_id == 'document_agent':
            # Prepare document analysis request
            return self._prepare_document_query(original_task, context, previous_results)
        
        else:
            return original_task
    
    def _extract_weather_query(self, task: str, context: Dict) -> str:
        """Extract weather-related query from task."""
        # Simple extraction - in production, use more sophisticated NLP
        import re
        
        # Look for city names or location indicators
        city_match = re.search(r'in (\w+)', task.lower())
        if city_match:
            return f"What is the weather in {city_match.group(1)}?"
        
        return "What is the current weather?"
    
    def _prepare_email_content(self, task: str, context: Dict, previous_results: List[Dict]) -> str:
        """Prepare email content based on previous agent results."""
        import re
        
        # Extract email address
        email_match = re.search(r'(\S+@\S+\.\S+)', task)
        email_address = email_match.group(1) if email_match else "unknown@example.com"
        
        # Get content from previous results
        content_parts = []
        for result in previous_results:
            agent_result = result.get("result", {})
            if agent_result.get("status") == "success":
                message = agent_result.get("message", "")
                content_parts.append(f"{result['agent_id']}: {message}")
        
        combined_content = "\n".join(content_parts)
        
        return f"Send email to {email_address} with content: {combined_content}"
    
    def _extract_math_query(self, task: str, context: Dict) -> str:
        """Extract mathematical query from task."""
        # Look for mathematical expressions or keywords
        import re
        
        math_patterns = [
            r'calculate .*',
            r'what is \d+.*',
            r'\d+\s*[+\-*/]\s*\d+',
            r'\d+%\s*of\s*\d+'
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, task.lower())
            if match:
                return match.group(0)
        
        return task
    
    def _extract_ocr_query(self, task: str, context: Dict) -> str:
        """Extract OCR-related query from task."""
        # Look for image file references or OCR keywords
        if 'image' in task.lower() or 'extract text' in task.lower():
            return task
        
        return "Extract text from the provided image"
    
    def _prepare_document_query(self, task: str, context: Dict, previous_results: List[Dict]) -> str:
        """Prepare document analysis query."""
        # If we have OCR results, use them for document analysis
        for result in previous_results:
            if result['agent_id'] == 'image_ocr_agent':
                ocr_result = result.get("result", {})
                if ocr_result.get("extracted_text"):
                    return f"Analyze this text: {ocr_result['extracted_text']}"
        
        return task
    
    def _extract_context_from_result(self, agent_result: Dict) -> Dict:
        """Extract useful context from agent result for next agents."""
        context = {}
        
        if agent_result.get("extracted_text"):
            context["extracted_text"] = agent_result["extracted_text"]
        
        if agent_result.get("weather_data"):
            context["weather_data"] = agent_result["weather_data"]
        
        if agent_result.get("calculation_result"):
            context["calculation_result"] = agent_result["calculation_result"]
        
        return context
    
    def _combine_workflow_results(self, workflow: Dict, results: List[Dict], 
                                original_task: str) -> str:
        """Combine results from multiple agents into a coherent response."""
        
        if workflow['description'] == 'Check weather and send email based on conditions':
            weather_result = next((r for r in results if r['agent_id'] == 'weather_agent'), None)
            email_result = next((r for r in results if r['agent_id'] == 'email_agent'), None)
            
            if weather_result and email_result:
                weather_msg = weather_result['result'].get('message', 'Weather checked')
                email_msg = email_result['result'].get('message', 'Email sent')
                return f"Weather update: {weather_msg}. Email notification: {email_msg}"
        
        # Default combination
        messages = []
        for result in results:
            agent_msg = result['result'].get('message', 'Task completed')
            messages.append(f"{result['agent_id']}: {agent_msg}")
        
        return "Multi-agent task completed. " + " | ".join(messages)
    
    async def _execute_agent(self, agent_id: str, input_query: str, 
                           user_id: str, session_id: str) -> Dict[str, Any]:
        """Execute a specific agent."""
        try:
            # This is a placeholder - in actual implementation, 
            # you would call the real agent instances
            
            self.logger.info(f"Executing {agent_id} with query: {input_query[:50]}...")
            
            # Simulate agent execution
            await asyncio.sleep(0.1)  # Simulate processing time
            
            return {
                "status": "success",
                "message": f"{agent_id} processed: {input_query[:100]}...",
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing agent {agent_id}: {e}")
            return {
                "status": "error",
                "message": f"Agent {agent_id} failed: {str(e)}",
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _handle_single_agent_task(self, task: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Handle task that requires only a single agent."""
        # This would route to the conversation engine for single-agent tasks
        return {
            "status": "success",
            "message": f"Single agent task: {task}",
            "single_agent": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _log_coordination(self, task: str, workflow: Dict, result: Dict,
                              user_id: str, session_id: str):
        """Log coordination activity."""
        try:
            coordination_log = {
                "task_description": task,
                "workflow_used": workflow['description'],
                "agents_involved": workflow['agents'],
                "result_status": result.get("status"),
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow()
            }
            
            # Store in MongoDB (you would implement this)
            self.logger.info(f"Coordination completed: {workflow['description']}")
            
        except Exception as e:
            self.logger.error(f"Error logging coordination: {e}")
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics."""
        return {
            "registered_agents": len(self.registered_agents),
            "available_workflows": len(self.workflow_patterns),
            "agent_capabilities": self.agent_capabilities,
            "workflow_patterns": list(self.workflow_patterns.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global instance
inter_agent_coordinator = InterAgentCoordinator()
