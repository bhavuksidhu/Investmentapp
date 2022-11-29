import os
from django.conf import settings
from datetime import datetime


def question_files_upload_dir(question, filename, ):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'question_files/{0}/{1}'.format(question.quiz.pk, filename)


def prize_images_dir(prize, filename, ):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'prize_images/{0}/{1}'.format(prize.quiz.pk, filename)


def save_file(file, quiz, media_dir):
    print(f"saving {file.name} for quiz {quiz.name}")
    file_dir = os.path.join(settings.MEDIA_ROOT, media_dir, f"{quiz.pk}")

    if not os.path.exists(file_dir):
        try:
            os.mkdir(file_dir)
        except Exception as exc:
            raise Exception(f"Failed creating directory: {exc}")
    file_path = os.path.join(file_dir, file.name)

    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return file_path


def name_prefix(index):
    if index == 0:
        return "first_prize"
    elif index == 1:
        return "second_prize"
    elif index == 2:
        return "third_prize"
    else:
        return None

def ensure_datetime(d):
    """
    Takes a date or a datetime as input, outputs a datetime
    """
    if isinstance(d, datetime):
        return d
    return datetime(year=d.year, month=d.month, day=d.day)


def datetime_cmp(d1, d2):
    """
    Compares two timestamps.  Tolerates dates.
    """
    return ensure_datetime(d1) < ensure_datetime(d2)