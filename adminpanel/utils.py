
from core.models import UserSetting
from core.utils import send_notification


def send_tip_notification(tip_text):
    title = "Fun Fact!"
    body = f"Hey there! We have a fun fact for you. Check out now. ...({tip_text[:100]})"

    user_settings = UserSetting.objects.all()
    for setting in user_settings:
        registration_id = setting.device_token

        if registration_id:
            send_notification(
                registration_id=registration_id,
                message_title=title,
                message_body=body,
            )
