import datetime
from copy import deepcopy

from .models import *

class ScheduleConstants:
    DEBUG_SCHEDULE = False
    START_POINT = "24-09-01 23:59"
    PAIR_START = {
        1: "09:00",
        2: "10:40",
        3: "12:40",
        4: "14:20",
        5: "16:20",
        6: "18:00"
    }
    PAIR_END = {
        1: "10:30",
        2: "12:10",
        3: "14:10",
        4: "15:50",
        5: "17:50",
        6: "19:30"
    }

    @staticmethod
    def get_debug_schedule():
        return ScheduleConstants.DEBUG_SCHEDULE

    @staticmethod
    def get_start_point():
        return datetime.datetime.strptime(ScheduleConstants.START_POINT, "%y-%m-%d %H:%M")

    @staticmethod
    def get_pair_start(date, num):
        if date is None:
            date = datetime.datetime.now()
        string = date.strftime("%y-%m-%d ") + ScheduleConstants.PAIR_START[num]

        return datetime.datetime.strptime(string, "%y-%m-%d %H:%M")

    @staticmethod
    def get_pair_end(date, num):
        if date is None:
            date = datetime.datetime.now()
        string = date.strftime("%y-%m-%d ") + ScheduleConstants.PAIR_END[num]

        return datetime.datetime.strptime(string, "%y-%m-%d %H:%M")


def isEvenWeek(date):
    if date is None:
        date = datetime.datetime.now()
    start_point = ScheduleConstants.get_start_point()
    interval = (date - start_point).days // 7
    if date < start_point:
        return interval % 2 == 0
    else:
        return interval % 2 == 1


def getSchedule(groupID):
    schedule_objects = Schedule.objects.filter(group_id=groupID)

    schedule = []
    for item in schedule_objects:
        schedule.append({
            "week": item.week,
            "weekday": item.weekday,
            "pairNumber": item.pairNumber,
            "auditory": item.auditory_id,
            "subject": item.subject_id,
            "pairType": item.pairType_id
        })

    return schedule


def getScheduleTable(schedule):
    scheduleTable = {
        0: {
            1: {
                    1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            2: {
                    1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            3: {
                    1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            4: {
                    1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            5: {
                    1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            6: {
                    1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            }
        },  # even
        1: {
            1: {
                1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            2: {
                1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            3: {
                1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            4: {
                1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            5: {
                1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            },
            6: {
                1: dict(), 2: dict(), 3: dict(), 4: dict(), 5: dict(), 6: dict()
            }
        },  # even
    }

    for item in schedule:
        week, weekday, pair = item["week"], item["weekday"], item["pairNumber"]
        scheduleTable[week][weekday][pair] = {
            "auditory": item["auditory"],
            "subject": item["subject"],
            "pairType": item["pairType"]
        }

    return scheduleTable


def formScheduleTable(groupID):
    scheduleTable = getScheduleTable(getSchedule(groupID))

    # получаем вспомогательные объекты
    pairtypes_objects = PairType.objects.all()
    auditories_objects = Auditory.objects.all()
    campuses_objects = Campus.objects.all()
    subjects_objects = Subject.objects.all()
    groups_objects = Group.objects.all()

    pairtypes = dict()
    for pairtype in pairtypes_objects:
        pairtypes[pairtype.pairTypeID] = {
            "name": pairtype.name,
            "name_short": pairtype.name_short
        }

    auditories = dict()
    for auditory in auditories_objects:
        auditories[auditory.auditoryID] = {
            "name": auditory.name,
            "campusID": auditory.campus_id
        }

    campuses = dict()
    for campus in campuses_objects:
        campuses[campus.campusID] = {
            "name": campus.name,
            "address": campus.address
        }

    subjects = dict()
    for subject in subjects_objects:
        subjects[subject.subjectID] = {
            "name": subject.name
        }

    groups = dict()
    for group in groups_objects:
        groups[group.groupID] = {
            "name": group.name
        }

    res = deepcopy(scheduleTable)

    for e in range(0, 2):
        for w in range(1, 7):
            for p in range(1, 7):
                res[e][w][p] = dict()
                if 'auditory' in scheduleTable[e][w][p]:
                    res[e][w][p]["auditory"] = auditories[scheduleTable[e][w][p]['auditory']]['name']
                    res[e][w][p]["campus"] = campuses[auditories[scheduleTable[e][w][p]['auditory']]['campusID']]['name']
                if 'subject' in scheduleTable[e][w][p]:
                    res[e][w][p]["subject"] = subjects[scheduleTable[e][w][p]['subject']]['name']
                if 'pairType' in scheduleTable[e][w][p]:
                    res[e][w][p]["pairType"] = pairtypes[scheduleTable[e][w][p]['pairType']]['name_short']

    return res


def isTomorrow(date):
    current = datetime.datetime.now()
    date = datetime.datetime.strptime(date, "%d.%m.%y, %H:%M")
    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    return (date - current).days > 1


def getPairs(groupID, amount=5):
    # получает amount ближайших пар. если amount = -1, получает все пары
    pairs = []

    # получаем вспомогательные объекты
    pairtypes_objects = PairType.objects.all()
    auditories_objects = Auditory.objects.all()
    campuses_objects = Campus.objects.all()
    subjects_objects = Subject.objects.all()
    groups_objects = Group.objects.all()

    pairtypes = dict()
    for pairtype in pairtypes_objects:
        pairtypes[pairtype.pairTypeID] = {
            "name": pairtype.name,
            "name_short": pairtype.name_short
        }

    auditories = dict()
    for auditory in auditories_objects:
        auditories[auditory.auditoryID] = {
            "name": auditory.name,
            "campusID": auditory.campus_id
        }

    campuses = dict()
    for campus in campuses_objects:
        campuses[campus.campusID] = {
            "name": campus.name,
            "address": campus.address
        }

    subjects = dict()
    for subject in subjects_objects:
        subjects[subject.subjectID] = {
            "name": subject.name
        }

    groups = dict()
    for group in groups_objects:
        groups[group.groupID] = {
            "name": group.name
        }

    # получаем таблицу расписания для группы
    scheduleTable = getScheduleTable(getSchedule(groupID))

    # выбираем подходящие пары
    now = datetime.datetime.now()
    current_week = int(isEvenWeek(None))
    current_weekday = now.weekday() + 1
    current_pair = 0
    days_processed = 0

    if now >= ScheduleConstants.get_pair_start(None, 1):
        for _ in range(1, 7):
            if now < ScheduleConstants.get_pair_start(None, _):
                current_pair = _-1
        if current_pair == 0:
            current_pair = 7

    if current_pair == 0:
        current_pair = 1
    if current_pair == 7:
        current_weekday += 1
        current_pair = 1
        days_processed += 1

    if current_weekday >= 7:
        current_weekday = 1
        current_week = 0 if current_week == 1 else 1
        current_pair = 1
        days_processed += 1

    matching = []
    while days_processed <= 14 and len(matching) < amount:
        while current_pair < 7:
            pair = scheduleTable[current_week][current_weekday][current_pair]
            if pair != dict():
                pair_start = ScheduleConstants.get_pair_start(now + datetime.timedelta(days=days_processed), current_pair)
                matching_pair = pair.copy()
                matching_pair.update({"pairStart": pair_start.strftime("%d.%m.%y, %H:%M")})
                matching.append(matching_pair)
                if len(matching) == amount: break
            current_pair += 1


        current_pair = 1
        current_weekday += 1
        if current_weekday == 7:
            current_weekday = 1
            current_week = 0 if current_week == 1 else 1
            days_processed += 1

        days_processed += 1

    # форматируем полученные пары
    for item in matching:
        temp = item.copy()
        temp["not_tomorrow"] = isTomorrow(item["pairStart"])
        temp["auditory"] = auditories[item['auditory']]['name']
        temp["date"] = item["pairStart"]
        temp["campus"] = campuses[auditories[item['auditory']]['campusID']]['name']
        temp["subject"] = subjects[item['subject']]['name']
        temp["pairType"] = pairtypes[item['pairType']]['name_short']

        pairs.append(temp)

    return pairs
