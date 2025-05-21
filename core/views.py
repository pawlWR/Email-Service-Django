from django.shortcuts import render
from .models import DummyEmailTemplate, DummyEmailConfiguration, EmailLog
import random
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from django.utils import timezone
import time
import imaplib
import email
import smtplib
import threading
from .serializers import EmailLogSerializer, SendEmailSerializer
from email.mime.text import MIMEText
from .permissions import HasValidAPIKey
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
# Create your views here.

def get_random_template():
    templates  = DummyEmailTemplate.objects.all()
    if templates.exists():
        return random.choice(templates)
    return None

def get_random_email_configuration():
    configurations = DummyEmailConfiguration.objects.filter(is_active=True)
    config_list = []
    for config in configurations:
        if config.check_connection():
            config_list.append(config)
    if config_list:
        return random.choice(config_list)
    return None

def check_bounce_and_log(config_id, recipient_email):
    config = DummyEmailConfiguration.objects.get(id=config_id)

    # Wait for a random delay between 5-7 minutes
    time.sleep(random.randint(5, 10))

    bounce_detected = False
    imap = None

    try:
        if config.imap_use_ssl:
            imap = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
        else:
            imap = imaplib.IMAP4(config.imap_server, config.imap_port)

        imap.login(config.email_username, config.email_password)
        imap.select("inbox")
        result, data = imap.search(None, '(ALL)')
        email_ids = data[0].split()
        latest_email_ids = email_ids[-100:] if len(email_ids) > 100 else email_ids

        for email_id in reversed(latest_email_ids):
            result, email_data = imap.fetch(email_id, '(RFC822)')
            raw_email = email_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors='ignore')
                    if recipient_email.lower() in body.lower():
                        bounce_detected = True
                        break
            if bounce_detected:
                break

    except Exception as e:
        bounce_detected = False
    finally:
        if imap:
            try:
                imap.logout()
            except:
                pass

    try:
        log_entry, created = EmailLog.objects.update_or_create(
            email_configuration=config,
            recipient=recipient_email,
            defaults={
                'status': 'invalid' if bounce_detected else 'valid',
                'checked_at': timezone.now()
            }
        )
    except Exception as e:
        print(f"Failed to update EmailLog: {e}")

class SendEmailView(generics.GenericAPIView):
    serializer_class = SendEmailSerializer
    permission_classes = [HasValidAPIKey]

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient_email = serializer.validated_data['recipient_email']

        if not recipient_email:
            return Response({"error": "Missing recipient_email"}, status=400)

        # Check if already sent
        email_log = EmailLog.objects.filter(recipient=recipient_email).first()
        if email_log:
            return Response({"mail_sent": True, "detail": "Email already sent."})

        # Get config and template
        config = get_random_email_configuration()
        if not config:
            return Response({"error": "No active email configuration found"}, status=404)

        template = get_random_template()
        if not template:
            return Response({"error": "Email template not found"}, status=404)

        # Prepare email
        msg = MIMEText(template.body)
        msg['Subject'] = template.subject
        msg['To'] = recipient_email
        msg['From'] = config.email_address

        # Send email
        try:
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                if config.smtp_use_tls:
                    server.starttls()
                server.login(config.email_username, config.email_password)
                server.sendmail(config.email_address, recipient_email, msg.as_string())

            # Update daily limit
            if config.daily_limit > config.daily_sent:
                config.daily_sent += 1
                config.save()

            threading.Thread(target=check_bounce_and_log, args=(config.id, recipient_email)).start()

            return Response({"mail_sent": True, "detail": "Email sent, bounce check scheduled."})

        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=500)
        
class TestConnectionView(generics.GenericAPIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_QUERY,
                description="DummyEmailConfiguration ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        config_id = request.query_params.get("id")
        if not config_id:
            return Response({"error": "Missing id"}, status=400)
        try:
            config = DummyEmailConfiguration.objects.get(id=config_id)
        except DummyEmailConfiguration.DoesNotExist:
            return Response({"error": "Configuration not found"}, status=404)

        # Test SMTP connection
        try:
            server = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=10)
            if config.smtp_use_tls:
                server.starttls()
            server.login(config.email_username, config.email_password)
            server.quit()
            smtp_status = True
        except Exception:
            smtp_status = False

        # Test IMAP connection
        try:
            if config.imap_use_ssl:
                mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                mail = imaplib.IMAP4(config.imap_server, config.imap_port)
            mail.login(config.email_username, config.email_password)
            mail.logout()
            imap_status = True
        except Exception:
            imap_status = False

        return Response({
            "smtp_status": smtp_status,
            "imap_status": imap_status,
            "connection_ok": smtp_status and imap_status
        })


class CheckStatusView(generics.RetrieveAPIView):
    serializer_class = EmailLogSerializer
    permission_classes = [HasValidAPIKey]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'recipient_email',
                openapi.IN_QUERY,
                description="Recipient email address",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        recipient_email = request.query_params.get("recipient_email")

        if not recipient_email:
            return Response({"error": "Missing recipient_email"}, status=400)

        try:
            log = EmailLog.objects.get(recipient=recipient_email)
            serializer = EmailLogSerializer(log)
            return Response(serializer.data, status=200)
        except EmailLog.DoesNotExist:
            return Response({"error": "Email log not found"}, status=404)