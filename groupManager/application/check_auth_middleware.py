from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from datetime import timedelta
from .models import Authorize, User


class SessionTokenMiddleware(MiddlewareMixin):
    excluded_paths = ['/login', "/logout", "/authorize", "/signup", "/register", '/recover', "/profile/change_password"]

    def process_request(self, request):
        if request.path in self.excluded_paths:
            return None

        user_id = request.session.get('userID')
        if user_id:
            try:
                user = User.objects.get(userID=user_id)
                auth = Authorize.objects.get(user=user)

                # Проверка токена сессии
                if auth.session_token != request.session.get('session_token'):
                    request.session.flush()  # Удаляем сессию, если токены не совпадают

                # Проверка даты последнего входа
                if auth.last_login and (timezone.now() - auth.last_login) > timedelta(weeks=1):
                    request.session.flush()  # Удаляем сессию, если последний вход был более недели

            except Authorize.DoesNotExist:
                request.session.flush()  # Удаляем сессию, если пользователь не найден