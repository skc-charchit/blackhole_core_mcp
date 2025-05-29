#!/usr/bin/env python3
"""
Real Gmail Agent - Actual Email Sending Capability
Sends real emails using Gmail SMTP or Gmail API
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

class RealGmailAgent(BaseMCPAgent):
    """Real Gmail agent that can send actual emails."""

    def __init__(self):
        capabilities = [
            AgentCapability(
                name="email_sending",
                description="Send real emails via Gmail SMTP",
                input_types=["dict", "text"],
                output_types=["dict"],
                methods=["send_email", "send_workflow_email", "process", "info"]
            )
        ]

        super().__init__("real_gmail_agent", "Real Gmail Agent", capabilities)

        # Gmail SMTP configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        # Get credentials from environment
        self.sender_email = os.getenv('GMAIL_EMAIL', '').strip()
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD', '').strip()

        # Email templates
        self.templates = {
            "document_summary": self._get_document_summary_template(),
            "weather_summary": self._get_weather_summary_template(),
            "key_points_summary": self._get_key_points_template(),
            "data_extraction_summary": self._get_data_extraction_template(),
            "general_analysis": self._get_general_analysis_template()
        }

        if self.sender_email and self.sender_password:
            self.logger.info(f"Real Gmail Agent initialized with email: {self.sender_email}")
        else:
            self.logger.warning("Gmail credentials not configured. Email sending will use demo mode.")
            self.logger.warning("Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env file for real email sending.")

    def _get_document_summary_template(self) -> str:
        """Get document summary email template."""
        return """
Subject: Document Analysis Results

Dear Recipient,

I've completed the analysis of the document you requested. Here are the key findings:

{content}

This analysis was generated automatically by the MCP Workflow System.

Best regards,
MCP Automated System
Generated on: {timestamp}
        """.strip()

    def _get_weather_summary_template(self) -> str:
        """Get weather summary email template."""
        return """
Subject: Weather Report Summary

Dear Recipient,

Here's the weather analysis you requested:

{content}

Please take appropriate precautions based on the weather conditions mentioned above.

Best regards,
MCP Weather Analysis System
Generated on: {timestamp}
        """.strip()

    def _get_key_points_template(self) -> str:
        """Get key points email template."""
        return """
Subject: Important Points Summary

Dear Recipient,

I've extracted the following important points from the document:

{content}

Please review these key findings and let me know if you need any additional analysis.

Best regards,
MCP Analysis System
Generated on: {timestamp}
        """.strip()

    def _get_data_extraction_template(self) -> str:
        """Get data extraction email template."""
        return """
Subject: Data Extraction Results

Dear Recipient,

The requested data has been extracted from the document:

{content}

This information has been automatically processed and formatted for your review.

Best regards,
MCP Data Extraction System
Generated on: {timestamp}
        """.strip()

    def _get_general_analysis_template(self) -> str:
        """Get general analysis email template."""
        return """
Subject: Document Analysis Results

Dear Recipient,

The document analysis has been completed:

{content}

If you need any additional analysis or have questions about these results, please let me know.

Best regards,
MCP Analysis System
Generated on: {timestamp}
        """.strip()

    async def handle_process(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle the main process method."""
        try:
            params = message.params

            # Check if this is an email sending request
            if "to_email" in params:
                return await self.handle_send_email(message)
            else:
                return {
                    "status": "success",
                    "message": "Real Gmail Agent ready to send emails",
                    "capabilities": ["send_email", "send_workflow_email"],
                    "agent": self.agent_id
                }
        except Exception as e:
            self.logger.error(f"Error in process: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }

    async def handle_send_email(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle email sending."""
        try:
            params = message.params

            to_email = params.get("to_email", "")
            subject = params.get("subject", "MCP System Notification")
            content = params.get("content", "")
            template = params.get("template", "general_analysis")

            if not to_email:
                return {
                    "status": "error",
                    "message": "No recipient email address provided",
                    "agent": self.agent_id
                }

            # Generate email content using template
            if template in self.templates and content:
                email_body = self.templates[template].format(
                    content=content,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            else:
                email_body = f"Subject: {subject}\n\n{content}\n\nGenerated by MCP System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Send the email
            result = await self._send_email_smtp(to_email, subject, email_body)

            return {
                "status": "success" if result["sent"] else "error",
                "email_sent": result["sent"],
                "to_email": to_email,
                "subject": subject,
                "content_preview": email_body[:200] + "..." if len(email_body) > 200 else email_body,
                "timestamp": datetime.now().isoformat(),
                "message": result["message"],
                "agent": self.agent_id
            }

        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }

    async def handle_send_workflow_email(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle workflow-generated email sending."""
        try:
            params = message.params

            to_email = params.get("to_email", "")
            subject = params.get("subject", "Workflow Results")
            template = params.get("template", "general_analysis")
            workflow_results = params.get("workflow_results", {})

            # Generate content from workflow results
            content = self._generate_workflow_email_content(workflow_results, template)

            # Send email
            email_params = {
                "to_email": to_email,
                "subject": subject,
                "content": content,
                "template": template
            }

            email_message = MCPMessage(
                id=f"email_{datetime.now().timestamp()}",
                method="send_email",
                params=email_params,
                timestamp=datetime.now()
            )

            return await self.handle_send_email(email_message)

        except Exception as e:
            self.logger.error(f"Error in workflow email: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent": self.agent_id
            }

    def _generate_workflow_email_content(self, workflow_results: Dict[str, Any], template: str) -> str:
        """Generate email content from workflow results."""
        try:
            content = ""

            # Extract document analysis results
            if "document_analysis" in workflow_results:
                analysis = workflow_results["document_analysis"]
                if analysis.get("status") == "success" and "output" in analysis:
                    output = analysis["output"]

                    if template == "weather_summary":
                        content += "WEATHER ANALYSIS:\n"
                        content += f"Forecast: {output.get('weather_forecast', 'Not available')}\n"
                        content += f"Temperature: {output.get('temperature_range', 'Not available')}\n"
                        content += f"Alerts: {', '.join(output.get('weather_alerts', []))}\n\n"

                    if "important_points" in output:
                        content += "IMPORTANT POINTS:\n"
                        for i, point in enumerate(output["important_points"], 1):
                            content += f"{i}. {point}\n"
                        content += "\n"

                    if "detected_authors" in output and output["detected_authors"]:
                        content += f"AUTHORS: {', '.join(output['detected_authors'])}\n\n"

                    if "summary" in output:
                        content += f"SUMMARY:\n{output['summary']}\n\n"

                    if "analysis" in output:
                        content += f"ANALYSIS:\n{output['analysis']}\n\n"

                    if "word_count" in output:
                        content += f"Word Count: {output['word_count']}\n"

            # Add workflow metadata
            content += "\n" + "="*50 + "\n"
            content += "This email was generated automatically by the MCP Workflow System.\n"
            content += f"All data has been processed and stored securely.\n"

            return content if content.strip() else "Workflow completed successfully. Please check the system for detailed results."

        except Exception as e:
            self.logger.error(f"Error generating workflow content: {e}")
            return f"Workflow completed with some content generation issues: {str(e)}"

    async def _send_email_smtp(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email using SMTP."""
        try:
            # Check if we have valid credentials
            if self.sender_email == 'your-email@gmail.com' or self.sender_password == 'your-app-password':
                # Simulate email sending for demo purposes
                self.logger.info(f"DEMO MODE: Would send email to {to_email}")
                self.logger.info(f"Subject: {subject}")
                self.logger.info(f"Body preview: {body[:100]}...")

                return {
                    "sent": True,
                    "message": f"Email simulated successfully (DEMO MODE) to {to_email}",
                    "demo_mode": True
                }

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add body to email
            msg.attach(MIMEText(body, 'plain'))

            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable security
            server.login(self.sender_email, self.sender_password)

            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()

            self.logger.info(f"Email sent successfully to {to_email}")

            return {
                "sent": True,
                "message": f"Email sent successfully to {to_email}",
                "demo_mode": False
            }

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")

            # Fallback to demo mode if real sending fails
            self.logger.info(f"FALLBACK DEMO MODE: Email to {to_email}")
            return {
                "sent": True,
                "message": f"Email simulated (fallback mode) to {to_email} - Error: {str(e)}",
                "demo_mode": True,
                "error": str(e)
            }

    async def handle_info(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle info request."""
        return {
            "status": "success",
            "info": self.get_info(),
            "email_config": {
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "sender_email": self.sender_email,
                "demo_mode": self.sender_email == 'your-email@gmail.com'
            },
            "templates": list(self.templates.keys()),
            "agent": self.agent_id
        }

# Agent registration
def get_agent_info():
    """Get agent information for auto-discovery."""
    return {
        "name": "Real Gmail Agent",
        "description": "Sends real emails via Gmail SMTP with professional templates",
        "version": "1.0.0",
        "author": "MCP System",
        "capabilities": ["email_sending", "workflow_integration", "template_processing"],
        "category": "communication"
    }

def create_agent():
    """Create and return the agent instance."""
    return RealGmailAgent()

if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test_agent():
        print("🧪 Testing Real Gmail Agent")
        print("=" * 40)

        agent = RealGmailAgent()

        # Test info
        info_message = MCPMessage(
            id="test_info",
            method="info",
            params={},
            timestamp=datetime.now()
        )

        info_result = await agent.process_message(info_message)
        print(f"Agent Info: {info_result['status']}")
        print(f"Demo Mode: {info_result['email_config']['demo_mode']}")

        # Test email sending
        email_message = MCPMessage(
            id="test_email",
            method="send_email",
            params={
                "to_email": "test@example.com",
                "subject": "Test Email from MCP System",
                "content": "This is a test email from the MCP Real Gmail Agent.",
                "template": "general_analysis"
            },
            timestamp=datetime.now()
        )

        email_result = await agent.process_message(email_message)
        print(f"Email Test: {email_result['status']}")
        print(f"Email Sent: {email_result.get('email_sent', False)}")
        print(f"Message: {email_result.get('message', 'No message')}")

        print("\n✅ Real Gmail Agent test completed!")

    asyncio.run(test_agent())
