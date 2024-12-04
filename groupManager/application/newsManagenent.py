import datetime
import os
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .models import *


def getNews(gid, nid):
    try:
        news_instance = News.objects.get(id=nid)

        groups = news_instance.groups

        if groups.all().exists():
            if not groups.filter(groupID=gid).exists():
                return None

        return {
            "id": news_instance.id,
            "title": news_instance.title,
            "shortdesc": news_instance.shortdesc,
            "content": news_instance.content,
            "author": news_instance.author.username,
            "date": news_instance.created_at,
            "groups": news_instance.groups
        }
    except ObjectDoesNotExist:
        return None


def readLastNews(gid, amount=3):
    news_list = []

    if gid is not None:
        group = Group.objects.get(groupID=gid)

        news = News.objects.filter(groups=group).order_by('-created_at') | News.objects.filter(groups=None).order_by('-created_at')
    else:
        news = News.objects.filter(groups=None).order_by('-created_at')

    if amount != -1:
        news = news[:amount]

    for news_instance in news:
        news_list.append({
            "id": news_instance.id,
            "title": news_instance.title,
            "shortdesc": news_instance.shortdesc,
            "content": news_instance.content,
            "author": news_instance.author.username,
            "date": news_instance.created_at,
            "groups": news_instance.groups
        })

    return news_list


def resize_images_in_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    for img in soup.find_all('img'):
        img['style'] = 'width: 256px; height: auto;'  # Устанавливаем максимальные размеры изображений

    return str(soup)  # Возвращаем измененный HTML как строку
