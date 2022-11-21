from django.conf import settings
from pyfcm import FCMNotification

FCM_SERVER_KEY = settings.FCM_SERVER_KEY
push_service = FCMNotification(api_key=FCM_SERVER_KEY)

def send_notification(registration_id,message_title,message_body,notification_type="Normal"):
    push_service.notify_single_device(registration_id,message_title,message_body,data_message={"type":notification_type})
