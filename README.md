# Quask Manager

Приложение для управления очередями и заданиями в учебной группе.

Идеально подойдет для студентов, которые устали от того, что их преподаватель успевает проверять не всех, а очередь постоянно занимается одними и теми же людьми. Теперь они смогут перенести ее на следующую пару!

## Установка и настройка

1. Перейдите в папку, где вы хотите расположить репозиторий.
2. В терминале пропишите ```git init```
1. Склонируйте репозиторий: ```git clone git@github.com:dmitryh2004/QuaskManager.git```
1. Создайте виртуальную среду: ```python -m venv .venv```;
2. Активируйте ее в зависимости от вашей ОС;
2. Установите необходимые пакеты: в виртуальной среде пропишите команды ```pip install Django```, ```pip install djangorestframework```;
3. Перейдите в папку groupManager: ```cd groupManager```;
4. Запустите сервер: ```python manage.py runserver [port]```. При необходимости укажите порт, на котором будет открыт сервер.

## Функционал

Приложение предоставляет следующий функционал:

- Регистрация и авторизация;
- Управление очередями: запись, выход, обмен местами, прохождение очереди;
- Управление заданиями: бронирование, отказ и выполнение;
- Работа с расписанием группы: просмотр, редактирование расписания старостой;
- Работа с новостями: просмотр новостей, выпуск новостей администраторами и старостами;

Приложение имеет проработанную ролевую систему, включающую 5 ролей:

- Пользователь: роль по умолчанию, доступен базовый функционал;
- Модератор: имеет полномочия пользователя, также доступно управление очередями и заданиями;
- Староста: имеет полномочия модератора, доступны изменение расписания, выпуск новостей, назначение ролей внутри группы. Может поменяться ролями с одним из модераторов;
- Администратор: может выдавать роли пользователям и взаимодействовать с базой данных;
- Главный администратор: имеет полномочия администратора, может назначать администраторов. Может поменяться ролями с одним из администраторов.

## Использованные технологии

В проекте был использован фреймворк Django. Также было реализовано API для взаимодействия с внешними приложениями.

Для реализации клиентской части использовались HTML5, CSS3 и Javascript 9.

Также была использована библиотека *tinymce* для реализации WYSIWYG редактора новостей.