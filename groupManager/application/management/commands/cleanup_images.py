from django.core.management.base import BaseCommand
from application.models import User
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Clean up unused profile images'

    def handle(self, *args, **kwargs):
        total_deleted = 0
        profile_dir = os.path.join(settings.MEDIA_ROOT, 'profile')

        # Проверяем наличие папки с изображениями
        if not os.path.exists(profile_dir):
            self.stdout.write(self.style.WARNING('Profile directory does not exist.'))
            return

        # Получаем все файлы в папке
        for filename in os.listdir(profile_dir):
            file_path = os.path.join(profile_dir, filename)
            db_file = "profile/" + filename

            # Проверяем наличие записи в базе данных
            if not User.objects.filter(image=db_file).exists():
                try:
                    os.remove(file_path)  # Удаляем файл, если запись не найдена
                    total_deleted += 1
                    self.stdout.write(self.style.SUCCESS(f'Deleted {filename}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error deleting {filename}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Unused images deleted: {total_deleted}'))