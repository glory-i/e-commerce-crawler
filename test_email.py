"""
Test email configuration
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_email_config():
    """Check if email is configured"""
    print("Checking email configuration...\n")
    
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    alert_email = os.getenv('ALERT_EMAIL')
    
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"SMTP Username: {smtp_username}")
    print(f"SMTP Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    print(f"Alert Email: {alert_email}")
    print()
    
    if not smtp_username or not smtp_password or not alert_email:
        print("ERROR: Email configuration incomplete!")
        print("\nPlease update your .env file with:")
        print("  SMTP_USERNAME=your_email@gmail.com")
        print("  SMTP_PASSWORD=your_app_password")
        print("  ALERT_EMAIL=recipient@example.com")
        print("\nFor Gmail, you need an App Password:")
        print("  1. Go to Google Account settings")
        print("  2. Security -> 2-Step Verification")
        print("  3. App passwords -> Generate new password")
        print("  4. Use that password (not your regular password)")
        return False
    
    return True


def send_test_email():
    """Send a test email"""
    from notifications.email_notifier import test_email_configuration
    
    print("Sending test email...\n")
    
    try:
        success = test_email_configuration()
        
        if success:
            print("\nSUCCESS! Test email sent.")
            print(f"Check your inbox at: {os.getenv('ALERT_EMAIL')}")
            print("\nIf you don't see it:")
            print("  1. Check spam/junk folder")
            print("  2. Wait a few minutes (email can be delayed)")
            print("  3. Verify SMTP credentials in .env")
        else:
            print("\nFAILED! Could not send test email.")
            print("Check the error messages above.")
            
        return success
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nCommon issues:")
        print("  - Wrong SMTP username/password")
        print("  - Not using App Password (for Gmail)")
        print("  - Firewall blocking SMTP port 587")
        print("  - Invalid email addresses")
        return False


if __name__ == "__main__":
    print("="*60)
    print("EMAIL CONFIGURATION TEST")
    print("="*60)
    print()
    
    # Check configuration
    if not check_email_config():
        sys.exit(1)
    
    # Send test email
    success = send_test_email()
    
    print()
    print("="*60)
    
    if success:
        print("EMAIL TEST PASSED")
    else:
        print("EMAIL TEST FAILED")
    
    print("="*60)
    
    sys.exit(0 if success else 1)