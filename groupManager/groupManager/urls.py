"""
URL configuration for groupManager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import datetime

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path, include
from application import views
from application.views import (UserRoleViewSet,
   GroupViewSet,
   UserViewSet,
   UserByGroupViewSet,
   UserByRoleViewSet,
   AuthorizeViewSet,
   CampusViewSet,
   AuditoryViewSet,
   PairTypeViewSet,
   SubjectViewSet,
   QueueListViewSet,
   QueueEntriesViewSet,
   QueueViewSet,
   TaskViewSet,
   ScheduleViewSet,
   NotificationViewSet,
   NewsViewSet)
from rest_framework.routers import DefaultRouter

schedule_patterns = [
    path('delete/<int:gid>/<int:week>/<int:weekday>/<int:pair>', views.schedule_delete, name='schedule-delete'),
    path('update/<int:gid>/<int:week>/<int:weekday>/<int:pair>', views.schedule_update, name='schedule-update'),
    path('edit/<int:gid>/<int:week>/<int:weekday>/<int:pair>', views.schedule_edit, name='schedule-edit'),
    path('view/<int:id>', views.schedule_view_group, name='schedule-view-group'),
    path('view', views.schedule_view),
    path('', views.schedule_index, name='schedule'),
]

queue_patterns = [
    path('queue-edit', views.queue_edit, name='queue-edit'),
    path('queue-create', views.queue_create, name='queue-create'),
    path('queue-settings/<int:qid>', views.queue_settings, name='queue-settings'),
    path('queue-delete/<int:qid>', views.queue_delete, name='queue-delete'),
    path('queue-update/<int:qid>', views.view_queue_update, name='queue-update'),
    path('signout/<int:qid>/<int:uid>', views.queue_signout),
    path('signup/<int:qid>/<int:uid>', views.queue_signup),
    path('list/rtu/<int:gid>/<int:uid>', views.queue_list_rtu, name='queue-list-rtu'),
    path('rtu/<int:qid>', views.queue_show_rtu, name='queue-show-rtu'),
    path('<int:qid>', views.queue_show, name='queue-show'),
    path('list', views.queue_list, name='queue-list'),
    path('check', views.check_queue),
]

tasks_patterns = [
    path('', views.tasks_index, name='tasks'),
    path('list', views.tasks_list, name='tasks-list'),
    path('rtu/<int:gid>', views.tasks_list_rtu, name='tasks-list-rtu'),
    path('rtu/all/<int:gid>', views.tasks_list_rtu_all, name='tasks-list-rtu-all'),
    path('task-claim/<int:taskID>/<int:userID>', views.task_claim, name='task-claim'),
    path('task-unclaim/<int:taskID>/<int:userID>', views.task_unclaim, name='task-unclaim'),
    path('task-complete/<int:taskID>', views.task_complete, name='task-complete'),
    path('task-edit', views.task_edit, name='task-edit'),
    path('task-create', views.task_create, name='task-create'),
    path('task-update/<int:tid>', views.task_update, name='task-update'),
    path('task-delete/<int:tid>', views.task_delete, name='task-delete')
]

news_patterns = [
    path('create', views.news_create, name="news-create"),
    path('show/<id>', views.news_show_1, name="news-show-1"),
    path('show', views.news_show, name="news-show")
]

admin_patterns = [
    path('user-management', views.admin_user_management, name='admin-user-management'),
    path('db-create/<str:table>', views.admin_db_create, name='admin-db-create'),
    path('db-update/<str:table>/<int:id>', views.admin_db_update, name='admin-db-update'),
    path('db-delete/<str:table>/<int:id>', views.admin_db_delete, name='admin-db-delete'),
    path('db-edit/<str:table>/<int:page>', views.admin_db_edit_page, name='admin-db-edit-page'),
    path('db-edit/<str:table>', views.admin_db_edit, name='admin-db-edit'),
    path('db-edit', views.admin_db_edit_page, name='admin-db-edit-default'),
    path('', views.admin_index, name='admin')
]

profile_patterns = [
    path('group-management', views.profile_group_management, name='profile-group-management'),
    path('notifications', views.profile_notifications, name='profile-notifications'),
    path('update/<str:type>', views.profile_update, name='profile-update'),
    path('change_password', views.profile_change_password, name='profile-change-password'),
    path('edit', views.profile_edit, name='profile-edit'),
    path('settings', views.profile_settings, name='profile-settings'),
    path('', views.profile, name='profile')
]

router = DefaultRouter()
router.register(r'user_roles', UserRoleViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'users', UserViewSet)
router.register(r'authorizes', AuthorizeViewSet)
router.register(r'campuses', CampusViewSet)
router.register(r'auditories', AuditoryViewSet)
router.register(r'pair_types', PairTypeViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'queue_lists', QueueListViewSet)
router.register(r'queues', QueueViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'news', NewsViewSet)

api_urls = [
    path('', include(router.urls)),
    path('groups/<int:group_id>/users', UserByGroupViewSet.as_view({'get': 'list'})),
    path('user_roles/<int:role_id>/users', UserByRoleViewSet.as_view({'get': 'list'})),
    path('queue_lists/<int:queue_id>/entries', QueueEntriesViewSet.as_view({'get': 'list'}))
]

urlpatterns = [
    path('', views.index, name='home'),
    path('api/', include(api_urls)),
    path("login", views.login, name='login'),
    path("logout", views.logout, name="logout"),
    path("authorize", views.authorize),
    path("signup", views.signup, name='signup'),
    path("register", views.register),
    path('recover', views.recover, name='recover'),
    path("user_update", views.user_update, name='user-update'),
    path("give-leadership/<int:new_leader>", views.give_leadership, name="give-leadership"),
    path("give-main-admin/<int:new_main_admin>", views.give_main_admin, name="give-main-admin"),
    path('notifications-count-rtu/<int:uid>', views.count_notifications, name='notifications-count-rtu'),
    path("your_turn", views.your_turn),
    path('ping/', views.ping, name='ping'),
    path('set_offline/', views.set_offline),
    path('about/guide/<int:role>', views.about_guide, name="guide"),
    re_path('^about', views.about, name='about'),
    re_path("^schedule/", include(schedule_patterns)),
    re_path("^queue/", include(queue_patterns)),
    re_path("^tasks/", include(tasks_patterns)),
    re_path("^news/", include(news_patterns)),
    re_path("^profile/", include(profile_patterns)),
    re_path("^admin/", include(admin_patterns)),
    path('tinymce/', include('tinymce.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
