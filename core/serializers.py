from rest_framework import serializers
from core.models import EmailLog, DummyEmailConfiguration, DummyEmailTemplate


class EmailLogSerializer(serializers.ModelSerializer):
    recipient_email = serializers.EmailField(source='recipient')

    class Meta:
        model = EmailLog
        fields = ['id', 'recipient_email', 'status', 'checked_at']


class SendEmailSerializer(serializers.Serializer):
    recipient_email = serializers.EmailField()
