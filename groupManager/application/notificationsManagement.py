from .models import *


def getNotifications(userID):
    notifications = Notification.objects.filter(receiver_id=userID).order_by("-id")
    seen_notifications_list = []
    unseen_notifications_list = []

    for notification in notifications:
        notif_object = {
            "type": notification.type,
            "date": notification.date,
            "text": notification.text,
            "sender": notification.sender_id
        }
        if notification.seen:
            seen_notifications_list.append(notif_object)
        else:
            unseen_notifications_list.append(notif_object)

    return unseen_notifications_list, seen_notifications_list


def readNotifications(userID):
    Notification.objects.filter(receiver_id=userID, seen=False).update(seen=True)
