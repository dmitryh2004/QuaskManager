import math

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.response import Response

from .serializers import *

from .models import *

from .newsManagenent import *
from .scheduleManagement import *
from .notificationsManagement import *
from .queueManagement import *

import hashlib

import pytz

PAGE_SIZE = 10

timezone = pytz.timezone('Europe/Moscow')
permitted_tables_for_admins = ["auditory", "group", "subject", "campus"]  # разрешенные для админов таблицы

# тексты сообщений для уведомлений
role_changed = "Ваша роль была изменена на роль \"{role_name}\". Вы можете ознакомиться с ее описанием в профиле."
group_changed = "Ваша группа была изменена на группу \"{group_name}\"."
task_claimed = "Вы успешно взяли себе задание \"{task_name}\"."
task_unclaimed = "Вы успешно отказались от задания \"{task_name}\"."
task_deleted = "Задание \"{task_name}\" было удалено пользователем {deleter}."
task_completed = "Задание \"{task_name}\" было отмечено как выполненное."
task_uncompleted = "Задание \"{task_name}\" было отмечено как невыполненное."
queues_deleted = "Вы были удалены из всех очередей в группе \"{group_name}\"."


def sha256_hash(message):
    # Преобразуем сообщение в байты
    message = message.encode('utf-8')
    # Создаём объект хеша SHA-256
    sha256 = hashlib.sha256()
    # Обновляем объект хеша байтами сообщения
    sha256.update(message)
    # Получаем шестнадцатеричное представление хеша
    hash_code = sha256.hexdigest()
    # Возвращаем хеш-код
    return hash_code


def ping(request):
    userID = request.session["userID"]
    authorize_instance = Authorize.objects.get(user_id=userID)
    authorize_instance.update_last_ping()
    return JsonResponse({'status': 'success'})


def set_offline(request):
    userID = request.session["userID"]
    authorize_instance = Authorize.objects.get(user_id=userID)
    authorize_instance.online = False
    authorize_instance.save()
    return JsonResponse({})


"""def error_403(request, exception):
    return render(request, "403.html", status=403)


def error_404(request, exception):
    return TemplateResponse(request, "404.html")


def error_500(request):
    return TemplateResponse(request, "500.html")"""


def login(request):
    info = request.session.pop('info', '')
    error = request.session.pop('error', '')
    context = {"signup_link": reverse('signup'),
               "recover_link": reverse('recover'),
               "info": info,
               "error": error}

    return TemplateResponse(request, "login.html", context=context)


def authorize(request):
    email = request.POST.get('email', '')
    password = request.POST.get('password', '')

    hash = sha256_hash(password)

    accounts = Authorize.objects.filter(email=email)
    if not accounts.exists():
        request.session["error"] = "Неверная почта или пароль"
        return redirect("/login")

    for account in accounts:
        if account.password_hash != hash:
            request.session["error"] = "Неверная почта или пароль"
            return redirect("/login")
        else:
            request.session["userID"] = account.user_id
            users = User.objects.filter(userID=account.user_id)
            if not users.exists():
                request.session["error"] = "Ошибка: вашей почте не назначен ни один аккаунт. Обратитесь к администраторам для решения этой проблемы."
                return redirect("/login")

            account.session_token = str(uuid.uuid4())
            request.session['session_token'] = account.session_token
            account.update_last_login()
            for user in users:
                request.session["username"] = user.username
                return redirect("/")


def signup(request):
    context = {"login_link": reverse('login')}
    keys = ["name", "email", "password", "password_repeat", "error"]
    values = [request.session.pop(key, '') for key in keys]
    context.update({key: value for key, value in zip(keys, values)})

    group_list = []
    groups = Group.objects.all()

    for group in groups:
        group_list.append({
            "id": group.groupID,
            "name": group.name
        })

    context.update({"groups": group_list})
    return TemplateResponse(request, "signup.html", context=context)


def register(request):
    name = request.POST.get("name", "")
    email = request.POST.get("email", "")
    password = request.POST.get("password", "")
    password_repeat = request.POST.get("password_repeat", "")
    group = int(request.POST.get("group_select", 0))
    if group == 0:
        group = None

    if password != password_repeat:
        request.session["name"] = name
        request.session["email"] = email
        request.session["password"] = password
        request.session["password_repeat"] = password_repeat
        request.session["error"] = "Ошибка: пароли не совпадают"
        request.session["group_selected"] = group
        return redirect("/signup")
    else:
        if Authorize.objects.filter(email=email):
            request.session["name"] = name
            request.session["email"] = email
            request.session["password"] = password
            request.session["password_repeat"] = password_repeat
            request.session["error"] = "Ошибка: эта электронная почта уже используется"
            request.session["group_selected"] = group
            return redirect("/signup")

        hash = sha256_hash(password)
        userrole = UserRole.objects.get(userRoleID=1)

        user = User.objects.create(username=name, role=userrole, group_id=group, preferredTheme=0)
        Authorize.objects.create(user=user, email=email, password_hash=str(hash))

        request.session["info"] = "Новый пользователь зарегистрирован"
        return redirect("/login")


def recover(request):
    return TemplateResponse(request, "not-implemented.html", context={"title": "Восстановление пароля",
                                                                      "back_link": reverse('login')})


def index(request):
    # читаем информацию о текущем пользователе
    username = ""
    groupID = 0
    role = 0
    url = None
    theme = 0
    errors = dict()
    warnings = dict()
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]
    user = User.objects.filter(userID=userID)

    for user_ in user:
        username = user_.username
        groupID = user_.group_id if user_.group_id is not None else 0
        role = user_.role_id
        url = user_.get_image()

    # обработка ошибок
    if username == "":
        errors["profile"] = "Не удалось найти ваш ник. Обратитесь к администраторам для решения этой проблемы."

    if groupID == 0:
        if role > 3:
            warnings["no_group"] = "Ваш профиль не поддерживает установку группы, так как вы являетесь администратором."
        elif role == 3:
            errors["no_group"] = "В вашем профиле не установлена группа! Обратитесь к администратору для того, чтобы он добавил вас в вашу группу."
        else:
            errors["no_group"] = "В вашем профиле не установлена группа! Обратитесь к старосте или администратору для того, чтобы он добавил вас в свою группу."

    pairs = getPairs(groupID)

    new_notifications, _ = getNotifications(userID)

    context = {"about_link": reverse('about'),
               "schedule_link": reverse('schedule'),
               "pairs": pairs,
               "username": username,
               "warnings": warnings,
               "errors": errors,
               "role": role,
               "path": url,
               "notifications_count": len(new_notifications)}

    tasks = Task.objects.filter(user_id=userID, state=0).order_by("subject_id")
    task_list = []

    for task in tasks:
        task_list.append({
            "id": task.id,
            "name": task.taskName,
            "subject": task.subject.name
        })

    context.update({"tasks": task_list})

    context.update({"current_user_id": userID, "group_id": groupID})

    context.update({"queues": get_formatted_queues(userID)})

    if role >= 4:
        group_list = []
        groups = Group.objects.all()

        for group in groups:
            group_list.append({"id": group.groupID, "name": group.name})

        context.update({"groups": group_list})

    if groupID == 0:
        groupID = None

    news_list = readLastNews(groupID)
    context.update({"news": news_list})

    return TemplateResponse(request, "mainpage.html", context=context)


def count_notifications(request, uid):
    notifications_list, _ = getNotifications(uid)
    return JsonResponse({"notifications_count": len(notifications_list)})


def about(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]
    context = dict()

    users = User.objects.filter(userID=userID)

    for user in users:
        userrole = user.role_id

        roles = UserRole.objects.filter(userRoleID=userrole)

        for role in roles:
            context.update({"userroleID": role.userRoleID})
    return TemplateResponse(request, "about.html", context=context)


def about_guide(request, role):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "back_link": {
            "link": reverse("about"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)

        if user.role_id != role:
            return redirect("guide", user.role_id)
    except ObjectDoesNotExist:
        return redirect("about")

    return TemplateResponse(request, f"about-guide-{role}.html", context=context)


def news_show(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    user = User.objects.get(userID=userID)
    gid = user.group_id

    news_list = readLastNews(gid, -1)

    context["news_list"] = news_list
    context["one_news"] = False

    return TemplateResponse(request, "news-show.html", context=context)


def news_show_1(request, id):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    user = User.objects.get(userID=userID)
    gid = user.group_id

    news_instance = getNews(gid, id)

    if news_instance is None:
        context["error"] = f"Произошла ошибка при попытке прочитать новость с id={id}.<br>Возможные причины:<br>- новости с таким id не существует;<br>- новость недоступна для вашей группы."
    else:
        context["news"] = news_instance
        context["one_news"] = True

    return TemplateResponse(request, "news-show.html", context=context)


def schedule_index(request):
    return redirect("/schedule/view")


def schedule_view(request):
    # читаем информацию о текущем пользователе
    groupID = 0
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]
    user = User.objects.filter(userID=userID)

    for user_ in user:
        groupID = user_.group_id if user_.group_id is not None else 0

    group_select = request.POST.get("groupselect", 0)
    if group_select != 0:
        groupID = group_select

    return redirect("schedule-view-group", groupID)


def schedule_view_group(request, id):
    role = 0
    user_group = None
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]
    user = User.objects.filter(userID=userID)

    for user_ in user:
        role = user_.role_id
        user_group = user_.group_id

    groupname = ""
    error = None
    try:
        group = Group.objects.get(groupID=id)
        groupname = group.name
        if groupname == "":
            groupname = "not found"
    except ObjectDoesNotExist:
        error = f"Группа с ID={id} не найдена."

    scheduleTable = formScheduleTable(id)

    pairDuration = dict()
    for _ in range(1, 7):
        pairDuration[_] = [
            ScheduleConstants.get_pair_start(date=None, num=_).strftime("%H:%M"),
            ScheduleConstants.get_pair_end(date=None, num=_).strftime("%H:%M")
        ]

    days = {
        1: "пн",
        2: "вт",
        3: "ср",
        4: "чт",
        5: "пт",
        6: "сб"
    }

    context = {
        "about_link": reverse('about'),
        "back_link": {"link": reverse('home'), "text": "Назад"},
        "pairDuration": pairDuration,
        "schedule": scheduleTable,
        "groupname": groupname,
        "days": days,
        "role": role,
        "group": id,
        "user_group": user_group
    }

    if error is not None:
        context["error"] = error

    return TemplateResponse(request, "schedule-view.html", context=context)


def schedule_edit(request, gid, week, weekday, pair):
    role = 0
    user_group = None
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]
    user = User.objects.filter(userID=userID)

    for user_ in user:
        role = user_.role_id
        user_group = user_.group_id

    if role < 4:
        if role < 3 or user_group != gid:
            return HttpResponseForbidden()

    groupname = ""
    error = None
    try:
        group = Group.objects.get(groupID=gid)
        groupname = group.name
        if groupname == "":
            groupname = "not found"
    except ObjectDoesNotExist:
        error = f"Группа с ID={gid} не найдена."

    # получение вспомогательных объектов
    pairtypes_objects = PairType.objects.all()
    auditories_objects = Auditory.objects.all()
    campuses_objects = Campus.objects.all()
    subjects_objects = Subject.objects.all()

    pairtypes = dict()
    for pairtype in pairtypes_objects:
        pairtypes[pairtype.pairTypeID] = {
            "name": pairtype.name,
            "name_short": pairtype.name_short
        }

    campuses = dict()
    for campus in campuses_objects:
        campuses[campus.campusID] = {
            "name": campus.name,
            "address": campus.address
        }

    auditories = dict()
    for auditory in auditories_objects:
        auditories[auditory.auditoryID] = {
            "name": auditory.name,
            "campusID": auditory.campus_id
        }

    subjects = dict()
    for subject in subjects_objects:
        subjects[subject.subjectID] = {
            "name": subject.name
        }

    context = {
        "group": gid,
        "even": week,
        "weekday": weekday,
        "weekday_name": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"][weekday-1],
        "pairNumber": pair,
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("schedule-view-group", kwargs={"id": gid}),
            "text": "Назад"
        },
        "subjects": subjects,
        "pairTypes": pairtypes,
        "auditories": auditories,
        "campuses": campuses,
        "groupname": groupname
    }

    if error:
        context.update({"error": error})

    # чтение расписания
    scheduleTable = getScheduleTable(getSchedule(gid))
    if scheduleTable[week][weekday][pair] != dict():
        context.update(scheduleTable[week][weekday][pair])

    return TemplateResponse(request, "schedule-edit.html", context=context)


def schedule_update(request, gid, week, weekday, pair):
    new_subject = request.POST.get("subject", 0)
    new_auditory = request.POST.get("auditory", 0)
    new_pairType = request.POST.get("pairType", 0)

    try:
        entry = Schedule.objects.get(
            group_id=gid,
            week=week,
            weekday=weekday,
            pairNumber=pair
        )
        entry.auditory_id=new_auditory
        entry.subject_id=new_subject
        entry.pairType_id=new_pairType
        entry.save()
    except ObjectDoesNotExist:
        Schedule.objects.create(group_id=gid,
            week=week,
            weekday=weekday,
            pairNumber=pair,
            auditory_id=new_auditory,
            subject_id=new_subject,
            pairType_id=new_pairType
        )

    return redirect("schedule-view-group", gid)


def schedule_delete(request, gid, week, weekday, pair):
    try:
        Schedule.objects.filter(
            group_id=gid,
            week=week,
            weekday=weekday,
            pairNumber=pair
        ).delete()
    except ObjectDoesNotExist:
        pass

    return redirect("schedule-view-group", gid)


def check_queue(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    try:
        user = User.objects.get(userID=userID)

        if user.role_id > 3:
            return JsonResponse({'redirect': False})

        # Получаем записи очереди для текущего пользователя
        queue_items = Queue.objects.filter(user=user)

        if queue_items.exists():
            for item in queue_items:
                if not item.queue.active:
                    continue
                if 1 <= item.orderStatus <= 2:
                    return JsonResponse({'redirect': True,
                                         'url': '/your_turn',
                                         'queue_id': item.queue_id,
                                         'token': item.token})

        return JsonResponse({'redirect': False})
    except ObjectDoesNotExist:
        return JsonResponse({'redirect': False})


def your_turn(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    queue_id = request.GET.get("queue_id")
    back = request.GET.get("back")
    token = request.GET.get("token")

    context = {
        "back_link": back
    }

    if request.method == "POST":
        entry_id = int(request.POST.get("entry_id"))
        option = int(request.POST.get("option", 2))
        match option:
            case 1:
                entry = Queue.objects.get(id=entry_id)
                entry.orderStatus = 2
                entry.save()
                context.update({"answering": True})
            case 2:
                entry = Queue.objects.get(id=entry_id)
                entry.orderStatus = 3
                entry.save()

                queue_update(queue_id)

                return redirect(back)
            case 3:
                entry = Queue.objects.get(id=entry_id)
                entry.orderStatus = 3
                entry.save()

                queue_update(queue_id)

                return redirect(back)

    try:
        entry = Queue.objects.get(queue_id=queue_id, user_id=userID, orderStatus__gte=1, orderStatus__lte=2)
        if entry.token != token:
            return redirect("home")
        context.update({"queue": {"id": queue_id, "title": entry.queue.title, "subject": entry.queue.subject.name}, "entry_id": entry.id})
        context.update({"timeout": entry.queue.timeout})
        if entry.orderStatus == 2:
            context.update({"answering": True})
    except ObjectDoesNotExist:
        context["error"] = "Неизвестная ошибка сервера."

    return TemplateResponse(request, "your-turn.html", context=context)


def queue_list(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    user_error = request.session.pop("user_error", None)
    if user_error is not None:
        context["user_error"] = user_error

    error = request.session.pop("error", None)
    if error is not None:
        context["error"] = error

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if user.role_id > 3:
            return HttpResponseForbidden()

        context.update({"role": user.role_id})

        context.update({"current_user_id": userID})
        context.update({"group_id": groupID})

        group = Group.objects.get(groupID=groupID)
        context.update({"groupname": group.name})
    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "queue-list.html", context=context)


def queue_list_rtu(request, gid, uid):
    queues = get_all_queues_for_group(gid)
    for queue in queues:
        queue_entry = Queue.objects.filter(queue_id=queue["id"], user_id=uid, orderStatus=0).first()

        queue.update({"place": get_queue_place(queue["id"], uid), "next": is_next_in_queue(queue["id"], uid)})
    return JsonResponse(queues, safe=False)


def queue_signup(request, qid, uid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    if userID != uid:
        request.session["user_error"] = "Вы не можете занять очередь для другого пользователя."
    else:
        try:
            queue = QueueList.objects.get(queueID=qid)
            user = User.objects.get(userID=uid)

            if user.role_id > 3:
                return HttpResponseForbidden()

            queue_entry = Queue.objects.filter(user_id=uid, queue_id=qid).exclude(orderStatus=3)

            if queue_entry.exists():
                request.session["user_error"] = "Вы не можете занять эту очередь повторно, пока не пройдете в ней или не выйдете из нее."
            else:
                if queue.type == 0:
                    request.session["user_error"] = "Вы не можете записаться в эту очередь, так как в ее настройках отключена самостоятельная запись."
                else:
                    signup_into_queue(qid, uid)
                    queue_title = f"{queue.title} ({queue.subject.name})" if queue.title is not None else f"Очередь по предмету {queue.subject.name}"
                    request.session["info"] = f"Вы успешно записались в очередь {queue_title}."
        except ObjectDoesNotExist:
            request.session["user_error"] = "Ошибка при обработке запроса."
    return redirect("queue-list")


def queue_signout(request, qid, uid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    if userID != uid:
        request.session["user_error"] = "Вы не можете выписать другого пользователя из очереди."
    else:
        try:
            queue = QueueList.objects.get(queueID=qid)
            user = User.objects.get(userID=uid)

            if user.role_id > 3:
                return HttpResponseForbidden()

            queue_entry = Queue.objects.filter(user_id=uid).exclude(orderStatus=3)

            if not queue_entry.exists():
                request.session["user_error"] = "Вы не можете выйти из очереди, в которой вас нет."
            else:
                signout_from_queue(qid, uid)
                queue_title = f"{queue.title} ({queue.subject.name})" if queue.title is not None else f"Очередь по предмету {queue.subject.name}"
                request.session["info"] = f"Вы успешно вышли из очереди {queue_title}."
        except ObjectDoesNotExist:
            request.session["user_error"] = "Ошибка при обработке запроса."
    return redirect("queue-list")


def queue_show(request, qid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("queue-list"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)

        if user.role_id > 3:
            return HttpResponseForbidden()

        group = user.group
        queue = QueueList.objects.get(queueID=qid)

        if group.groupID != queue.group_id:
            return HttpResponseForbidden()

        user_list = []
        users = User.objects.filter(group_id=queue.group_id)

        for user_ in users:
            user_list.append({
                "id": user_.userID,
                "name": user_.username,
                "image": user_.get_image()
            })

        context.update({"users": user_list})

        entries = show_queue(qid)
        queue = get_queue(qid)

        context.update({"current_user_id": userID, "current_user_role": user.role_id})
        context.update({"queue": queue, "queue_size": get_queue_size(qid)})
        context.update({"entries": entries})
    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "queue-show.html", context=context)


def queue_show_rtu(request, qid):
    return JsonResponse({"queue": show_queue(qid), "queue_size": get_queue_size(qid)}, safe=False)


def view_queue_update(request, qid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    redirect_path = "queue-list"

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if user.role_id > 3:
            return HttpResponseForbidden()

        queue = QueueList.objects.get(queueID=qid)

        if queue.group_id != groupID:
            return HttpResponseForbidden()

        if request.method == "POST":
            new_member = request.POST.get("new_member", None)

            if new_member is not None:
                new_member_entry = User.objects.get(userID=new_member)

                if new_member_entry.group_id != groupID:
                    request.session["user_error"] = "Вы не можете добавить в очередь пользователя не из вашей группы."
                else:
                    if get_queue_place(qid, new_member) == 0:
                        redirect_path = "queue-show"
                        signup_into_queue(qid, new_member)
                        request.session["info"] = f"В очередь с id={queue.queueID} был записан пользователь {new_member_entry.username}."
                    else:
                        request.session["user_error"] = "Вы не можете добавить в очередь пользователя, уже состоящего в очереди."
            else:
                request.session["error"] = "Ошибка при обработке запроса."
        else:
            action = request.GET.get("action", None)
            order = request.GET.get("order", None)
            token = request.GET.get("token", None)
            if action is None:
                request.session["error"] = "Ошибка при обработке запроса."
            else:
                match action:
                    case "activate":
                        queue_activate(qid)
                        request.session["info"] = f"Очередь с id={qid} активирована."
                    case "deactivate":
                        queue_deactivate(qid)
                        request.session["info"] = f"Очередь с id={qid} деактивирована."
                    case _:
                        if order is None or token is None:
                            request.session["error"] = "Ошибка при обработке запроса."
                        else:
                            order = int(order)
                            entry = Queue.objects.get(order=order, queue_id=qid, orderStatus=0)
                            if token != entry.token:
                                request.session["user_error"] = "Ошибка при проверке подлинности запроса."
                            redirect_path = "queue-show"
                            match action:
                                case "up":
                                    if order > 1:
                                        queue_lift_up(qid, order)
                                    else:
                                        request.session["user_error"] = "Ошибка при проверке подлинности запроса."
                                case "down":
                                    if order < get_queue_size(qid):
                                        queue_lift_down(qid, order)
                                    else:
                                        request.session["user_error"] = "Ошибка при проверке подлинности запроса."
                                case "delete":
                                    queue_delete_entry(qid, order)
    except ObjectDoesNotExist:
        request.session["error"] = "Ошибка при обработке запроса."

    if redirect_path == "queue-list":
        return redirect(redirect_path)
    return redirect(redirect_path, qid)


def queue_edit(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    user_error = request.session.pop("user_error", None)
    if user_error is not None:
        context["user_error"] = user_error

    error = request.session.pop("error", None)
    if error is not None:
        context["error"] = error

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        queues = QueueList.objects.filter(group_id=groupID)
        queue_list = []
        for queue in queues:
            queue_list.append(get_queue(queue.queueID))

        context.update({"queues": queue_list})
        context.update({"groupname": user.group.name})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    return TemplateResponse(request, "queue-edit.html", context=context)


def queue_create(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("queue-edit"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        if request.method == "POST":
            subject_id = request.POST.get("subject_id", 0)
            title = request.POST.get("title", None)
            type = request.POST.get("type", 0)
            timeout = request.POST.get("timeout", 10)

            QueueList.objects.create(subject_id=int(subject_id), title=title, group_id=groupID,
                                     type=type, active=False, timeout=int(timeout))
            context.update({"info": "Очередь успешно создана."})

        context.update({"groupname": user.group.name})

        subjects = Subject.objects.all()
        subject_list = []

        for subject in subjects:
            subject_list.append({
                "id": subject.subjectID,
                "name": subject.name
            })

        context.update({"subjects": subject_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    return TemplateResponse(request, "queue-create.html", context=context)


def queue_settings(request, qid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("queue-edit"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        queue = QueueList.objects.get(queueID=qid)

        if groupID != queue.group_id:
            return HttpResponseForbidden()

        if request.method == "POST":
            subject_id = request.POST.get("subject_id", 0)
            title = request.POST.get("title", None)
            type = request.POST.get("type", 0)
            timeout = request.POST.get("timeout", 10)

            queue = QueueList.objects.get(queueID=qid)
            queue.subject_id = int(subject_id)
            queue.title = title
            queue.type = type
            queue.timeout = int(timeout)
            queue.save()

            context.update({"info": "Очередь успешно обновлена."})

        queue = get_queue(qid)
        context.update({"queue": queue})
        context.update({"groupname": user.group.name})

        subjects = Subject.objects.all()
        subject_list = []

        for subject in subjects:
            subject_list.append({
                "id": subject.subjectID,
                "name": subject.name
            })

        context.update({"subjects": subject_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    return TemplateResponse(request, "queue-settings.html", context=context)


def queue_delete(request, qid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("queue-edit"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        queue = QueueList.objects.get(queueID=qid)

        if groupID != queue.group_id:
            return HttpResponseForbidden()

        if request.method == "POST":
            queue = QueueList.objects.get(queueID=qid)
            queue.delete()

            request.session["info"] = "Очередь успешно удалена."
            return redirect('queue-edit')

        queue = get_queue(qid)
        context.update({"queue": queue})
        context.update({"groupname": user.group.name})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    return TemplateResponse(request, "queue-delete.html", context=context)


def tasks_index(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    return redirect("tasks-list")


def tasks_list(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    user_error = request.session.pop("user_error", None)
    if user_error is not None:
        context["user_error"] = user_error

    error = request.session.pop("error", None)
    if error is not None:
        context["error"] = error

    try:
        user = User.objects.get(userID=userID)
        groupID = user.group_id

        if user.role_id > 3:
            return HttpResponseForbidden()

        context.update({"current_user_id": userID})
        context.update({"group_id": groupID})

        group = Group.objects.get(groupID=groupID)
        context.update({"groupname": group.name})

        tasks = Task.objects.filter(group_id=groupID).exclude(state=1)
        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "name": task.taskName,
                "subject_id": task.subject_id,
                "user_id": task.user_id
            })

        context.update({"tasks": task_list})

        user_list = []
        users = User.objects.filter(group_id=groupID)

        for user_ in users:
            user_list.append({
                "id": user_.userID,
                "name": user_.username,
                "image": user_.get_image()
            })

        context.update({"users": user_list})

        subjects = Subject.objects.all()
        subject_list = []
        for subject in subjects:
            subject_list.append({
                "id": subject.subjectID,
                "name": subject.name
            })

        context.update({"subjects": subject_list})

    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "tasks-list.html", context=context)


def tasks_list_rtu(request, gid):
    tasks = Task.objects.filter(group_id=gid).exclude(state=1).values('id', 'taskName', 'subject_id', 'user_id')
    return JsonResponse(list(tasks), safe=False)


def task_claim(request, taskID, userID):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID_ = request.session["userID"]

    if userID_ != userID:
        request.session["user_error"] = "Вы не можете занять задание для другого пользователя."
    else:
        try:
            user = User.objects.get(userID=userID)
            if user.role_id > 3:
                return HttpResponseForbidden()

            task = Task.objects.get(id=taskID)
            if task.user_id is not None:
                request.session["user_error"] = f"Задание \"{task.taskName}\" (id={task.id}) уже кем-то занято."
            else:
                task.user_id = userID
                task.save()
                Notification.objects.create(sender_id=0, receiver_id=userID,
                                                    type=0, date=datetime.datetime.now(timezone),
                                                    seen=False, text=task_claimed.format(task_name=task.taskName))
        except ObjectDoesNotExist:
            request.session["error"] = "Ошибка при обработке запроса."

    return redirect("tasks-list")


def task_unclaim(request, taskID, userID):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID_ = request.session["userID"]

    if userID_ != userID:
        request.session["user_error"] = "Вы не можете освободить задание за другого пользователя."
    else:
        try:
            user = User.objects.get(userID=userID)
            if user.role_id > 3:
                return HttpResponseForbidden()

            task = Task.objects.get(id=taskID)
            if task.user_id is None:
                request.session["user_error"] = f"Задание \"{task.taskName}\" (id={task.id}) и так уже свободно."
            else:
                task.user_id = None
                task.save()
                Notification.objects.create(sender_id=0, receiver_id=userID,
                                            type=0, date=datetime.datetime.now(timezone),
                                            seen=False, text=task_unclaimed.format(task_name=task.taskName))
        except ObjectDoesNotExist:
            request.session["error"] = "Ошибка при обработке запроса."

    return redirect("tasks-list")


def task_complete(request, taskID):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    try:
        user = User.objects.get(userID=userID)
        if user.role_id > 3:
            return HttpResponseForbidden()

        task = Task.objects.get(id=taskID)

        if task.user_id != userID:
            request.session["user_error"] = f"Вы не можете выполнить задание, которое не занимали себе."
        else:
            task.state = 1
            task.save()
            request.session["info"] = f"Вы отметили задание \"{task.taskName}\" как выполненное."
            Notification.objects.create(sender_id=0, receiver_id=userID,
                                        type=0, date=datetime.datetime.now(timezone),
                                        seen=False, text=task_completed.format(task_name=task.taskName))

    except ObjectDoesNotExist:
        request.session["error"] = "Ошибка при обработке запроса."

    return redirect("tasks-list")


def task_edit(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    try:
        user = User.objects.get(userID=userID)
        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        context.update({"group_id": user.group_id})

        tasks = Task.objects.filter(group_id=user.group_id)
        task_list = []

        context.update({"groupname": user.group.name})

        for task in tasks:
            task_list.append({
                "id": task.id,
                "name": task.taskName,
                "subject": task.subject,
                "user": task.user_id,
                "state": task.state
            })

        subjects = Subject.objects.all()
        subject_list = []

        for subject in subjects:
            subject_list.append({
                "id": subject.subjectID,
                "name": subject.name
            })

        users = User.objects.filter(group_id=user.group_id)
        user_list = []

        for user_ in users:
            user_list.append({
                "id": user_.userID,
                "name": user_.username,
                "image": user_.get_image()
            })

        context.update({"users": user_list, "tasks": task_list, "subjects": subject_list})
    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "task-edit.html", context=context)


def tasks_list_rtu_all(request, gid):
    tasks = Task.objects.filter(group_id=gid).values('id', 'taskName', 'subject_id', 'user_id', 'state')
    return JsonResponse(list(tasks), safe=False)


def task_create(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("task-edit"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        context.update({"group_id": user.group_id})

        context.update({"groupname": user.group.name})

        if request.method == "POST":
            subject_id = request.POST.get("subjectSelect", 0)
            taskName = request.POST.get("taskname", "")

            Task.objects.create(state=0, group_id=user.group_id, user=None,
                                taskName=taskName, subject_id=subject_id)
            request.session["info"] = "Новое задание создано успешно."
            return redirect("task-create")
        else:
            schedule = Schedule.objects.filter(group_id=user.group_id)
            available_subject_list = []

            for entry in schedule:
                subject = Subject.objects.get(subjectID=entry.subject_id)

                seen_ids = [item['id'] for item in available_subject_list]

                if subject.subjectID not in seen_ids:
                    available_subject_list.append({
                        "id": subject.subjectID,
                        "name": subject.name
                    })

            context.update({"subjects": available_subject_list})

            info = request.session.pop("info", None)
            if info is not None:
                context.update({"info": info})
    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "task-create.html", context=context)


def task_update(request, tid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("task-edit"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        context.update({"group_id": user.group_id})

        context.update({"groupname": user.group.name})

        task = Task.objects.get(id=tid)

        if task.group_id != user.group_id:
            context["error"] = "Вы не можете редактировать это задание: оно не относится к вашей группе."
        else:
            if request.method == "POST":
                old_state = task.state
                subject_id = request.POST.get("subjectSelect", 0)
                taskName = request.POST.get("taskname", "")
                state = int(request.POST.get("completed", 0))

                task.subject_id = subject_id
                task.taskName = taskName
                task.state = state
                task.save()

                if old_state != state:
                    if state == 0:
                        Notification.objects.create(sender_id=userID, receiver_id=task.user_id,
                                                    type=0, date=datetime.datetime.now(timezone),
                                                    seen=False, text=task_uncompleted.format(task_name=task.taskName))
                    else:
                        Notification.objects.create(sender_id=userID, receiver_id=task.user_id,
                                                    type=0, date=datetime.datetime.now(timezone),
                                                    seen=False, text=task_completed.format(task_name=task.taskName))

                request.session["info"] = "Задание обновлено успешно."
                return redirect("task-update", tid)
            else:
                context.update({"task": {"id": task.id, "name": task.taskName, "subject": task.subject_id, "state": task.state}})

                schedule = Schedule.objects.filter(group_id=user.group_id)
                available_subject_list = []

                for entry in schedule:
                    subject = Subject.objects.get(subjectID=entry.subject_id)

                    seen_ids = [item['id'] for item in available_subject_list]

                    if subject.subjectID not in seen_ids:
                        available_subject_list.append({
                            "id": subject.subjectID,
                            "name": subject.name
                        })

                context.update({"subjects": available_subject_list})

                info = request.session.pop("info", None)
                if info is not None:
                    context.update({"info": info})
    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "task-update.html", context=context)


def task_delete(request, tid):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("task-edit"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        if not (2 <= user.role_id <= 3):
            return HttpResponseForbidden()

        context.update({"group_id": user.group_id})

        context.update({"groupname": user.group.name})

        if tid == 0:
            tasks = Task.objects.filter(state=1, group_id=user.group_id)
            for task in tasks:
                owner = task.user_id
                taskName = task.taskName
                task.delete()
                if owner is not None:
                    Notification.objects.create(sender_id=0, receiver_id=owner,
                                                type=0, date=datetime.datetime.now(timezone),
                                                seen=False, text=task_deleted.format(task_name=taskName, deleter=user.username))
            request.session["info"] = "Удалены все задания в вашей группе, отмеченные как выполненные."
            return redirect("task-edit")
        else:
            task = Task.objects.get(id=tid)

            if task.group_id != user.group_id:
                context["error"] = "Вы не можете удалить это задание: оно не относится к вашей группе."
            else:
                if request.method == "POST":
                    task.delete()

                    request.session["info"] = "Задание удалено успешно."
                    return redirect("task-edit")
                else:
                    context.update({"task": {"id": task.id, "name": task.taskName, "subject": task.subject_id}})

                    schedule = Schedule.objects.filter(group_id=user.group_id)
                    available_subject_list = []

                    for entry in schedule:
                        subject = Subject.objects.get(subjectID=entry.subject_id)

                        seen_ids = [item['id'] for item in available_subject_list]

                        if subject.subjectID not in seen_ids:
                            available_subject_list.append({
                                "id": subject.subjectID,
                                "name": subject.name
                            })

                    context.update({"subjects": available_subject_list})
    except ObjectDoesNotExist:
        context["error"] = "Ошибка при обработке запроса."

    return TemplateResponse(request, "task-delete.html", context=context)


def profile(request):
    role = 0
    url = None
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        username = user.username
        role = user.role_id
        groupID = user.group_id if user.group_id is not None else 0
        url = user.get_image()
        context.update({"username": username, "path": url})

        if groupID != 0:
            group_ = Group.objects.get(groupID=groupID)
            context.update({"groupname": group_.name})
        else:
            context.update({"groupname": "нет группы"})

        role_ = UserRole.objects.get(userRoleID=role)
        context.update({"role": role, "role_name": role_.name, "role_desc": role_.desc.replace("\n", "<br>")})

        new_notifications, _ = getNotifications(userID)
        context.update({"notifications_count": len(new_notifications)})

        tasks = Task.objects.filter(user_id=userID, state=0).order_by("subject_id")
        task_list = []

        for task in tasks:
            task_list.append({
                "id": task.id,
                "name": task.taskName,
                "subject": task.subject.name
            })

        context.update({"tasks": task_list})

        context.update({"current_user_id": userID, "group_id": groupID})
        context.update({"queues": get_formatted_queues(userID)})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при сборе данных."})

    return TemplateResponse(request, "profile.html", context=context)


def profile_settings(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("profile"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)

        if request.method == "POST":
            theme, color = int(request.POST.get("theme", 0)), int(request.POST.get("color", 0))
            preferredTheme = (color << 1) + theme

            user.preferredTheme = preferredTheme

            user.save()

            context.update({"info": "Настройки применены успешно."})
        else:
            preferredTheme = user.preferredTheme

            theme, color = (preferredTheme & 1), (preferredTheme >> 1)
        context.update({"theme": theme, "color": color})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при чтении данных пользователя."})

    return TemplateResponse(request, "profile-settings.html", context=context)


def profile_edit(request):
    url = None
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("profile"),
            "text": "Назад"
        },
    }

    try:
        user = User.objects.get(userID=userID)
        username = user.username
        url = user.get_image()
        context.update({"username": username, "path": url})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при чтении базы данных."})

    return TemplateResponse(request, "profile-edit.html", context=context)


def profile_change_password(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    keys = ['old_password', 'new_password', 'new_password_repeat']
    values = [request.session.pop(key, "") for key in keys]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("profile-edit"),
            "text": "Назад"
        }
    }

    context.update({key: value for key, value in zip(keys, values)})

    info = request.session.pop("info", None)
    error = request.session.pop("error", None)
    user_error = request.session.pop("user_error", None)

    if info is not None:
        context.update({"info": info})
    if error is not None:
        context.update({"error": error})
    if user_error is not None:
        context.update({"user_error": user_error})

    return TemplateResponse(request, "profile-change-password.html", context=context)


def profile_update(request, type):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {

    }

    try:
        user = User.objects.get(userID=userID)
        user_auth = Authorize.objects.get(user_id=userID)

        match type:
            case "name":
                new_name = request.POST.get("username", "")
                new_image = request.FILES.get("image")

                user.username = new_name
                if new_image is not None:
                    #user.image = crop_and_scale_gif(new_image, new_image.name)
                    user.image = new_image

                user.save()

                return redirect("profile")
            case "auth":
                current_password = request.POST.get("old_password", "")
                password = user_auth.password_hash

                if sha256_hash(current_password) != password:
                    context.update({"user_error": "Ошибка: указан неправильный текущий пароль"})
                else:
                    new_password = request.POST.get("new_password", "")
                    new_password_repeat = request.POST.get("new_password_repeat", "")

                    request.session["old_password"] = current_password
                    request.session["new_password"] = new_password
                    request.session["new_password_repeat"] = new_password_repeat

                    if current_password == new_password:
                        context.update({"user_error": "Ошибка: новый пароль совпадает с текущим"})
                    elif new_password != new_password_repeat:
                        context.update({"user_error": "Ошибка: пароли не совпадают"})
                    else:
                        new_hash = sha256_hash(new_password)

                        user_auth.password_hash = new_hash
                        user_auth.session_token = str(uuid.uuid4())

                        user_auth.save()
                        context.update({"info": "Пароль успешно изменен. Вам необходимо перезайти в аккаунт для продолжения работы."})
            case _:
                context.update({"error": "Ошибка при обработке запроса."})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    if "info" in context:
        request.session["info"] = context["info"]
    if "error" in context:
        request.session["error"] = context["error"]
    if "user_error" in context:
        request.session["user_error"] = context["user_error"]
    return redirect("profile-change-password")


def profile_notifications(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("profile"),
            "text": "Назад"
        },
        "notif_types": {
            0: "Обычное уведомление",
            1: "Важное уведомление"
        }
    }

    unseen_notifications, seen_notifications = getNotifications(userID)
    readNotifications(userID)

    context.update({"unseen": unseen_notifications,
                    "seen": seen_notifications,
                    "notif_count": len(unseen_notifications)})

    users = User.objects.all()
    user_list = []

    for user in users:
        image = user.get_image()
        user_list.append({"id": user.userID, "name": user.username, "image": image})
        if user.userID == userID:
            context.update({"username": user.username})

    context.update({"users": user_list})

    return TemplateResponse(request, "profile-notifications.html", context=context)


def profile_group_management(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("profile"),
            "text": "Назад"
        }
    }

    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    error = request.session.pop("error", None)
    if error is not None:
        context["error"] = error

    user_error = request.session.pop("user_error", None)
    if user_error is not None:
        context["user_error"] = user_error

    try:
        user = User.objects.get(userID=userID)
        role = user.role_id

        if role != 3:
            return HttpResponseForbidden()

        context.update({"user_role": role})

        available_user_list = []
        available_users = (User.objects.filter(group_id=None) | User.objects.filter(group_id=user.group_id)) & User.objects.filter(role_id__lt=3)

        for user_ in available_users:
            image = user_.get_image()
            available_user_list.append({
                "id": user_.userID,
                "name": user_.username,
                "group_id": user_.group_id if user_.group_id is not None else 0,
                "role": user_.role_id,
                "image": image
            })

        context.update({"users": available_user_list})

        group_list = []
        groups = Group.objects.filter(groupID=user.group_id)

        for group in groups:
            group_list.append({"id": group.groupID, "name": group.name})

        role_list = []
        roles = UserRole.objects.filter(userRoleID__lt=3)

        for role_ in roles:
            role_list.append({"id": role_.userRoleID, "name": role_.name})

        context.update({"groups": group_list, "roles": role_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    context.update({"um_handler": "user-update"})

    return TemplateResponse(request, "user-management.html", context=context)


def logout(request):
    request.session.pop("userID", "")
    request.session.pop("session_token", "")
    request.session["info"] = "Вы вышли из аккаунта."
    return redirect("login")


def admin_index(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("profile"),
            "text": "Назад"
        }
    }

    try:
        user = User.objects.get(userID=userID)
        username = user.username
        role = user.role_id

        if role < 4:
            return HttpResponseForbidden()

        admin_roles = UserRole.objects.filter(isAdmin=True)
        admin_roles_ = []

        for admin_role in admin_roles:
            admin_roles_.append(admin_role.userRoleID)

        admins = User.objects.filter(role_id__in=admin_roles_).exclude(userID=0)
        admin_list = []

        for admin in admins:
            authorize_entry = Authorize.objects.get(user_id=admin.userID)
            last_login = authorize_entry.last_login
            admin_list.append({
                "id": admin.userID,
                "username": admin.username,
                "last_login": last_login.strftime("%d.%m.%y, %H:%M:%S %Z") if last_login is not None else None
            })

        admin_list = sorted(admin_list, key=lambda item: item["id"])

        roles = UserRole.objects.all()
        role_list = []

        for role_ in roles:
            if role_.userRoleID < role:
                role_list.append({"name": role_.name, "desc": role_.desc})

        context.update({"admin_list": admin_list, "user_id": userID, "roles": role_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при сборе данных."})

    return TemplateResponse(request, "admin.html", context=context)


def admin_db_edit(request, table=None):
    return redirect("admin-db-edit-page", table, 1)


def admin_db_edit_page(request, table=None, page=1):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("admin"),
            "text": "Назад"
        }
    }

    try:
        user = User.objects.get(userID=userID)
        role = user.role_id

        if role < 4:
            return HttpResponseForbidden()

        context.update({"role": role})

        header = []
        objects = []

        total_objects = 0

        if table is not None:
            match table:
                case "group":
                    header = ["ID", "Название"]
                    groups = Group.objects.all()[(page-1)*PAGE_SIZE:page*PAGE_SIZE]
                    total_objects = Group.objects.count()
                    for group in groups:
                        objects.append({
                            "id": group.groupID,
                            "name": group.name
                        })
                case "subject":
                    header = ["ID", "Название"]
                    subjects = Subject.objects.all()[(page-1)*PAGE_SIZE:page*PAGE_SIZE]
                    total_objects = Subject.objects.count()
                    for subject in subjects:
                        objects.append({
                            "id": subject.subjectID,
                            "name": subject.name
                        })
                case "auditory":
                    header = ["ID", "ID корпуса", "Название"]
                    auditories = Auditory.objects.all()[(page-1)*PAGE_SIZE:page*PAGE_SIZE]
                    total_objects = Auditory.objects.count()
                    for auditory in auditories:
                        objects.append({
                            "id": auditory.auditoryID,
                            "campus_id": auditory.campus_id,
                            "name": auditory.name
                        })
                case "campus":
                    header = ["ID", "Название", "Адрес"]
                    campuses = Campus.objects.all()[(page-1)*PAGE_SIZE:page*PAGE_SIZE]
                    total_objects = Campus.objects.count()
                    for campus in campuses:
                        objects.append({
                            "id": campus.campusID,
                            "name": campus.name,
                            "address": campus.address
                        })
                case "user":  # пример таблицы, доступной только для главного админа
                    if role < 5:
                        return HttpResponseForbidden()

                    header = ["ID", "Имя пользователя", "Роль", "ID группы", "Предпочитаемая тема"]
                    users = User.objects.all().exclude(userID=0)[(page-1)*PAGE_SIZE:page*PAGE_SIZE]
                    total_objects = User.objects.all().exclude(userID=0).count()
                    for user_ in users:
                        objects.append({
                            "id": user_.userID,
                            "name": user_.username,
                            "role": user_.role_id,
                            "groupID": user_.group_id if user_.group_id is not None else 0,
                            "preferredTheme": user_.preferredTheme
                        })
                case "authorize":
                    if role < 5:
                        return HttpResponseForbidden()

                    header = ["ID", "Электронная почта", "Последний вход в систему"]
                    auths = Authorize.objects.all()[(page-1)*PAGE_SIZE:page*PAGE_SIZE]
                    total_objects = Authorize.objects.count()
                    for auth_ in auths:
                        objects.append({
                            "id": auth_.user_id,
                            "email": auth_.email,
                            "last_login": auth_.last_login.strftime("%d.%m.%y, %H:%M:%S %Z") if
                            auth_.last_login is not None else "-"
                        })

                case _:
                    return TemplateResponse(request, "404.html")

            total_pages = total_objects // PAGE_SIZE

            if total_pages * PAGE_SIZE != total_objects:
                total_pages = math.ceil(total_objects / PAGE_SIZE)

            if len(objects) == 0:
                return redirect('admin-db-edit-page', table, total_pages)

            context.update({"table_name": table})
            context.update({"header": header, "objects": objects})
            context.update({"user_id": userID})
            context.update({"page": page, "total_pages": total_pages})

            info = request.session.pop("info", None)
            if info is not None:
                context.update({"info": info})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при сборе данных."})

    return TemplateResponse(request, "admin-db-edit.html", context=context)


def get_model_by_name(table):
    from django.apps import apps
    return apps.get_model('application', table)


def get_object(table, id):
    model = get_model_by_name(table)
    match table:
        case "authorize":
            return get_object_or_404(model, user_id=id)
        case "user":
            return get_object_or_404(model, userID=id)
        case "group":
            return get_object_or_404(model, groupID=id)
        case "auditory":
            return get_object_or_404(model, auditoryID=id)
        case "campus":
            return get_object_or_404(model, campusID=id)
        case "pairType":
            return get_object_or_404(model, pairTypeID=id)
        case "queueList":
            return get_object_or_404(model, queueID=id)
        case "queue":
            return get_object_or_404(model, id=id)
        case "subject":
            return get_object_or_404(model, subjectID=id)
        case "task":
            return get_object_or_404(model, id=id)
        case "schedule":
            return get_object_or_404(model, id=id)
        case _:
            return None


def get_model_data(obj):
    data = {}

    # Получаем все поля модели, кроме первичного ключа
    for field in obj._meta.fields[1:]:
        value = getattr(obj, field.name)

        # Обрабатываем значения полей
        if isinstance(field, models.IntegerField):
            data[field.name] = int(value) if value is not None else None
            # Проверяем, является ли поле ForeignKey
        elif isinstance(field, models.ForeignKey):
            related_obj = getattr(obj, field.name)
            if related_obj:
                data[f"{field.name}_id"] = getattr(related_obj, related_obj._meta.fields[0].name)
            else:
                data[f"{field.name}_id"] = None
        else:
            data[field.name] = value if value is not None else ""

    return data


def get_empty_model_data(model_class):
    data = {}

    # Получаем все поля модели, кроме первичного ключа
    for field in model_class._meta.fields[1:]:  # Пропускаем первое поле (обычно это id)
        if isinstance(field, models.IntegerField):
            data[field.name] = 0  # Присваиваем 0 для IntegerField
        elif isinstance(field, models.ForeignKey):
            data[f"{field.name}_id"] = None
        else:
            data[field.name] = ""  # Присваиваем пустую строку для остальных типов

    return data


def admin_db_update(request, table, id):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("admin-db-edit", args=[table]),
            "text": "Назад"
        }
    }

    try:
        user = User.objects.get(userID=userID)
        role = user.role_id

        if role < 4:
            return HttpResponseForbidden()

        if table not in permitted_tables_for_admins and role < 5:
            return HttpResponseForbidden()

        model = get_model_by_name(table)
        obj = get_object(table, id)

        if obj is None:
            raise ObjectDoesNotExist()

        if request.method == "POST":
            for field in request.POST:
                if field == "password_hash" and request.POST[field] != "":
                    setattr(obj, field, sha256_hash(request.POST[field]))
                elif field == "last_login":
                    setattr(obj, field, request.POST[field] if request.POST[field] != "" else None)
                elif field == "group_id":
                    setattr(obj, field, request.POST[field] if int(request.POST[field]) != 0 else None)
                else:
                    setattr(obj, field, request.POST[field])
            obj.save()
            context.update({"info": "Изменения успешно сохранены."})

        context.update({"fields": get_model_data(obj),
                        "object_id": id
        })

        role_list = []
        roles = UserRole.objects.filter(userRoleID__lt=5)
        for role_ in roles:
            role_list.append({"id": role_.userRoleID, "name": role_.name})

        context.update({"roles": role_list})

        group_list = []
        groups = Group.objects.all()
        for group_ in groups:
            group_list.append({"id": group_.groupID, "name": group_.name})

        context.update({"groups": group_list})

        campus_list = []
        campuses = Campus.objects.all()
        for campus_ in campuses:
            campus_list.append({"id": campus_.campusID, "name": campus_.name, "address": campus_.address})

        context.update({"campuses": campus_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при сборе данных."})

    return TemplateResponse(request, "admin-db-update.html", context=context)


def admin_db_delete(request, table, id):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("admin-db-edit", args=[table]),
            "text": "Назад"
        }
    }

    try:
        user = User.objects.get(userID=userID)
        role = user.role_id

        if role < 4:
            return HttpResponseForbidden()

        if table not in permitted_tables_for_admins and role < 5:
            return HttpResponseForbidden()

        model = get_model_by_name(table)
        obj = get_object(table, id)

        if obj is None:
            raise ObjectDoesNotExist()

        if request.method == "POST":
            obj.delete()
            request.session["info"] = "Объект удален успешно."
            return redirect(reverse("admin-db-edit", args=[table]))
        else:
            context.update({"object_id": id})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при сборе данных."})

    return TemplateResponse(request, "admin-db-delete.html", context=context)


def admin_db_create(request, table):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("admin-db-edit", args=[table]),
            "text": "Назад"
        },
        "table_name": table
    }

    try:
        user = User.objects.get(userID=userID)
        role = user.role_id

        if role < 4:
            return HttpResponseForbidden()

        if table not in permitted_tables_for_admins and role < 5:
            return HttpResponseForbidden()

        model = get_model_by_name(table)

        if request.method == "POST":
            obj = model()
            for field in request.POST:
                if field == "password_hash":
                    if request.POST[field] != "":
                        setattr(obj, field, sha256_hash(request.POST[field]))
                elif field == "last_login":
                    setattr(obj, field, request.POST[field] if request.POST[field] != "" else None)
                elif field == "group_id":
                    setattr(obj, field, request.POST[field] if request.POST[field] != 0 else None)
                else:
                    setattr(obj, field, request.POST[field])
            obj.save()
            context.update({"info": "Объект успешно создан."})

        context.update({"fields":get_empty_model_data(model)})

        role_list = []
        roles = UserRole.objects.filter(userRoleID__lt=5)
        for role_ in roles:
            role_list.append({"id": role_.userRoleID, "name": role_.name})

        context.update({"roles": role_list})

        group_list = []
        groups = Group.objects.all()
        for group_ in groups:
            group_list.append({"id": group_.groupID, "name": group_.name})

        context.update({"groups": group_list})

        campus_list = []
        campuses = Campus.objects.all()
        for campus_ in campuses:
            campus_list.append({"id": campus_.campusID, "name": campus_.name, "address": campus_.address})

        context.update({"campuses": campus_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при сборе данных."})

    return TemplateResponse(request, "admin-db-create.html", context=context)


def admin_user_management(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("admin"),
            "text": "Назад"
        }
    }
    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    error = request.session.pop("error", None)
    if error is not None:
        context["error"] = error

    user_error = request.session.pop("user_error", None)
    if user_error is not None:
        context["user_error"] = user_error

    try:
        user = User.objects.get(userID=userID)
        role = user.role_id

        if role < 4:
            return HttpResponseForbidden()

        context.update({"user_role": role})

        users = User.objects.all()

        user_list = []
        for user in users:
            if user.role_id < role:
                image = user.get_image()
                user_list.append({
                    "id": user.userID,
                    "name": user.username,
                    "group_id": user.group_id if user.group_id is not None else 0,
                    "role": user.role_id,
                    "image": image
                })

        context.update({"users": user_list})

        group_list = []
        groups = Group.objects.all()

        for group in groups:
            group_list.append({
                "id": group.groupID,
                "name": group.name
            })

        role_list = []
        roles = UserRole.objects.filter(userRoleID__lt=role)

        for role_ in roles:
            role_list.append({
                "id": role_.userRoleID,
                "name": role_.name
            })

        context.update({"groups": group_list, "roles": role_list})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    context.update({"um_handler": "user-update"})

    return TemplateResponse(request, "user-management.html", context=context)


def user_update(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    redirect_path = "admin-user-management"

    if request.method == "POST":
        try:
            user = User.objects.get(userID=userID)

            if user.role_id < 3:
                return HttpResponseForbidden()

            if user.role_id == 3:
                redirect_path = "profile-group-management"

            for field in request.POST:
                if field == "csrfmiddlewaretoken":
                    continue
                name, id = field.split("_")
                user_ = User.objects.get(userID=int(id))
                if name == "group":
                    old_group_id = user_.group_id
                    old_group_name = user_.group.name if old_group_id is not None else "(нет группы)"
                    new_group_id = int(request.POST[field])
                    if new_group_id == 0:
                        new_group_id = None
                    user_.group_id = new_group_id

                    if old_group_id != new_group_id:
                        new_group_name = "(нет группы)"
                        if new_group_id is not None:
                            new_group = Group.objects.get(groupID=new_group_id)
                            new_group_name = new_group.name

                        Notification.objects.create(sender_id=userID, receiver_id=user_.userID,
                                                    type=1, date=datetime.datetime.now(timezone),
                                                    seen=False, text=group_changed.format(group_name=new_group_name))

                        user_tasks = Task.objects.filter(user_id=user_.userID, group_id=old_group_id)
                        for task in user_tasks:
                            temp = Task.objects.get(id=task.id)
                            temp.user_id = None
                            temp.save()

                            Notification.objects.create(sender_id=0, receiver_id=user_.userID,
                                                        type=0, date=datetime.datetime.now(timezone),
                                                        seen=False, text=task_unclaimed.format(task_name=task.taskName))

                        user_queues = Queue.objects.filter(user_id=user_.userID, queue__group_id=old_group_id)
                        if user_queues.exists():
                            for queue in user_queues:
                                temp = Queue.objects.get(id=queue.id)
                                temp.delete()

                            Notification.objects.create(sender_id=0, receiver_id=user_.userID,
                                                        type=0, date=datetime.datetime.now(timezone),
                                                        seen=False, text=queues_deleted.format(group_name=old_group_name))
                elif name == "role":
                    old_role_id = user_.role_id
                    new_role_id = int(request.POST[field])
                    user_.role_id = new_role_id

                    if new_role_id != old_role_id:
                        new_role = UserRole.objects.get(userRoleID=new_role_id)

                        Notification.objects.create(sender_id=userID, receiver_id=user_.userID,
                                                    type=1, date=datetime.datetime.now(timezone),
                                                    seen=False, text=role_changed.format(role_name=new_role.name))
                user_.save()
            request.session["info"] = "Данные обновлены успешно."
            return redirect(redirect_path)
        except ObjectDoesNotExist:
            request.session["error"] = "Ошибка при обновлении данных."
            return redirect(redirect_path)
    else:
        return redirect(redirect_path)


def give_leadership(request, new_leader):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    redirect_path = "home"

    try:
        current_user = User.objects.get(userID=userID)
        new_user = User.objects.get(userID=new_leader)

        if current_user.group_id == new_user.group_id:
            if new_user.role_id == 2:
                temp = current_user.role_id
                current_user.role_id = new_user.role_id
                new_user.role_id = temp

                current_user.save()
                new_user.save()

                Notification.objects.create(sender_id=current_user.userID, receiver_id=new_user.userID,
                                            type=1, date=datetime.datetime.now(timezone),
                                            seen=False, text=role_changed.format(role_name=new_user.role.name))
                Notification.objects.create(sender_id=new_user.userID, receiver_id=current_user.userID,
                                            type=1, date=datetime.datetime.now(timezone),
                                            seen=False, text=role_changed.format(role_name=current_user.role.name))
            else:
                request.session["user_error"] = f"Невозможно передать роль старосты пользователю {new_user.username} (id={new_leader}): он должен являться модератором в группе."
                redirect_path = "profile-group-management"
        else:
            request.session["user_error"] = f"Невозможно передать роль старосты пользователю {new_user.username} (id={new_leader}): он должен находиться с вами в одной группе."
            redirect_path = "profile-group-management"
    except ObjectDoesNotExist:
        request.session["user_error"] = f"Пользователь с id={new_leader} не найден, невозможно передать ему роль старосты."
        redirect_path = "profile-group-management"

    return redirect(redirect_path)


def give_main_admin(request, new_main_admin):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    redirect_path = "home"

    try:
        current_user = User.objects.get(userID=userID)
        new_user = User.objects.get(userID=new_main_admin)

        if new_user.role_id == 4:
            temp = current_user.role_id
            current_user.role_id = new_user.role_id
            new_user.role_id = temp

            current_user.save()
            new_user.save()

            Notification.objects.create(sender_id=current_user.userID, receiver_id=new_user.userID,
                                        type=1, date=datetime.datetime.now(timezone),
                                        seen=False, text=role_changed.format(role_name=new_user.role.name))
            Notification.objects.create(sender_id=new_user.userID, receiver_id=current_user.userID,
                                        type=1, date=datetime.datetime.now(timezone),
                                        seen=False, text=role_changed.format(role_name=current_user.role.name))
        else:
            request.session["user_error"] = f"Невозможно передать роль главного администратора пользователю {new_user.username} (id={new_main_admin}): он должен являться администратором."
            redirect_path = "admin-user-management"
    except ObjectDoesNotExist:
        request.session["user_error"] = f"Пользователь с id={new_main_admin} не найден, невозможно передать ему роль главного администратора."
        redirect_path = "admin-user-management"

    return redirect(redirect_path)


def news_create(request):
    if "userID" not in request.session:
        request.session["error"] = "Чтобы продолжить работу с сервером, войдите в аккаунт."
        return redirect("/login")

    userID = request.session["userID"]

    context = {
        "about_link": reverse("about"),
        "back_link": {
            "link": reverse("home"),
            "text": "Назад"
        }
    }
    info = request.session.pop("info", None)
    if info is not None:
        context["info"] = info

    error = request.session.pop("error", None)
    if error is not None:
        context["error"] = error

    user_error = request.session.pop("user_error", None)
    if user_error is not None:
        context["user_error"] = user_error

    try:
        user = User.objects.get(userID=userID)

        if user.role_id == 1:
            return HttpResponseForbidden()

        if request.method == "POST":
            all = request.POST.get('all')
            title = request.POST.get('title')
            shortdesc = request.POST.get('shortdesc')
            content = request.POST.get('content')

            shortdesc = resize_images_in_html(shortdesc)
            content = resize_images_in_html(content)

            groups_ids = request.POST.getlist('groups')

            news_instance = News(
                title=title,
                shortdesc=shortdesc,
                content=content,
                author_id=userID  # Сохраняем текущего пользователя как автора
            )
            news_instance.save()

            # Привязываем группы к новости
            if not all:
                for group_id in groups_ids:
                    news_instance.groups.add(group_id)

            context.update({"info": "Новость успешно создана."})
        else:
            group_list = []
            if user.role_id >= 4:
                groups = Group.objects.all()
                for group in groups:
                    group_list.append({
                        "id": group.groupID,
                        "name": group.name
                    })
            else:
                group = Group.objects.get(groupID=user.group_id)
                group_list.append({
                    "id": group.groupID,
                    "name": group.name
                })

            context.update({"groups": group_list})
            context.update({"role": user.role_id})
    except ObjectDoesNotExist:
        context.update({"error": "Ошибка при обработке запроса."})

    return TemplateResponse(request, 'news-create.html', context=context)


# for rest api
class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        userrole = self.get_object()
        serializer = self.get_serializer(userrole)
        return Response(serializer.data)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserByGroupViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        group_id = self.kwargs["group_id"]
        return User.objects.filter(group_id=group_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserByRoleViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        role_id = self.kwargs["role_id"]
        return User.objects.filter(role_id=role_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Метод для создания нового пользователя (POST)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Метод для получения списка пользователей (GET)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # Метод для получения конкретного пользователя по ID (GET)
    def retrieve(self, request, pk=None, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    # Метод для обновления пользователя (PUT/PATCH)
    def update(self, request, pk=None, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Метод для удаления пользователя (DELETE)
    def destroy(self, request, pk=None, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthorizeViewSet(viewsets.ModelViewSet):
    queryset = Authorize.objects.all()
    serializer_class = AuthorizeSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None, *args, **kwargs):
        auth = self.get_object()
        serializer = self.get_serializer(auth)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        auth = self.get_object()
        serializer = self.get_serializer(auth, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        auth = self.get_object()
        auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampusViewSet(viewsets.ModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        campus = self.get_object()
        serializer = self.get_serializer(campus)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        campus = self.get_object()
        serializer = self.get_serializer(campus, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        campus = self.get_object()
        campus.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuditoryViewSet(viewsets.ModelViewSet):
    queryset = Auditory.objects.all()
    serializer_class = AuditorySerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        auditory = self.get_object()
        serializer = self.get_serializer(auditory)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        auditory = self.get_object()
        serializer = self.get_serializer(auditory, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        auditory = self.get_object()
        auditory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PairTypeViewSet(viewsets.ModelViewSet):
    queryset = PairType.objects.all()
    serializer_class = PairTypeSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        pairtype = self.get_object()
        serializer = self.get_serializer(pairtype)
        return Response(serializer.data)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        subject = self.get_object()
        serializer = self.get_serializer(subject)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        subject = self.get_object()
        serializer = self.get_serializer(subject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        subject = self.get_object()
        subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QueueListViewSet(viewsets.ModelViewSet):
    queryset = QueueList.objects.all()
    serializer_class = QueueListSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        group = self.get_object()
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QueueEntriesViewSet(viewsets.ModelViewSet):
    serializer_class = QueueSerializer
    queryset = Queue.objects.all()

    def get_queryset(self):
        queue_id = self.kwargs["queue_id"]
        return Queue.objects.filter(queue_id=queue_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class QueueViewSet(viewsets.ModelViewSet):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None, *args, **kwargs):
        queue_entry = self.get_object()
        serializer = self.get_serializer(queue_entry)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        queue_entry = self.get_object()
        serializer = self.get_serializer(queue_entry, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        queue_entry = self.get_object()
        queue_entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        task = self.get_object()
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        schedule = self.get_object()
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        notification = self.get_object()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        notification = self.get_object()
        serializer = self.get_serializer(notification, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        notification = self.get_object()
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        news = self.get_object()
        serializer = self.get_serializer(news)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        news = self.get_object()
        serializer = self.get_serializer(news, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        news = self.get_object()
        news.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
