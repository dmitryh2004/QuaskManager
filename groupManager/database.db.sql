BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "groups" (
	"groupID"	INTEGER NOT NULL UNIQUE,
	"groupname"	TEXT NOT NULL,
	PRIMARY KEY("groupID")
);
CREATE TABLE IF NOT EXISTS "campuses" (
	"campusID"	INTEGER NOT NULL UNIQUE,
	"campusName"	TEXT NOT NULL,
	"campusAddress"	TEXT NOT NULL,
	PRIMARY KEY("campusID")
);
CREATE TABLE IF NOT EXISTS "subjects" (
	"subjectID"	INTEGER NOT NULL UNIQUE,
	"subjectName"	TEXT NOT NULL,
	PRIMARY KEY("subjectID")
);
CREATE TABLE IF NOT EXISTS "auditories" (
	"auditoryID"	INTEGER NOT NULL UNIQUE,
	"campusID"	INTEGER NOT NULL,
	"auditoryName"	TEXT NOT NULL,
	PRIMARY KEY("auditoryID","campusID")
);
CREATE TABLE IF NOT EXISTS "queueList" (
	"queueID"	INTEGER NOT NULL UNIQUE,
	"groupID"	INTEGER NOT NULL,
	"subjectID"	INTEGER NOT NULL,
	"writeMode"	INTEGER NOT NULL,
	PRIMARY KEY("queueID")
);
CREATE TABLE IF NOT EXISTS "queues" (
	"queueID"	INTEGER NOT NULL,
	"orderID"	INTEGER NOT NULL,
	"UserID"	INTEGER,
	"orderStatus"	INTEGER NOT NULL,
	PRIMARY KEY("queueID","orderID")
);
CREATE TABLE IF NOT EXISTS "tasks" (
	"groupID"	INTEGER NOT NULL,
	"subjectID"	INTEGER NOT NULL,
	"taskID"	INTEGER NOT NULL,
	"userID"	INTEGER,
	"taskName"	TEXT NOT NULL,
	PRIMARY KEY("groupID","subjectID","taskID")
);
CREATE TABLE IF NOT EXISTS "schedule" (
	"week"	INTEGER NOT NULL,
	"weekday"	INTEGER NOT NULL,
	"pairNumber"	INTEGER NOT NULL,
	"groupID"	INTEGER NOT NULL,
	"auditoryID"	INTEGER NOT NULL,
	"subjectID"	INTEGER NOT NULL,
	"pairTypeID"	INTEGER NOT NULL DEFAULT 1,
	PRIMARY KEY("week","weekday","pairNumber","groupID")
);
CREATE TABLE IF NOT EXISTS "authorize" (
	"userID"	INTEGER NOT NULL UNIQUE,
	"email"	TEXT NOT NULL,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("userID")
);
CREATE TABLE IF NOT EXISTS "pairTypes" (
	"pairTypeID"	INTEGER NOT NULL UNIQUE,
	"pairType"	TEXT NOT NULL,
	"pairTypeShort"	TEXT NOT NULL,
	PRIMARY KEY("pairTypeID")
);
CREATE TABLE IF NOT EXISTS "users" (
	"userID"	INTEGER NOT NULL UNIQUE,
	"username"	TEXT NOT NULL,
	"userrole"	INTEGER NOT NULL,
	"groupID"	INTEGER NOT NULL,
	"preferredColor"	INTEGER NOT NULL DEFAULT 4,
	PRIMARY KEY("userID")
);
CREATE TABLE IF NOT EXISTS "userroles" (
	"userroleID"	INTEGER NOT NULL UNIQUE,
	"userroleName"	TEXT NOT NULL,
	"userrolePriority"	INTEGER NOT NULL,
	"leader"	INTEGER NOT NULL DEFAULT 0,
	"description"	TEXT NOT NULL DEFAULT '',
	PRIMARY KEY("userroleID")
);
INSERT INTO "groups" VALUES (1,'ИКБО-01-22');
INSERT INTO "groups" VALUES (2,'ИКБО-02-22');
INSERT INTO "groups" VALUES (3,'ИКБО-03-22');
INSERT INTO "groups" VALUES (4,'ИКБО-04-22');
INSERT INTO "campuses" VALUES (1,'В-78','Москва, проспект Вернадского, 78');
INSERT INTO "campuses" VALUES (2,'В-86','Москва, проспект Вернадского, 86');
INSERT INTO "campuses" VALUES (3,'МП-1','Москва, улица Малая Пироговская, 1');
INSERT INTO "subjects" VALUES (1,'Геймдизайн');
INSERT INTO "subjects" VALUES (2,'Разработка серверных частей интернет-ресурсов');
INSERT INTO "subjects" VALUES (3,'Разработка баз данных');
INSERT INTO "subjects" VALUES (4,'Моделирование бизнес-процессов');
INSERT INTO "subjects" VALUES (5,'Мемология');
INSERT INTO "subjects" VALUES (6,'Военная кафедра');
INSERT INTO "subjects" VALUES (7,'Основы работы с редактором Starcraft 2');
INSERT INTO "auditories" VALUES (1,1,'А-1');
INSERT INTO "auditories" VALUES (2,1,'А-2');
INSERT INTO "auditories" VALUES (3,1,'А-3');
INSERT INTO "schedule" VALUES (0,1,1,1,1,1,2);
INSERT INTO "schedule" VALUES (0,1,2,1,1,1,2);
INSERT INTO "schedule" VALUES (0,2,4,1,2,3,1);
INSERT INTO "schedule" VALUES (0,2,4,2,2,3,1);
INSERT INTO "schedule" VALUES (0,3,3,1,3,5,1);
INSERT INTO "schedule" VALUES (0,3,3,2,3,5,1);
INSERT INTO "schedule" VALUES (0,3,3,3,3,5,1);
INSERT INTO "schedule" VALUES (0,3,3,4,3,5,1);
INSERT INTO "schedule" VALUES (1,5,5,3,2,4,1);
INSERT INTO "schedule" VALUES (1,5,6,3,1,2,1);
INSERT INTO "schedule" VALUES (1,2,3,3,3,4,2);
INSERT INTO "schedule" VALUES (0,6,2,3,1,1,1);
INSERT INTO "schedule" VALUES (0,3,4,3,1,7,1);
INSERT INTO "authorize" VALUES (1,'dhohlinov@mail.ru','7e2c1b5b8353caeb29d8444bb0f5e8525709308a3e0bd629f6e8d1aa0eb0b19b');
INSERT INTO "authorize" VALUES (2,'example@mail.ru','ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f');
INSERT INTO "pairTypes" VALUES (1,'Лекция','ЛК');
INSERT INTO "pairTypes" VALUES (2,'Практическое занятие','ПР');
INSERT INTO "pairTypes" VALUES (3,'Лабораторное занятие','ЛАБ');
INSERT INTO "pairTypes" VALUES (4,'Практика','Практика');
INSERT INTO "pairTypes" VALUES (5,'Военная кафедра','ВК');
INSERT INTO "users" VALUES (1,'Штирлиц',4,3,0);
INSERT INTO "users" VALUES (2,'Example',2,2,4);
INSERT INTO "userroles" VALUES (0,'Пользователь',0,0,'Роль по умолчанию.');
INSERT INTO "userroles" VALUES (1,'Модератор',1,0,'Может управлять очередями и заданиями в своей группе. Может выпускать новости для своей группы.');
INSERT INTO "userroles" VALUES (2,'Староста',2,1,'Имеет все полномочия модератора (управление очередями и заданиями, выпуск новостей для своей группы). Может изменять расписание для своей группы. Может назначать новых модераторов в своей группе и разжаловать существующих. Может передать свою роль одному из модераторов в своей группе.');
INSERT INTO "userroles" VALUES (3,'Администратор',10,0,'Имеет полномочия модератора в своей группе. Может назначать новых старост и модераторов и разжаловать существующих, а также выпускать новости для любых групп. Может изменять названия предметов, аудиторий и корпусов.');
INSERT INTO "userroles" VALUES (4,'Главный администратор',11,1,'Имеет все полномочия администратора (выдача ролей старосты и модератора, выпуск новостей для любых групп) и полномочия старосты (управление очередями и заданиями, выпуск новостей для своей группы) в своей группе. Может назначить новых администраторов и разжаловать существующих. Может передать свою роль одному из администраторов.');
COMMIT;
