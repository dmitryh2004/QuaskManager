from django.core.exceptions import ObjectDoesNotExist

from .models import *


def get_queue_place(queueID, userID):
    try:
        queue = QueueList.objects.get(queueID=queueID)
        queue_entries = Queue.objects.filter(queue=queue, orderStatus=0).order_by("order")

        place = 1
        for entry in queue_entries:
            if entry.user_id == userID:
                return place
            place += 1
        return 0
    except ObjectDoesNotExist:
        return None


def is_next_in_queue(queueID, userID):
    try:
        queue = QueueList.objects.get(queueID=queueID)
        queue_entry = Queue.objects.filter(queue=queue, user_id=userID).last()

        if queue_entry is not None:
            userOrder = queue_entry.order

            current = Queue.objects.filter(queue=queue, orderStatus__gte=1, orderStatus__lte=2).last()
            if current is not None:
                currentOrder = current.order

                if currentOrder == userOrder - 1:
                    return True
                else:
                    return False
            else:
                return userOrder == 1
    except ObjectDoesNotExist:
        return None
    return None


def get_all_queue_IDs_for_user(userID):
    queue_entries = Queue.objects.filter(user_id=userID, orderStatus=0)
    queues = []
    for entry in queue_entries:
        if entry.queue_id not in queues:
            queues.append(entry.queue_id)

    return queues


def get_all_queues_for_group(groupID):
    queues = QueueList.objects.filter(group_id=groupID)
    queue_list = []
    for queue in queues:
        queue_list.append({
            "id": queue.queueID,
            "subject": queue.subject.name,
            "title": queue.title,
            "type": queue.type,
            "active": queue.active
        })

    return queue_list


def get_formatted_queues(userID):
    queue_ids = get_all_queue_IDs_for_user(userID)
    queues = {}
    for queue_id in queue_ids:
        queue = QueueList.objects.get(queueID=queue_id)
        queues[queue_id] = {
            "subject": queue.subject.name,
            "title": queue.title,
            "type": queue.type,
            "place": get_queue_place(queue_id, userID),
            "next": is_next_in_queue(queue_id, userID)
        }
    return queues


def queue_update(queueID):
    try:
        passed = Queue.objects.filter(queue_id=queueID, orderStatus=3)
        entry = None
        if passed.exists():
            entry = passed.last()
        else:
            entry = Queue.objects.get(queue_id=queueID, order=1)
        if entry.queue.active:
            order = 1
            if passed.exists():
                order = entry.order + 1
            while True:
                next_entry = Queue.objects.get(queue_id=entry.queue_id, order=order)
                if next_entry:
                    if next_entry.orderStatus == 0:
                        if Authorize.objects.get(user=next_entry.user).online:
                            next_entry.orderStatus = 1
                            next_entry.save()
                            break
                        else:
                            next_entry.orderStatus = 3
                            next_entry.save()
                order += 1
    except ObjectDoesNotExist:
        ...


def signup_into_queue(qid, uid):
    try:
        entry = Queue.objects.filter(queue_id=qid).order_by("order").last()

        if entry is not None:
            immediate_cond = entry.orderStatus == 3 and entry.queue.active
            queue = entry.queue
            order = entry.order + 1
        else:
            immediate_cond = QueueList.objects.get(queueID=qid).active
            queue = QueueList.objects.get(queueID=qid)
            order = 1
        orderStatus = 1 if immediate_cond else 0

        Queue.objects.create(queue=queue, order=order, orderStatus=orderStatus,
                             token=uuid.uuid4(), user_id=uid)
    except ObjectDoesNotExist:
        ...


def signout_from_queue(qid, uid):
    try:
        entries = Queue.objects.filter(queue_id=qid, user_id=uid, orderStatus=0)
        if entries.exists():
            last_entry = entries.last()
            order = last_entry.order
            last_entry.delete()

            after = Queue.objects.filter(queue_id=qid, order__gt=order)
            if after.exists():
                for entry in after:
                    entry.order -= 1
                    entry.save()
    except ObjectDoesNotExist:
        ...


def get_queue(qid):
    try:
        queue = QueueList.objects.get(queueID=qid)
        res = {
            "id": queue.queueID,
            "subject": queue.subject.name,
            "subject_id": queue.subject.subjectID,
            "title": queue.title,
            "type": queue.type,
            "active": queue.active,
            "group": queue.group_id,
            "timeout": queue.timeout
        }
        return res
    except ObjectDoesNotExist:
        return None


def show_queue(qid):
    entry_list = []
    try:
        entries = Queue.objects.filter(queue_id=qid).order_by("order").values('id', 'order', 'user_id', 'orderStatus', 'token')
        for entry in entries:
            temp = User.objects.get(userID=entry["user_id"])
            entry_list.append({
                "id": entry["id"],
                "order": entry["order"],
                "user": {
                    "id": temp.userID,
                    "name": temp.username,
                    "image": temp.get_image()
                },
                "orderStatus": entry["orderStatus"],
                "token": entry["token"]
            })
        return entry_list
    except ObjectDoesNotExist:
        return None


def get_queue_size(qid):
    return Queue.objects.filter(queue_id=qid).count()


def queue_activate(qid):
    groupID = None
    try:
        groupID = QueueList.objects.get(queueID=qid).group_id
        try:
            old_active_queue = QueueList.objects.get(active=1, group_id=groupID)
            old_active_queue.active = False
            old_active_queue.save()
        except ObjectDoesNotExist:
            ...

        try:
            queue = QueueList.objects.get(queueID=qid)
            queue.active = True
            queue.save()
            queue_update(qid)
        except ObjectDoesNotExist:
            ...
    except ObjectDoesNotExist:
        ...


def queue_deactivate(qid):
    try:
        queue = QueueList.objects.get(queueID=qid)
        queue.active = False
        queue.save()
    except ObjectDoesNotExist:
        ...


def queue_lift_up(qid, order):
    try:
        entry = Queue.objects.get(queue_id=qid, order=order)
        before = Queue.objects.get(queue_id=qid, order=order-1, orderStatus=0)

        entry.order, before.order = before.order, entry.order
        entry.save()
        before.save()
    except ObjectDoesNotExist:
        ...


def queue_lift_down(qid, order):
    try:
        entry = Queue.objects.get(queue_id=qid, order=order)
        after = Queue.objects.get(queue_id=qid, order=order + 1, orderStatus=0)

        entry.order, after.order = after.order, entry.order
        entry.save()
        after.save()
    except ObjectDoesNotExist:
        ...


def queue_delete_entry(qid, order):
    try:
        entry = Queue.objects.get(queue_id=qid, order=order)
        afters = Queue.objects.filter(queue_id=qid, order__gt=order)

        entry.delete()
        for after in afters:
            after.order -= 1
            after.save()
    except ObjectDoesNotExist:
        ...