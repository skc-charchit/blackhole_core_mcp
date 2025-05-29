#!/usr/bin/env python3
"""
Direct Email Sending Script
Send email directly using the Gmail agent
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append('.')

async def send_email_direct():
    """Send email directly using Gmail agent."""
    print("📧 SENDING EMAIL DIRECTLY")
    print("=" * 50)
    
    try:
        # Import the Gmail agent
        from agents.communication.real_gmail_agent import RealGmailAgent
        from agents.base_agent import MCPMessage
        
        # Create Gmail agent
        gmail_agent = RealGmailAgent()
        print("✅ Gmail agent created successfully")
        
        # Email details
        to_email = "shreekumarchandancharchit@gmail.com"
        subject = "Health Update - Returning to Work"
        content = """Dear Team,

I hope this email finds you well.

I wanted to update you that I am feeling much better now and will be able to return to work from Monday onwards.

Thank you for your understanding during my absence. I look forward to getting back to work and contributing to our projects.

Best regards,
Shree Chandan"""
        
        print(f"📧 To: {to_email}")
        print(f"📝 Subject: {subject}")
        print(f"💌 Content preview: {content[:100]}...")
        print()
        
        # Create email message
        email_message = MCPMessage(
            id=f"email_{datetime.now().timestamp()}",
            method="send_email",
            params={
                "to_email": to_email,
                "subject": subject,
                "content": content,
                "template": "general_analysis"
            },
            timestamp=datetime.now()
        )
        
        print("📤 Sending email...")
        
        # Send email
        result = await gmail_agent.process_message(email_message)
        
        print("📊 RESULT:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Email sent: {result.get('email_sent', False)}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        if result.get('email_sent'):
            print("\n🎉 EMAIL SENT SUCCESSFULLY!")
            print(f"✅ Your email has been sent to {to_email}")
            print("📧 The recipient will receive your health update message")
        else:
            print("\n⚠️ Email processed but may be in demo mode")
            print("🔧 Check Gmail credentials and SMTP settings")
            
            # Show demo mode info if applicable
            if result.get('demo_mode'):
                print("📝 Demo mode detected - email simulated")
            
        return result.get('email_sent', False)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Gmail agent may not be properly configured")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def check_gmail_config():
    """Check Gmail configuration."""
    print("🔍 CHECKING GMAIL CONFIGURATION")
    print("=" * 50)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    gmail_email = os.getenv('GMAIL_EMAIL', '').strip()
    gmail_password = os.getenv('GMAIL_APP_PASSWORD', '').strip()
    
    print(f"📧 Gmail Email: {gmail_email}")
    print(f"🔑 App Password: {'*' * len(gmail_password)} ({len(gmail_password)} chars)")
    
    if gmail_email and gmail_password:
        if gmail_email != 'your-email@gmail.com' and gmail_password != 'your-app-password':
            print("✅ Real Gmail credentials configured!")
            return True
        else:
            print("⚠️ Using placeholder credentials")
            return False
    else:
        print("❌ Gmail credentials not found")
        return False

def test_smtp_connection():
    """Test SMTP connection."""
    print("\n🔌 TESTING SMTP CONNECTION")
    print("=" * 50)
    
    try:
        import smtplib
        from dotenv import load_dotenv
        load_dotenv()
        
        gmail_email = os.getenv('GMAIL_EMAIL', '').strip()
        gmail_password = os.getenv('GMAIL_APP_PASSWORD', '').strip()
        
        if not gmail_email or not gmail_password:
            print("❌ Gmail credentials not found")
            return False
        
        print("🔌 Connecting to Gmail SMTP...")
        
        # Test SMTP connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_email, gmail_password)
        server.quit()
        
        print("✅ SMTP connection successful!")
        print("🎉 Gmail is ready to send emails!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP Authentication failed")
        print("🔧 Check your Gmail app password")
        return False
    except Exception as e:
        print(f"❌ SMTP connection error: {e}")
        return False

async def main():
    """Main function."""
    print("📧 DIRECT EMAIL SENDER")
    print("=" * 80)
    print("🎯 Sending health update to shreekumarchandancharchit@gmail.com")
    print("=" * 80)
    
    # Check Gmail configuration
    config_ok = check_gmail_config()
    
    if not config_ok:
        print("\n❌ Gmail configuration issues detected")
        return False
    
    # Test SMTP connection
    smtp_ok = test_smtp_connection()
    
    if not smtp_ok:
        print("\n❌ SMTP connection failed")
        return False
    
    # Send email
    email_sent = await send_email_direct()
    
    if email_sent:
        print("\n🎉 SUCCESS!")
        print("✅ Your health update email has been sent!")
        print("📧 shreekumarchandancharchit@gmail.com will receive your message")
        print("💼 You can return to work from Monday as planned")
    else:
        print("\n🔧 Email sending needs attention")
        print("💡 Check the error messages above")
    
    return email_sent

if __name__ == "__main__":
    import asyncio
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n🎉 Email sent successfully!")
        else:
            print("\n🔧 Email sending failed. Check configuration.")
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        print("💡 Make sure all dependencies are installed")
