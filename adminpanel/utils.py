
from core.models import Notification, UserSetting
from core.utils import send_notification


def send_tip_notification(tip_text):
    body = "Fun Fact!"
    title = f"Hey there! We have a fun fact for you. Check out now. ... {tip_text[:100]}"

    user_settings = UserSetting.objects.all()
    for setting in user_settings:
        registration_id = setting.device_token

        # Notification.objects.create(
        #         user=setting.user, notification_type=notification_type, head=head, body=body
        #     )
        if registration_id:
            send_notification(
                registration_id=registration_id,
                message_title=title,
                message_body=body,
                notification_type="Tip"
            )
