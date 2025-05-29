#!/usr/bin/env python3
"""
Simple Email Sender - Backup method for sending emails
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_health_update_email():
    """Send health update email with manual credentials."""
    print("📧 SIMPLE EMAIL SENDER")
    print("=" * 50)
    
    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Email details
    from_email = "shreechandan1498@gmail.com"
    to_email = "shreekumarchandancharchit@gmail.com"
    subject = "Health Update - Returning to Work"
    
    # Email content
    body = """Dear Team,

I hope this email finds you well.

I wanted to update you that I am feeling much better now and will be able to return to work from Monday onwards.

Thank you for your understanding during my absence. I look forward to getting back to work and contributing to our projects.

Best regards,
Shree Chandan

---
Sent via MCP Automated System
""" + datetime.now().strftime("Date: %Y-%m-%d %H:%M:%S")
    
    print(f"📧 From: {from_email}")
    print(f"📧 To: {to_email}")
    print(f"📝 Subject: {subject}")
    print()
    
    # Get app password from user
    print("🔑 GMAIL APP PASSWORD NEEDED:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Generate new app password for 'Mail'")
    print("3. Enter the 16-character password below")
    print()
    
    app_password = input("Enter Gmail app password (16 chars): ").strip()
    
    if len(app_password) != 16:
        print("❌ App password should be 16 characters")
        print("💡 Format: xxxxxxxxxxxx (no spaces)")
        return False
    
    try:
        print("\n📤 Sending email...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, app_password)
        
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("🎉 EMAIL SENT SUCCESSFULLY!")
        print(f"✅ Health update sent to {to_email}")
        print("📧 The recipient will receive your message shortly")
        print("💼 You can return to work from Monday as planned")
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed")
        print("🔧 Check your app password")
        print("💡 Make sure 2FA is enabled on your Google account")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def show_manual_email_template():
    """Show manual email template."""
    print("\n📝 MANUAL EMAIL TEMPLATE")
    print("=" * 50)
    print("If automated sending fails, copy this template:")
    print()
    print("To: shreekumarchandancharchit@gmail.com")
    print("Subject: Health Update - Returning to Work")
    print()
    print("Dear Team,")
    print()
    print("I hope this email finds you well.")
    print()
    print("I wanted to update you that I am feeling much better now and will be")
    print("able to return to work from Monday onwards.")
    print()
    print("Thank you for your understanding during my absence. I look forward to")
    print("getting back to work and contributing to our projects.")
    print()
    print("Best regards,")
    print("Shree Chandan")
    print()
    print("=" * 50)
    print("📧 Send this from: shreechandan1498@gmail.com")
    print("📧 Send this to: shreekumarchandancharchit@gmail.com")

def main():
    """Main function."""
    print("📧 HEALTH UPDATE EMAIL SENDER")
    print("=" * 80)
    print("🎯 Sending return-to-work notification")
    print("📧 From: shreechandan1498@gmail.com")
    print("📧 To: shreekumarchandancharchit@gmail.com")
    print("=" * 80)
    
    print("\n💡 CHOOSE SENDING METHOD:")
    print("1. Automated sending (requires app password)")
    print("2. Show manual email template")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = send_health_update_email()
        if not success:
            print("\n🔧 Automated sending failed. Showing manual template...")
            show_manual_email_template()
    elif choice == "2":
        show_manual_email_template()
    else:
        print("❌ Invalid choice")
        show_manual_email_template()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Email sending cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n📝 Manual email template:")
        show_manual_email_template()
