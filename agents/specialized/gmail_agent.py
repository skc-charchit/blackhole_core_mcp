#!/usr/bin/env python3
"""
Gmail Agent - Send and receive emails through Gmail API
"""

import asyncio
import json
import base64
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.base_agent import BaseMCPAgent, AgentCapability, MCPMessage

# Agent metadata for auto-discovery
AGENT_METADATA = {
    "id": "gmail_agent",
    "name": "Gmail Agent",
    "version": "1.0.0",
    "author": "MCP System",
    "description": "Send and receive emails through Gmail API integration",
    "dependencies": ["google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"],
    "auto_load": True,
    "priority": 3
}

class GmailAgent(BaseMCPAgent):
    """MCP Agent for Gmail email operations."""
    
    def __init__(self):
        capabilities = [
            AgentCapability(
                name="email_operations",
                description="Send and receive emails through Gmail",
                input_types=["text", "dict"],
                output_types=["dict"],
                methods=["send_email", "read_emails", "search_emails", "get_email_status"],
                can_call_agents=["text_analyzer", "document_processor"]
            )
        ]
        super().__init__("gmail_agent", "Gmail Agent", capabilities)
        
        # Gmail service (will be initialized when needed)
        self.gmail_service = None
        self.credentials = None
        self.authenticated = False
        
        # Email configuration
        self.sender_email = None
        
    async def initialize_gmail_service(self):
        """Initialize Gmail API service."""
        try:
            # Try to import Gmail dependencies
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            # Gmail API scopes
            SCOPES = ['https://www.googleapis.com/auth/gmail.send',
                     'https://www.googleapis.com/auth/gmail.readonly']
            
            creds = None
            
            # Check for existing token
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Need credentials.json file for OAuth
                    if os.path.exists('credentials.json'):
                        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        self.log_error("Gmail credentials.json file not found")
                        return False
                
                # Save credentials for next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            self.authenticated = True
            
            # Get sender email
            profile = self.gmail_service.users().getProfile(userId='me').execute()
            self.sender_email = profile.get('emailAddress')
            
            self.log_info(f"Gmail service initialized for {self.sender_email}")
            return True
            
        except ImportError:
            self.log_error("Gmail dependencies not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False
        except Exception as e:
            self.log_error(f"Failed to initialize Gmail service: {e}")
            return False
    
    async def handle_send_email(self, message: MCPMessage) -> Dict[str, Any]:
        """Send an email through Gmail."""
        params = message.params
        
        # Extract email parameters
        to_email = params.get("to_email", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        cc_emails = params.get("cc_emails", [])
        bcc_emails = params.get("bcc_emails", [])
        attachments = params.get("attachments", [])
        
        if not to_email or not subject:
            return {
                "status": "error",
                "message": "Missing required fields: to_email and subject",
                "agent": self.agent_id
            }
        
        # Initialize Gmail service if needed
        if not self.authenticated:
            if not await self.initialize_gmail_service():
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Gmail",
                    "agent": self.agent_id
                }
        
        try:
            # Create email message
            email_msg = MIMEMultipart()
            email_msg['to'] = to_email
            email_msg['subject'] = subject
            email_msg['from'] = self.sender_email
            
            if cc_emails:
                email_msg['cc'] = ', '.join(cc_emails)
            if bcc_emails:
                email_msg['bcc'] = ', '.join(bcc_emails)
            
            # Add body
            email_msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if any
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, "rb") as attachment_file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment_file.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment)}'
                    )
                    email_msg.attach(part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()
            
            # Send email
            send_result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.log_info(f"Email sent successfully to {to_email}")
            
            return {
                "status": "success",
                "message": f"Email sent successfully to {to_email}",
                "message_id": send_result.get('id'),
                "to_email": to_email,
                "subject": subject,
                "sent_at": datetime.now().isoformat(),
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.log_error(f"Failed to send email: {e}")
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "agent": self.agent_id
            }
    
    async def handle_read_emails(self, message: MCPMessage) -> Dict[str, Any]:
        """Read recent emails from Gmail."""
        params = message.params
        max_results = params.get("max_results", 10)
        query = params.get("query", "")
        
        # Initialize Gmail service if needed
        if not self.authenticated:
            if not await self.initialize_gmail_service():
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Gmail",
                    "agent": self.agent_id
                }
        
        try:
            # Get message list
            results = self.gmail_service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            email_list = []
            for msg in messages:
                # Get full message
                full_msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                # Extract email details
                headers = full_msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                # Get email body (simplified)
                body = ""
                if 'parts' in full_msg['payload']:
                    for part in full_msg['payload']['parts']:
                        if part['mimeType'] == 'text/plain':
                            if 'data' in part['body']:
                                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                break
                elif full_msg['payload']['mimeType'] == 'text/plain':
                    if 'data' in full_msg['payload']['body']:
                        body = base64.urlsafe_b64decode(full_msg['payload']['body']['data']).decode('utf-8')
                
                email_list.append({
                    "id": msg['id'],
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "body_preview": body[:200] + "..." if len(body) > 200 else body
                })
            
            return {
                "status": "success",
                "emails": email_list,
                "total_found": len(email_list),
                "query_used": query,
                "agent": self.agent_id
            }
            
        except Exception as e:
            self.log_error(f"Failed to read emails: {e}")
            return {
                "status": "error",
                "message": f"Failed to read emails: {str(e)}",
                "agent": self.agent_id
            }
    
    async def handle_search_emails(self, message: MCPMessage) -> Dict[str, Any]:
        """Search emails with specific criteria."""
        params = message.params
        search_query = params.get("search_query", "")
        max_results = params.get("max_results", 10)
        
        if not search_query:
            return {
                "status": "error",
                "message": "Search query is required",
                "agent": self.agent_id
            }
        
        # Use read_emails with search query
        search_params = MCPMessage(
            method="read_emails",
            params={
                "query": search_query,
                "max_results": max_results
            }
        )
        
        return await self.handle_read_emails(search_params)
    
    async def handle_get_email_status(self, message: MCPMessage) -> Dict[str, Any]:
        """Get Gmail service status and account info."""
        if not self.authenticated:
            await self.initialize_gmail_service()
        
        return {
            "status": "success",
            "authenticated": self.authenticated,
            "sender_email": self.sender_email,
            "service_available": self.gmail_service is not None,
            "agent": self.agent_id
        }

if __name__ == "__main__":
    # Test the Gmail agent
    print("📧 Testing Gmail Agent")
    print("=" * 40)
    
    agent = GmailAgent()
    print(f"Created agent: {agent}")
    print(f"Capabilities: {[cap.name for cap in agent.capabilities]}")
    print(f"Methods: {list(agent.message_handlers.keys())}")
    
    print("\n✅ Gmail agent ready!")
    print("🎯 Perfect for sending and receiving emails!")
    print("\n📋 Setup required:")
    print("1. Install dependencies: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print("2. Get Gmail API credentials from Google Cloud Console")
    print("3. Save as credentials.json in project root")
    print("4. Run authentication flow on first use")
