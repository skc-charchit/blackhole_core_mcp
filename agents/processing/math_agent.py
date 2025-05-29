#!/usr/bin/env python3
"""
Math Agent - Mathematical Calculations and Operations
Handles mathematical expressions, calculations, and problem solving
"""

import os
import re
import math
import operator
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

class MathAgent(BaseMCPAgent):
    """Math agent for mathematical calculations and operations."""
    
    def __init__(self):
        capabilities = [
            AgentCapability(
                name="mathematical_operations",
                description="Perform mathematical calculations and solve problems",
                input_types=["text", "dict"],
                output_types=["dict"],
                methods=["calculate", "solve", "evaluate", "process", "info"]
            )
        ]
        
        super().__init__("math_agent", "Math Agent", capabilities)
        
        # Mathematical operations mapping
        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '//': operator.floordiv,
            '%': operator.mod,
            '**': operator.pow,
            '^': operator.pow
        }
        
        # Mathematical functions
        self.functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'ceil': math.ceil,
            'floor': math.floor,
            'factorial': math.factorial
        }
        
        # Mathematical constants
        self.constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau
        }
        
        self.logger.info("Math Agent initialized")
    
    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method."""
        try:
            params = message.params
            
            # Get the mathematical expression or query
            expression = params.get("expression", "") or params.get("query", "") or params.get("text", "")
            
            if not expression:
                return {
                    "status": "error",
                    "message": "No mathematical expression provided",
                    "examples": [
                        "2 + 3 * 4",
                        "sqrt(16) + 5",
                        "sin(pi/2)",
                        "What is 15% of 200?",
                        "Calculate the area of a circle with radius 5"
                    ],
                    "agent": self.agent_id
                }
            
            # Process the mathematical expression
            return await self.process_math_expression(expression)
            
        except Exception as e:
            self.logger.error(f"Error in process: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }
    
    async def process_math_expression(self, expression: str) -> Dict[str, Any]:
        """Process mathematical expression or word problem."""
        try:
            expression = expression.strip()
            
            # Check if it's a word problem
            if self.is_word_problem(expression):
                return await self.solve_word_problem(expression)
            
            # Check if it's a direct mathematical expression
            elif self.is_math_expression(expression):
                return await self.evaluate_expression(expression)
            
            # Try to extract mathematical expression from text
            else:
                extracted_expr = self.extract_math_from_text(expression)
                if extracted_expr:
                    return await self.evaluate_expression(extracted_expr)
                else:
                    return {
                        "status": "error",
                        "message": "Could not identify mathematical expression",
                        "input": expression,
                        "suggestions": [
                            "Try a direct expression like '2 + 3'",
                            "Use word problems like 'What is 15% of 200?'",
                            "Include mathematical functions like 'sqrt(16)'"
                        ],
                        "agent": self.agent_id
                    }
                    
        except Exception as e:
            self.logger.error(f"Error processing math expression: {e}")
            return {
                "status": "error",
                "message": f"Failed to process expression: {str(e)}",
                "agent": self.agent_id
            }
    
    def is_word_problem(self, text: str) -> bool:
        """Check if the text is a word problem."""
        word_indicators = [
            "what is", "calculate", "find", "solve", "how much", "how many",
            "percentage", "percent", "%", "area", "volume", "circumference",
            "distance", "speed", "time", "rate", "interest", "profit", "loss"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in word_indicators)
    
    def is_math_expression(self, text: str) -> bool:
        """Check if the text is a direct mathematical expression."""
        # Remove spaces and check for mathematical characters
        clean_text = text.replace(" ", "")
        math_chars = set("0123456789+-*/()^.%")
        math_functions = ["sin", "cos", "tan", "sqrt", "log", "exp", "abs"]
        
        # Check if it contains mathematical characters or functions
        has_math_chars = any(char in math_chars for char in clean_text)
        has_math_functions = any(func in text.lower() for func in math_functions)
        
        return has_math_chars or has_math_functions
    
    def extract_math_from_text(self, text: str) -> Optional[str]:
        """Extract mathematical expression from text."""
        # Look for patterns like "2 + 3", "sqrt(16)", etc.
        math_patterns = [
            r'(\d+(?:\.\d+)?\s*[+\-*/^%]\s*\d+(?:\.\d+)?)',
            r'(sqrt\(\d+(?:\.\d+)?\))',
            r'(sin\([^)]+\))',
            r'(cos\([^)]+\))',
            r'(tan\([^)]+\))',
            r'(log\([^)]+\))',
            r'(\d+(?:\.\d+)?\s*\*\*\s*\d+(?:\.\d+)?)'
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    async def solve_word_problem(self, problem: str) -> Dict[str, Any]:
        """Solve word problems."""
        try:
            problem_lower = problem.lower()
            
            # Percentage problems
            if "%" in problem or "percent" in problem_lower:
                return self.solve_percentage_problem(problem)
            
            # Area problems
            elif "area" in problem_lower:
                return self.solve_area_problem(problem)
            
            # Basic arithmetic word problems
            elif any(word in problem_lower for word in ["add", "sum", "plus", "total"]):
                return self.solve_addition_problem(problem)
            
            elif any(word in problem_lower for word in ["subtract", "minus", "difference"]):
                return self.solve_subtraction_problem(problem)
            
            elif any(word in problem_lower for word in ["multiply", "times", "product"]):
                return self.solve_multiplication_problem(problem)
            
            elif any(word in problem_lower for word in ["divide", "divided", "quotient"]):
                return self.solve_division_problem(problem)
            
            else:
                return {
                    "status": "error",
                    "message": "Could not identify the type of word problem",
                    "problem": problem,
                    "supported_types": [
                        "Percentage calculations",
                        "Area calculations",
                        "Basic arithmetic (add, subtract, multiply, divide)"
                    ],
                    "agent": self.agent_id
                }
                
        except Exception as e:
            self.logger.error(f"Error solving word problem: {e}")
            return {
                "status": "error",
                "message": f"Failed to solve word problem: {str(e)}",
                "agent": self.agent_id
            }
    
    def solve_percentage_problem(self, problem: str) -> Dict[str, Any]:
        """Solve percentage problems."""
        try:
            # Extract numbers from the problem
            numbers = re.findall(r'\d+(?:\.\d+)?', problem)
            
            if len(numbers) >= 2:
                if "%" in problem or "percent" in problem.lower():
                    # Format: "What is X% of Y?"
                    percentage = float(numbers[0])
                    value = float(numbers[1])
                    result = (percentage / 100) * value
                    
                    return {
                        "status": "success",
                        "problem": problem,
                        "calculation": f"{percentage}% of {value}",
                        "result": result,
                        "formatted_result": f"{result:.2f}",
                        "explanation": f"{percentage}% of {value} = ({percentage}/100) × {value} = {result:.2f}",
                        "agent": self.agent_id
                    }
            
            return {
                "status": "error",
                "message": "Could not extract numbers from percentage problem",
                "problem": problem,
                "agent": self.agent_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in percentage calculation: {str(e)}",
                "agent": self.agent_id
            }
    
    def solve_area_problem(self, problem: str) -> Dict[str, Any]:
        """Solve area calculation problems."""
        try:
            numbers = re.findall(r'\d+(?:\.\d+)?', problem)
            problem_lower = problem.lower()
            
            if "circle" in problem_lower and len(numbers) >= 1:
                radius = float(numbers[0])
                area = math.pi * radius ** 2
                
                return {
                    "status": "success",
                    "problem": problem,
                    "shape": "circle",
                    "radius": radius,
                    "calculation": f"π × {radius}²",
                    "result": area,
                    "formatted_result": f"{area:.2f}",
                    "explanation": f"Area of circle = π × r² = π × {radius}² = {area:.2f}",
                    "agent": self.agent_id
                }
            
            elif "rectangle" in problem_lower and len(numbers) >= 2:
                length = float(numbers[0])
                width = float(numbers[1])
                area = length * width
                
                return {
                    "status": "success",
                    "problem": problem,
                    "shape": "rectangle",
                    "length": length,
                    "width": width,
                    "calculation": f"{length} × {width}",
                    "result": area,
                    "formatted_result": f"{area:.2f}",
                    "explanation": f"Area of rectangle = length × width = {length} × {width} = {area:.2f}",
                    "agent": self.agent_id
                }
            
            elif "square" in problem_lower and len(numbers) >= 1:
                side = float(numbers[0])
                area = side ** 2
                
                return {
                    "status": "success",
                    "problem": problem,
                    "shape": "square",
                    "side": side,
                    "calculation": f"{side}²",
                    "result": area,
                    "formatted_result": f"{area:.2f}",
                    "explanation": f"Area of square = side² = {side}² = {area:.2f}",
                    "agent": self.agent_id
                }
            
            return {
                "status": "error",
                "message": "Could not identify shape or extract dimensions",
                "problem": problem,
                "supported_shapes": ["circle", "rectangle", "square"],
                "agent": self.agent_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in area calculation: {str(e)}",
                "agent": self.agent_id
            }
    
    def solve_addition_problem(self, problem: str) -> Dict[str, Any]:
        """Solve addition problems."""
        numbers = re.findall(r'\d+(?:\.\d+)?', problem)
        if len(numbers) >= 2:
            nums = [float(n) for n in numbers]
            result = sum(nums)
            return {
                "status": "success",
                "problem": problem,
                "numbers": nums,
                "operation": "addition",
                "calculation": " + ".join(numbers),
                "result": result,
                "explanation": f"{' + '.join(numbers)} = {result}",
                "agent": self.agent_id
            }
        return {"status": "error", "message": "Could not extract numbers for addition", "agent": self.agent_id}
    
    def solve_subtraction_problem(self, problem: str) -> Dict[str, Any]:
        """Solve subtraction problems."""
        numbers = re.findall(r'\d+(?:\.\d+)?', problem)
        if len(numbers) >= 2:
            nums = [float(n) for n in numbers]
            result = nums[0] - nums[1]
            return {
                "status": "success",
                "problem": problem,
                "numbers": nums,
                "operation": "subtraction",
                "calculation": f"{numbers[0]} - {numbers[1]}",
                "result": result,
                "explanation": f"{numbers[0]} - {numbers[1]} = {result}",
                "agent": self.agent_id
            }
        return {"status": "error", "message": "Could not extract numbers for subtraction", "agent": self.agent_id}
    
    def solve_multiplication_problem(self, problem: str) -> Dict[str, Any]:
        """Solve multiplication problems."""
        numbers = re.findall(r'\d+(?:\.\d+)?', problem)
        if len(numbers) >= 2:
            nums = [float(n) for n in numbers]
            result = nums[0] * nums[1]
            return {
                "status": "success",
                "problem": problem,
                "numbers": nums,
                "operation": "multiplication",
                "calculation": f"{numbers[0]} × {numbers[1]}",
                "result": result,
                "explanation": f"{numbers[0]} × {numbers[1]} = {result}",
                "agent": self.agent_id
            }
        return {"status": "error", "message": "Could not extract numbers for multiplication", "agent": self.agent_id}
    
    def solve_division_problem(self, problem: str) -> Dict[str, Any]:
        """Solve division problems."""
        numbers = re.findall(r'\d+(?:\.\d+)?', problem)
        if len(numbers) >= 2:
            nums = [float(n) for n in numbers]
            if nums[1] != 0:
                result = nums[0] / nums[1]
                return {
                    "status": "success",
                    "problem": problem,
                    "numbers": nums,
                    "operation": "division",
                    "calculation": f"{numbers[0]} ÷ {numbers[1]}",
                    "result": result,
                    "explanation": f"{numbers[0]} ÷ {numbers[1]} = {result}",
                    "agent": self.agent_id
                }
            else:
                return {"status": "error", "message": "Division by zero is not allowed", "agent": self.agent_id}
        return {"status": "error", "message": "Could not extract numbers for division", "agent": self.agent_id}
    
    async def evaluate_expression(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expression."""
        try:
            # Clean and prepare expression
            clean_expr = self.clean_expression(expression)
            
            # Replace constants
            for const, value in self.constants.items():
                clean_expr = clean_expr.replace(const, str(value))
            
            # Replace ^ with **
            clean_expr = clean_expr.replace('^', '**')
            
            # Evaluate safely
            result = self.safe_eval(clean_expr)
            
            return {
                "status": "success",
                "expression": expression,
                "cleaned_expression": clean_expr,
                "result": result,
                "formatted_result": f"{result:.6f}".rstrip('0').rstrip('.') if isinstance(result, float) else str(result),
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating expression: {e}")
            return {
                "status": "error",
                "message": f"Failed to evaluate expression: {str(e)}",
                "expression": expression,
                "agent": self.agent_id
            }
    
    def clean_expression(self, expression: str) -> str:
        """Clean mathematical expression."""
        # Remove extra spaces
        clean = re.sub(r'\s+', '', expression)
        
        # Handle mathematical functions
        for func_name in self.functions.keys():
            clean = re.sub(f'{func_name}\\(', f'math.{func_name}(', clean)
        
        return clean
    
    def safe_eval(self, expression: str) -> Union[int, float]:
        """Safely evaluate mathematical expression."""
        # Create safe namespace
        safe_dict = {
            "__builtins__": {},
            "math": math,
            **self.constants
        }
        
        # Add mathematical functions to namespace
        for name, func in self.functions.items():
            safe_dict[name] = func
        
        # Evaluate expression
        result = eval(expression, safe_dict)
        return result
    
    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request."""
        return {
            "status": "success",
            "info": self.get_info(),
            "supported_operations": list(self.operations.keys()),
            "supported_functions": list(self.functions.keys()),
            "supported_constants": list(self.constants.keys()),
            "examples": [
                "2 + 3 * 4",
                "sqrt(16) + 5",
                "sin(pi/2)",
                "What is 15% of 200?",
                "Calculate the area of a circle with radius 5"
            ],
            "agent": self.agent_id
        }

# Agent registration
def get_agent_info():
    """Get agent information for auto-discovery."""
    return {
        "name": "Math Agent",
        "description": "Performs mathematical calculations, solves word problems, and evaluates expressions",
        "version": "1.0.0",
        "author": "MCP System",
        "capabilities": ["mathematical_operations", "word_problems", "expression_evaluation"],
        "category": "specialized"
    }

def create_agent():
    """Create and return the agent instance."""
    return MathAgent()

if __name__ == "__main__":
    # Test the agent
    import asyncio
    
    async def test_agent():
        print("🔢 Testing Math Agent")
        print("=" * 40)
        
        agent = MathAgent()
        
        test_expressions = [
            "2 + 3 * 4",
            "sqrt(16) + 5",
            "What is 15% of 200?",
            "Calculate the area of a circle with radius 5"
        ]
        
        for expr in test_expressions:
            print(f"\nTesting: {expr}")
            
            message = MCPMessage(
                id=f"test_{datetime.now().timestamp()}",
                method="process",
                params={"expression": expr},
                timestamp=datetime.now()
            )
            
            result = await agent.process_message(message)
            
            if result["status"] == "success":
                print(f"✅ Result: {result.get('result', result.get('formatted_result', 'N/A'))}")
            else:
                print(f"❌ Error: {result['message']}")
        
        print("\n✅ Math Agent test completed!")
    
    asyncio.run(test_agent())
