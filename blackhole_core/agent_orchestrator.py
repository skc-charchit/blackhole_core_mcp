#!/usr/bin/env python3
"""
Agent Orchestrator - Enables inter-agent communication and collaboration
Agents can interact with each other to provide comprehensive responses
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from .universal_connector import universal_connector
from .agent_registry import agent_registry

logger = logging.getLogger(__name__)

@dataclass
class AgentTask:
    """Represents a task for an agent."""
    task_id: str
    agent_id: str
    input_data: Any
    context: Dict[str, Any]
    dependencies: List[str] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: str = None
    created_at: datetime = None
    completed_at: datetime = None

class AgentOrchestrator:
    """
    Orchestrates multiple agents to work together and communicate.
    Enables complex workflows where agents collaborate to solve problems.
    """
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        self.active_workflows = {}
        self.agent_capabilities = {}
        self.collaboration_patterns = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks = {}
        
        # Initialize collaboration patterns
        self._setup_collaboration_patterns()
    
    def _setup_collaboration_patterns(self):
        """Setup common collaboration patterns between agents."""
        self.collaboration_patterns = {
            # Document processing workflow
            "document_analysis": {
                "description": "Complete document analysis with multiple agents",
                "workflow": [
                    {"agent": "document_processor", "task": "extract_text"},
                    {"agent": "nlp_agent", "task": "analyze_content", "depends_on": ["extract_text"]},
                    {"agent": "summary_agent", "task": "create_summary", "depends_on": ["analyze_content"]},
                    {"agent": "insight_agent", "task": "generate_insights", "depends_on": ["analyze_content", "create_summary"]}
                ]
            },
            
            # Data processing pipeline
            "data_pipeline": {
                "description": "Multi-stage data processing",
                "workflow": [
                    {"agent": "data_extractor", "task": "extract_data"},
                    {"agent": "data_cleaner", "task": "clean_data", "depends_on": ["extract_data"]},
                    {"agent": "data_analyzer", "task": "analyze_data", "depends_on": ["clean_data"]},
                    {"agent": "report_generator", "task": "generate_report", "depends_on": ["analyze_data"]}
                ]
            },
            
            # Research workflow
            "research_task": {
                "description": "Comprehensive research with multiple sources",
                "workflow": [
                    {"agent": "search_agent", "task": "search_documents"},
                    {"agent": "web_agent", "task": "search_web", "parallel": True},
                    {"agent": "data_agent", "task": "search_databases", "parallel": True},
                    {"agent": "synthesis_agent", "task": "synthesize_results", "depends_on": ["search_documents", "search_web", "search_databases"]},
                    {"agent": "report_agent", "task": "create_report", "depends_on": ["synthesize_results"]}
                ]
            },
            
            # Content creation workflow
            "content_creation": {
                "description": "Collaborative content creation",
                "workflow": [
                    {"agent": "research_agent", "task": "gather_information"},
                    {"agent": "outline_agent", "task": "create_outline", "depends_on": ["gather_information"]},
                    {"agent": "writer_agent", "task": "write_content", "depends_on": ["create_outline"]},
                    {"agent": "editor_agent", "task": "edit_content", "depends_on": ["write_content"]},
                    {"agent": "reviewer_agent", "task": "review_content", "depends_on": ["edit_content"]}
                ]
            }
        }
    
    async def process_collaborative_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user request that may require multiple agents working together.
        
        Args:
            user_input: User's request
            context: Additional context
            
        Returns:
            Comprehensive response from collaborative agents
        """
        try:
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Analyze request to determine collaboration strategy
            collaboration_plan = await self._analyze_collaboration_needs(user_input, context)
            
            if collaboration_plan["requires_collaboration"]:
                # Execute collaborative workflow
                result = await self._execute_collaborative_workflow(
                    workflow_id, user_input, collaboration_plan, context
                )
            else:
                # Single agent can handle this
                result = await self._execute_single_agent(user_input, collaboration_plan["primary_agent"], context)
            
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "collaboration_used": collaboration_plan["requires_collaboration"],
                "agents_involved": collaboration_plan.get("agents_involved", [collaboration_plan.get("primary_agent")]),
                "result": result,
                "processing_approach": "collaborative" if collaboration_plan["requires_collaboration"] else "single_agent",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in collaborative processing: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_collaboration_needs(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze if the request requires multiple agents to collaborate."""
        user_input_lower = user_input.lower()
        
        # Keywords that indicate need for collaboration
        collaboration_keywords = {
            "comprehensive": ["comprehensive", "complete", "thorough", "detailed", "full"],
            "analysis": ["analyze", "analysis", "examine", "study", "investigate"],
            "research": ["research", "find", "gather", "collect", "investigate"],
            "compare": ["compare", "contrast", "versus", "vs", "difference"],
            "create": ["create", "generate", "build", "make", "produce"],
            "process": ["process", "transform", "convert", "handle"],
            "multiple": ["multiple", "several", "various", "different", "many"]
        }
        
        # Check for collaboration indicators
        collaboration_score = 0
        detected_categories = []
        
        for category, keywords in collaboration_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                collaboration_score += 1
                detected_categories.append(category)
        
        # Determine if collaboration is needed
        requires_collaboration = collaboration_score >= 2 or any(
            pattern in user_input_lower for pattern in [
                "step by step", "comprehensive analysis", "detailed report",
                "research and analyze", "process and summarize", "extract and analyze"
            ]
        )
        
        if requires_collaboration:
            # Determine which agents should collaborate
            agents_needed = await self._identify_required_agents(user_input, detected_categories)
            workflow_pattern = self._select_workflow_pattern(detected_categories, agents_needed)
            
            return {
                "requires_collaboration": True,
                "collaboration_score": collaboration_score,
                "detected_categories": detected_categories,
                "agents_involved": agents_needed,
                "workflow_pattern": workflow_pattern,
                "reasoning": f"Detected {collaboration_score} collaboration indicators: {detected_categories}"
            }
        else:
            # Single agent can handle this
            primary_agent = await self._identify_primary_agent(user_input)
            return {
                "requires_collaboration": False,
                "primary_agent": primary_agent,
                "reasoning": "Single agent sufficient for this request"
            }
    
    async def _identify_required_agents(self, user_input: str, categories: List[str]) -> List[str]:
        """Identify which agents are needed for the collaborative task."""
        available_agents = list(universal_connector.connected_agents.keys())
        
        # Built-in agents
        builtin_agents = ["document_processor", "archive_search", "live_data"]
        
        # Agent selection based on categories and input
        selected_agents = []
        user_input_lower = user_input.lower()
        
        # Document processing
        if any(cat in ["analysis", "process"] for cat in categories) or any(
            word in user_input_lower for word in ["document", "text", "file", "pdf"]
        ):
            selected_agents.append("document_processor")
        
        # Search and research
        if any(cat in ["research", "comprehensive"] for cat in categories) or any(
            word in user_input_lower for word in ["search", "find", "research", "information"]
        ):
            selected_agents.append("archive_search")
        
        # Live data
        if any(word in user_input_lower for word in ["weather", "current", "live", "real-time"]):
            selected_agents.append("live_data")
        
        # Add available external agents that might be relevant
        for agent_id in available_agents:
            agent_info = universal_connector.connected_agents.get(agent_id, {})
            capabilities = agent_info.get("capabilities", {})
            keywords = capabilities.get("keywords", [])
            
            # Check if agent keywords match the request
            if any(keyword.lower() in user_input_lower for keyword in keywords):
                if agent_id not in selected_agents:
                    selected_agents.append(agent_id)
        
        return selected_agents[:5]  # Limit to 5 agents to avoid complexity
    
    async def _identify_primary_agent(self, user_input: str) -> str:
        """Identify the primary agent for single-agent requests."""
        # Use existing routing logic from universal connector
        external_response = universal_connector.route_request(user_input)
        
        if external_response.get("status") == "success":
            routing_info = external_response.get("routing_info", {})
            return routing_info.get("selected_agent", "document_processor")
        
        # Fallback to built-in agent selection
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["weather", "temperature", "climate"]):
            return "live_data"
        elif any(word in user_input_lower for word in ["search", "find", "documents"]):
            return "archive_search"
        else:
            return "document_processor"
    
    def _select_workflow_pattern(self, categories: List[str], agents: List[str]) -> str:
        """Select the most appropriate workflow pattern."""
        if "analysis" in categories and "document_processor" in agents:
            return "document_analysis"
        elif "research" in categories:
            return "research_task"
        elif "create" in categories:
            return "content_creation"
        elif "process" in categories:
            return "data_pipeline"
        else:
            return "custom"
    
    async def _execute_collaborative_workflow(self, workflow_id: str, user_input: str, 
                                           collaboration_plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a collaborative workflow with multiple agents."""
        agents_involved = collaboration_plan["agents_involved"]
        workflow_pattern = collaboration_plan["workflow_pattern"]
        
        logger.info(f"Starting collaborative workflow {workflow_id} with agents: {agents_involved}")
        
        # Create workflow execution plan
        if workflow_pattern in self.collaboration_patterns:
            # Use predefined pattern
            workflow_steps = self.collaboration_patterns[workflow_pattern]["workflow"]
        else:
            # Create custom workflow
            workflow_steps = self._create_custom_workflow(agents_involved, user_input)
        
        # Execute workflow steps
        workflow_results = {}
        step_results = {}
        
        for step_index, step in enumerate(workflow_steps):
            step_id = f"step_{step_index + 1}"
            agent_id = step["agent"]
            
            # Check if agent is available
            if agent_id not in agents_involved:
                continue
            
            # Wait for dependencies
            dependencies = step.get("depends_on", [])
            if dependencies:
                await self._wait_for_dependencies(dependencies, step_results)
            
            # Prepare input for this step
            step_input = self._prepare_step_input(user_input, step, step_results, context)
            
            # Execute step
            try:
                logger.info(f"Executing step {step_id} with agent {agent_id}")
                step_result = await self._execute_agent_step(agent_id, step_input, context)
                step_results[step.get("task", step_id)] = step_result
                
                # Store intermediate result
                workflow_results[step_id] = {
                    "agent": agent_id,
                    "task": step.get("task", "process"),
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in step {step_id} with agent {agent_id}: {e}")
                workflow_results[step_id] = {
                    "agent": agent_id,
                    "task": step.get("task", "process"),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Synthesize final result
        final_result = self._synthesize_workflow_results(workflow_results, user_input)
        
        return {
            "workflow_pattern": workflow_pattern,
            "steps_executed": len(workflow_results),
            "agents_used": agents_involved,
            "step_results": workflow_results,
            "final_result": final_result,
            "collaboration_summary": self._create_collaboration_summary(workflow_results)
        }
    
    async def _execute_single_agent(self, user_input: str, agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request with a single agent."""
        try:
            if agent_id in universal_connector.connected_agents:
                # External agent
                response = universal_connector.route_request(user_input, context)
                return {
                    "agent_used": agent_id,
                    "result": response.get("result"),
                    "type": "external_agent"
                }
            else:
                # Built-in agent - this would integrate with existing MCP processor
                return {
                    "agent_used": agent_id,
                    "result": f"Processed by {agent_id}: {user_input}",
                    "type": "builtin_agent"
                }
                
        except Exception as e:
            logger.error(f"Error executing single agent {agent_id}: {e}")
            return {
                "agent_used": agent_id,
                "error": str(e),
                "type": "error"
            }
    
    def _create_custom_workflow(self, agents: List[str], user_input: str) -> List[Dict[str, Any]]:
        """Create a custom workflow for the given agents."""
        workflow = []
        
        # Simple sequential workflow
        for i, agent in enumerate(agents):
            step = {
                "agent": agent,
                "task": f"process_step_{i + 1}"
            }
            
            # Add dependencies (each step depends on previous)
            if i > 0:
                step["depends_on"] = [f"process_step_{i}"]
            
            workflow.append(step)
        
        return workflow
    
    def _prepare_step_input(self, original_input: str, step: Dict[str, Any], 
                          previous_results: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Prepare input for a workflow step based on previous results."""
        # Start with original input
        step_input = original_input
        
        # Add context from previous steps
        if previous_results:
            context_info = []
            for task_name, result in previous_results.items():
                if isinstance(result, dict) and "result" in result:
                    context_info.append(f"{task_name}: {result['result']}")
                else:
                    context_info.append(f"{task_name}: {str(result)}")
            
            if context_info:
                step_input += f"\n\nContext from previous steps:\n" + "\n".join(context_info)
        
        return step_input
    
    async def _execute_agent_step(self, agent_id: str, step_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step with the specified agent."""
        if agent_id in universal_connector.connected_agents:
            # External agent
            response = universal_connector.route_request(step_input, context)
            return response
        else:
            # Built-in agent - integrate with existing agents
            # This would call the actual agent implementation
            return {
                "status": "success",
                "result": f"Processed by {agent_id}: {step_input[:100]}...",
                "agent": agent_id
            }
    
    async def _wait_for_dependencies(self, dependencies: List[str], step_results: Dict[str, Any]):
        """Wait for dependency steps to complete."""
        max_wait = 30  # seconds
        wait_interval = 0.5
        waited = 0
        
        while waited < max_wait:
            if all(dep in step_results for dep in dependencies):
                return
            
            await asyncio.sleep(wait_interval)
            waited += wait_interval
        
        logger.warning(f"Timeout waiting for dependencies: {dependencies}")
    
    def _synthesize_workflow_results(self, workflow_results: Dict[str, Any], original_input: str) -> Dict[str, Any]:
        """Synthesize the final result from all workflow steps."""
        successful_steps = [
            step for step in workflow_results.values() 
            if "error" not in step and "result" in step
        ]
        
        if not successful_steps:
            return {
                "status": "error",
                "message": "No steps completed successfully",
                "original_input": original_input
            }
        
        # Combine results
        combined_results = []
        agents_used = []
        
        for step in successful_steps:
            agents_used.append(step["agent"])
            result = step["result"]
            
            if isinstance(result, dict):
                combined_results.append(f"Agent {step['agent']}: {result.get('result', str(result))}")
            else:
                combined_results.append(f"Agent {step['agent']}: {str(result)}")
        
        return {
            "status": "success",
            "original_input": original_input,
            "agents_collaborated": agents_used,
            "steps_completed": len(successful_steps),
            "combined_output": "\n\n".join(combined_results),
            "synthesis": f"Collaborative result from {len(agents_used)} agents working together"
        }
    
    def _create_collaboration_summary(self, workflow_results: Dict[str, Any]) -> str:
        """Create a summary of the collaboration process."""
        total_steps = len(workflow_results)
        successful_steps = len([s for s in workflow_results.values() if "error" not in s])
        agents_used = list(set(s["agent"] for s in workflow_results.values()))
        
        return f"Collaboration completed: {successful_steps}/{total_steps} steps successful, {len(agents_used)} agents participated: {', '.join(agents_used)}"

# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()
