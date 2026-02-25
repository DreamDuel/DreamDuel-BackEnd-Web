"""Email service using AWS SES"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Optional, Dict, Any

from app.core.config import settings
from app.core.exceptions import EmailException


class SESEmailService:
    """Service for sending emails via AWS SES"""
    
    def __init__(self):
        ses_region = settings.AWS_SES_REGION or settings.AWS_REGION
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=ses_region
        )
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        html: str,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via AWS SES
        
        Args:
            to: List of recipient emails
            subject: Email subject
            html: HTML email content
            from_email: Sender email (default: settings.FROM_EMAIL)
            reply_to: Reply-to email
            tags: Email tags for tracking (converted to SES tags)
            
        Returns:
            SES response
        """
        try:
            sender = from_email or settings.FROM_EMAIL
            
            # Build email message
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': html, 'Charset': 'UTF-8'}}
            }
            
            # Send email
            kwargs = {
                'Source': sender,
                'Destination': {'ToAddresses': to},
                'Message': message,
            }
            
            if reply_to:
                kwargs['ReplyToAddresses'] = [reply_to]
            
            # SES tags (different format than Resend)
            if tags:
                kwargs['Tags'] = [
                    {'Name': tag.get('name', 'tag'), 'Value': tag.get('value', '')}
                    for tag in tags
                ]
            
            response = self.ses_client.send_email(**kwargs)
            
            return {
                'message_id': response['MessageId'],
                'status': 'sent'
            }
            
        except ClientError as e:
            raise EmailException(f"SES failed to send email: {str(e)}")
        except Exception as e:
            raise EmailException(f"Failed to send email: {str(e)}")
    
    def send_verification_email(self, to: str, username: str, verification_token: str) -> Dict[str, Any]:
        """Send email verification email"""
        verification_url = f"https://dreamduel.com/verify-email?token={verification_token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email - DreamDuel</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">DreamDuel</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2>Welcome to DreamDuel, {username}!</h2>
                <p>Thanks for signing up. Please verify your email address to get started.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Verify Email
                    </a>
                </div>
                <p style="color: #6c757d; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{verification_url}" style="color: #667eea;">{verification_url}</a>
                </p>
                <p style="color: #6c757d; font-size: 14px; margin-top: 30px;">
                    This link will expire in 7 days. If you didn't create an account, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to],
            subject="Verify your DreamDuel account",
            html=html,
            tags=[{"name": "type", "value": "verification"}]
        )
    
    def send_password_reset_email(self, to: str, username: str, reset_token: str) -> Dict[str, Any]:
        """Send password reset email"""
        reset_url = f"https://dreamduel.com/reset-password?token={reset_token}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password - DreamDuel</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">DreamDuel</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2>Password Reset Request</h2>
                <p>Hello {username},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #6c757d; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{reset_url}" style="color: #667eea;">{reset_url}</a>
                </p>
                <p style="color: #6c757d; font-size: 14px; margin-top: 30px;">
                    This link will expire in 24 hours. If you didn't request a password reset, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to],
            subject="Reset your DreamDuel password",
            html=html,
            tags=[{"name": "type", "value": "password_reset"}]
        )
    
    def send_welcome_email(self, to: str, username: str) -> Dict[str, Any]:
        """Send welcome email after successful verification"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to DreamDuel!</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🎉 Welcome to DreamDuel!</h1>
            </div>
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2>Hi {username}!</h2>
                <p>Your account is now verified and ready to use. You're all set to start creating amazing AI-powered images!</p>
                <h3>What you can do with your free account:</h3>
                <ul>
                    <li>✨ Generate 10 AI images per month</li>
                    <li>❤️ Like and save your favorite images</li>
                    <li>💬 Follow and connect with other creators</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://dreamduel.com/generate" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Generate Your First Image
                    </a>
                </div>
                <p style="color: #6c757d; font-size: 14px;">
                    Need help getting started? Visit our <a href="https://dreamduel.com/guide" style="color: #667eea;">Quick Start Guide</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to],
            subject="Welcome to DreamDuel! 🎉",
            html=html,
            tags=[{"name": "type", "value": "welcome"}]
        )


# Singleton instance
email_service = SESEmailService()

