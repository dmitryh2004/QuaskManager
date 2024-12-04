import uuid
import io

from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone

from django_resized import ResizedImageField
from PIL import Image, ImageSequence
from django.core.files.base import ContentFile


"""def crop_and_scale_gif(input_gif, name, size=(256, 256)):
    # Открываем исходный GIF файл
    original_gif = Image.open(input_gif)

    # Список для хранения кадров
    frames = []

    for frame in ImageSequence.Iterator(original_gif):
        orig_size = frame.size

        # scale = max(size[0] / orig_size[0], size[1] / orig_size[1])
        # frame.resize((int(orig_size[0] * scale), int(orig_size[1] * scale)), Image.Resampling.BICUBIC)

        # Масштабируем кадр с сохранением пропорций
        frame.thumbnail((size[0], size[1]), Image.Resampling.BICUBIC)

        # Определяем размеры нового кадра после масштабирования
        width, height = frame.size

        # Рассчитываем координаты для обрезки по центру
        left = (width - size[0]) / 2
        top = (height - size[1]) / 2
        right = (width + size[0]) / 2
        bottom = (height + size[1]) / 2

        # Обрезаем кадр по центру
        cropped_frame = frame.crop((left, top, right, bottom))

        # Добавляем кадр в список
        frames.append(cropped_frame)

    # Сохраняем обрезанные кадры в новый GIF файл в памяти
    output_io = io.BytesIO()
    frames[0].save(output_io, format='GIF', save_all=True, append_images=frames[1:],
                   duration=original_gif.info['duration'] if 'duration' in original_gif.info else 0.0, loop=0)

    # Возвращаем содержимое как ContentFile для сохранения в модели Django
    return ContentFile(output_io.getvalue(), name=name)
"""

class UserRole(models.Model):
    userRoleID = models.AutoField(primary_key=True, unique=True)
    name = models.TextField()
    priority = models.IntegerField()
    isAdmin = models.BooleanField()
    desc = models.TextField()


class Group(models.Model):
    groupID = models.AutoField(primary_key=True, unique=True)
    name = models.TextField()


class User(models.Model):
    userID = models.AutoField(primary_key=True, unique=True)
    username = models.TextField()
    role = models.ForeignKey(UserRole, on_delete=models.PROTECT, default=None, null=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, default=None, null=True)
    preferredTheme = models.IntegerField()
    image = ResizedImageField(null=True, size=[256, 256], crop=['middle', 'center'], upload_to='profile/')

    def get_image(self):
        if self.image == "":
            return None
        if default_storage.exists(self.image.name):
            return self.image.url
        else:
            return None


class Authorize(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, default=None)
    email = models.TextField()
    password_hash = models.TextField()
    session_token = models.TextField(default=uuid.uuid4, editable=False)
    last_login = models.DateTimeField(null=True, blank=True)
    online = models.BooleanField(default=False)
    last_ping = models.DateTimeField(null=True, blank=True)

    def update_last_login(self):
        self.last_login = timezone.localtime(timezone.now())  # Обновляем дату последнего входа
        self.save()

    def update_last_ping(self):
        self.last_ping = timezone.now()
        self.online = True
        self.save()

    def check_online_status(self):
        if self.last_ping and (timezone.now() - self.last_ping).total_seconds() < 10:
            self.online = True
        else:
            self.online = False
        self.save()


class Campus(models.Model):
    campusID = models.AutoField(primary_key=True, unique=True)
    name = models.TextField()
    address = models.TextField()


class Auditory(models.Model):
    auditoryID = models.AutoField(primary_key=True, unique=True)
    campus = models.ForeignKey(Campus, on_delete=models.PROTECT, default=None)
    name = models.TextField()


class PairType(models.Model):
    pairTypeID = models.AutoField(primary_key=True, unique=True)
    name = models.TextField()
    name_short = models.TextField()


class Subject(models.Model):
    subjectID = models.AutoField(primary_key=True, unique=True)
    name = models.TextField()


class QueueList(models.Model):
    queueID = models.AutoField(primary_key=True, unique=True)
    title = models.TextField(null=True, default=None)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, default=None)
    type = models.IntegerField()
    active = models.BooleanField(default=False)
    timeout = models.IntegerField(default=30)


class Queue(models.Model):
    queue = models.ForeignKey(QueueList, on_delete=models.CASCADE, default=None)
    order = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)
    orderStatus = models.IntegerField()  # 0 - в очереди, 1 - решает, 2 - отвечает, 3 - уже ответил/пропустил
    token = models.TextField(default=uuid.uuid4, editable=False)


class Task(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, default=None)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, default=None)
    taskName = models.TextField()
    state = models.IntegerField()


class Schedule(models.Model):
    week = models.IntegerField()
    weekday = models.IntegerField()
    pairNumber = models.IntegerField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    auditory = models.ForeignKey(Auditory, on_delete=models.CASCADE, default=None)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, default=None)
    pairType = models.ForeignKey(PairType, on_delete=models.PROTECT, default=None)

    class Meta:
        unique_together = (("week", "weekday", "pairNumber", "group"),)

    def __str__(self):
        return f"{self.week}, {self.weekday}, {self.pairNumber}, {self.group.groupID}"


class Notification(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, related_name="sent_notifications")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, related_name="received_notifications")
    type = models.IntegerField()
    date = models.DateTimeField()
    text = models.TextField()
    seen = models.BooleanField()


class News(models.Model):
    title = models.CharField(max_length=200)
    shortdesc = models.TextField()
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group)
    created_at = models.DateTimeField(auto_now_add=True)
