#! /usr/bin/env python
# -*- coding: utf-8 -*-

import mysql.connector
from config import db_host, db_port, db_database, db_user, db_password
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class DB:
    def __init__(self):
        try:
            self.db = mysql.connector.connect(
                    host=db_host,
                    port=db_port,
                    database=db_database,
                    user=db_user,
                    password=db_password,
            )
            if self.db.is_connected():
                print 'Успешное подключение к БД'
            self.cursor = self.db.cursor()

        except Exception as e:
            print e
            print "Ошибка"
            sys.exit()

    def add_user(self, user_id):
        try:
            sql = "INSERT INTO un_users (user_id) VALUES (%s)"
            val = (user_id, )
            self.cursor.execute(sql, val)
            self.db.commit()
        #     print "Успешное добавление пользователя"
        except mysql.connector.errors.IntegrityError:
            print "Ошибка, пользователь уже зарегистрирован"
        except Exception as e:
            print e

    def add_message(self, user_id, text, tags):
        try:
            sql = "INSERT INTO un_messages (user_id, message, tags) VALUES (%s, %s, %s);"
            val = (user_id, text, tags)
            self.cursor.execute(sql, val)
            msg_id = self.cursor.lastrowid
            sql2 = "UPDATE un_users SET last_msg_id = %s WHERE user_id = %s"
            val2 = (msg_id, user_id)
            self.cursor.execute(sql2, val2)
            self.db.commit()
            return [True, msg_id]
        except Exception as e:
            print e

    def read_last_message(self, user_id):
        try:
            sql = "SELECT un_messages.message FROM un_messages JOIN un_users " \
                  "ON un_messages.id = un_users.last_msg_id AND un_users.user_id = '%s'"
            val = (user_id, )
            self.cursor.execute(sql, val)
            row = self.cursor.fetchone()
            print row
            return [True, row[0]]
        except Exception as e:
            print e

    def read_message_by_id(self, user_id, msg_id):
        try:
            sql = "SELECT user_id, message FROM un_messages WHERE id=%s"
            val = (msg_id, )
            self.cursor.execute(sql, val)
            row = self.cursor.fetchone()
            if len(row) == 0:
                return [True, 'Заметка {} не найдена'.format(msg_id)]
            if int(row[0]) != user_id:
                return [True, 'Заметка {} принадлежит другому пользователю'.format(msg_id)]
            return [True, row[1]]
        except Exception as e:
            print e

    def read_all(self, user_id):
        try:
            sql = "SELECT message, date FROM un_messages WHERE user_id=%s ORDER BY date"
            val = (user_id, )
            self.cursor.execute(sql, val)
            row = self.cursor.fetchall()
            if len(row) == 0:
                return [True, 'Заметок нет']
            text = ""
            for msg in row:
                text += "<b>Отправлено: {}</b>\n\n{}\n\n\n".format(msg[1], msg[0])
            return [True, text]
        except Exception as e:
            print e

    def read_tag(self, user_id, tag):
        try:
            sql = "SELECT message FROM un_messages WHERE user_id=%s AND tags LIKE %s ORDER BY date"
            val = (user_id, "%|" + tag + "|%")
            self.cursor.execute(sql, val)
            row = self.cursor.fetchall()
            if len(row) == 0:
                return [True, 'Заметок по данному тегу нет']
            text = ""
            for msg in row:
                text += "{}\n\n".format(msg[0])
            return [True, text]
        except Exception as e:
            print e

    def write_tag(self, user_id, tag, desc):
        try:
            self.cursor.execute("SELECT `tag` FROM `un_tags` WHERE `tag`=%s AND `user_id`=%s", (tag, user_id))
            ch = self.cursor.fetchone()
            if ch is None:
                self.cursor.execute(
                    "INSERT INTO `un_tags` (`tag`, `description`, `user_id`) VALUES (%s, %s, %s)",
                    (tag, desc, user_id)
                )
                text = "Тэг #{} добавлен".format(tag)
            else:
                self.cursor.execute("UPDATE `un_tags` SET `description`=%s WHERE `tag`=%s", (desc, tag))
                text = "Тэг #{} обновлен".format(tag)
            self.db.commit()
            return [True, text]
        except Exception as e:
            print e

    def get_tags(self, user_id, tags):
        try:
            text = ""
            str_tags = ', '.join(map(lambda x: "'" + x + "'", tags))
            sql = "SELECT `tag`, `description` FROM `un_tags` WHERE `tag` IN ({}) AND (`user_id`={} OR " \
                  "`user_id`='all')".format(str_tags, user_id)
            self.cursor.execute(sql)
            ch = self.cursor.fetchall()
            if ch is None or len(ch) == 0:
                text += "Тэгов {} нет в базе данных\n\n".format(str_tags)
            else:
                for i in ch:
                    text += "#{} - {}\n\n".format(i[0], i[1])
            return [True, text]
        except Exception as e:
            print e

    def get_all_tags(self, user_id):
        try:
            text = ""
            sql = "SELECT `tag`, `description` FROM `un_tags` WHERE `user_id`=%s OR `user_id`='all'"
            self.cursor.execute(sql, (user_id, ))
            ch = self.cursor.fetchall()
            if ch is None or len(ch) == 0:
                text = "У вас нет сохраненных тэгов\n\n"
            else:
                for i in ch:
                    text += "#{} - {}\n\n".format(i[0], i[1])
            return [True, text]
        except Exception as e:
            print e
