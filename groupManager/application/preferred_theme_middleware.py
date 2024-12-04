from django.utils.deprecation import MiddlewareMixin
from .models import User


class PreferredThemeMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):
        if "userID" in request.session:
            # Получаем пользователя из базы данных
            user = User.objects.get(userID=request.session["userID"])
            # Обновляем значение preferredTheme в сессии
            request.session['preferredTheme'] = user.preferredTheme

        preferred_theme = 0
        if "preferredTheme" in request.session:
            preferred_theme = request.session["preferredTheme"]

        # Добавляем preferredTheme в контекст
        if response.context_data is not None:
            response.context_data['preferredTheme'] = preferred_theme

        return response