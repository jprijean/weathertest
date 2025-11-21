"""
Test script to verify email sending functionality.

This script checks if email configuration is set up correctly
and attempts to send a test email.
"""

import os
from dotenv import load_dotenv
from email_service import EmailService
from models import Intervention, Database

# Load environment variables
load_dotenv()

def test_email_configuration():
    """Check if email is configured and test sending."""
    
    print("=" * 60)
    print("Email Configuration Test")
    print("=" * 60)
    
    # Check configuration
    use_resend = os.getenv("USE_RESEND", "false").lower() == "true"
    sender_email = os.getenv("SENDER_EMAIL")
    
    if not sender_email:
        print("\n[ERROR] SENDER_EMAIL is not configured in .env file")
        print("\nTo configure email, add to your .env file:")
        print("\nOption 1: Using Resend API (Recommended)")
        print("  USE_RESEND=true")
        print("  RESEND_API_KEY=your_resend_api_key")
        print("  SENDER_EMAIL=your_verified_email@example.com")
        print("\nOption 2: Using SMTP")
        print("  USE_RESEND=false")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SENDER_EMAIL=your_email@gmail.com")
        print("  SENDER_PASSWORD=your_app_password")
        print("  SMTP_USE_TLS=true")
        return False
    
    print(f"\n[OK] SENDER_EMAIL is configured: {sender_email}")
    
    # Initialize email service
    email_service = None
    
    if use_resend:
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            print("\n❌ ERROR: USE_RESEND=true but RESEND_API_KEY is not set")
            return False
        
        print(f"[OK] Using Resend API")
        print(f"[OK] RESEND_API_KEY is configured")
        
        try:
            email_service = EmailService(
                sender_email=sender_email,
                use_resend=True,
                resend_api_key=resend_api_key
            )
            print("[OK] Email service initialized with Resend")
        except Exception as e:
            print(f"\n[ERROR] initializing Resend email service: {e}")
            return False
    else:
        smtp_host = os.getenv("SMTP_HOST")
        if not smtp_host:
            print("\n[ERROR] SMTP_HOST is not configured")
            return False
        
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_password = os.getenv("SENDER_PASSWORD")
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        print(f"[OK] Using SMTP")
        print(f"[OK] SMTP_HOST: {smtp_host}")
        print(f"[OK] SMTP_PORT: {smtp_port}")
        print(f"[OK] SMTP_USE_TLS: {use_tls}")
        
        if not sender_password:
            print("\n[WARNING] SENDER_PASSWORD is not set (may fail if authentication required)")
        else:
            print(f"[OK] SENDER_PASSWORD is configured")
        
        try:
            email_service = EmailService(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                sender_email=sender_email,
                sender_password=sender_password,
                use_tls=use_tls
            )
            print("[OK] Email service initialized with SMTP")
        except Exception as e:
            print(f"\n[ERROR] initializing SMTP email service: {e}")
            return False
    
    # Get test recipient email
    print("\n" + "=" * 60)
    print("Test Email Sending")
    print("=" * 60)
    
    # Try to get a recipient from locations.csv
    db = Database()
    locations = db.get_all_locations()
    
    test_recipient = None
    if locations:
        # Get first email from first location
        emails = db.get_location_emails(locations[0].building_code)
        if emails:
            test_recipient = emails[0].strip()
            print(f"\nUsing recipient from locations: {test_recipient}")
    
    if not test_recipient:
        # Ask user for test email
        test_recipient = input("\nEnter a test email address to send to: ").strip()
        if not test_recipient:
            print("[ERROR] No recipient email provided. Cannot test email sending.")
            return False
    
    # Create a test intervention
    test_intervention = Intervention(
        id="test_alert",
        title="Test Weather Alert",
        description="This is a test email to verify that the email sending functionality is working correctly. If you receive this email, the email service is configured properly."
    )
    
    print(f"\nSending test email to: {test_recipient}")
    print(f"Subject: Weather Alert: {test_intervention.title}")
    print("\nSending...")
    
    try:
        success = email_service.send_alert_email(test_recipient, test_intervention)
        
        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] Test email sent successfully!")
            print("=" * 60)
            print(f"\nPlease check the inbox of {test_recipient}")
            print("(Also check spam/junk folder if not found)")
            return True
        else:
            print("\n" + "=" * 60)
            print("[FAILED] Email sending returned False")
            print("=" * 60)
            print("\nCheck the error messages above for details.")
            return False
            
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[ERROR] Exception occurred while sending email")
        print("=" * 60)
        print(f"\nError details: {e}")
        print("\nCommon issues:")
        print("  - SMTP: Check credentials, firewall, or use App Password for Gmail")
        print("  - Resend: Verify API key and that sender email is verified")
        return False


if __name__ == "__main__":
    try:
        success = test_email_configuration()
        if success:
            print("\n[SUCCESS] Email service is working correctly!")
        else:
            print("\n[FAILED] Email service test failed. Please check configuration.")
            exit(1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

