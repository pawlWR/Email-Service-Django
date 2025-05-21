from django.db import models
import smtplib
import imaplib

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
# Create your models here.
class DummyEmailConfiguration(TimeStampedModel):
    email_address = models.EmailField()
    # Shared credentials
    email_username = models.CharField(max_length=255)
    email_password = models.CharField(max_length=255)  # Encrypt in production
    # SMTP settings
    smtp_server = models.CharField(max_length=255)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    # IMAP settings
    imap_server = models.CharField(max_length=255)
    imap_port = models.PositiveIntegerField(default=993)
    imap_use_ssl = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    daily_limit = models.PositiveIntegerField(default=100)
    daily_sent = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Email Config ({self.email_address})"
    
    def check_connection(self):
        """
        Checks both SMTP and IMAP connections.
        Returns True if both connections succeed, otherwise False.
        """
        smtp_status = False
        imap_status = False

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            if self.smtp_use_tls:
                server.starttls()
            server.login(self.email_username, self.email_password)
            server.quit()
            smtp_status = True
        except Exception:
            smtp_status = False

        try:
            if self.imap_use_ssl:
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_server, self.imap_port)
            mail.login(self.email_username, self.email_password)
            mail.logout()
            imap_status = True
        except Exception:
            imap_status = False

        return smtp_status and imap_status


class DummyEmailTemplate(TimeStampedModel):
    subject = models.CharField(max_length=1000)
    body = models.TextField()

    def __str__(self):
        return f"Template: {self.subject}"
    
class EmailLog(TimeStampedModel):
    email_configuration = models.ForeignKey(DummyEmailConfiguration, on_delete=models.CASCADE)
    recipient = models.EmailField()
    status = models.CharField(max_length=50, choices=[('valid', 'Valid'), ('invalid', 'Invalid')])
    checked_at = models.DateTimeField()
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Email to {self.recipient} - Status: {self.status}"