#! /usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os.path
from config import token
import requests
from db_helper import DB
import re
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')


tgurl = 'https://api.telegram.org/bot{token}'.format(token=token)


def json_write(user_id, message, time):
    time = datetime.utcfromtimestamp(int(time)).strftime('%H:%M:%S %d/%m/%Y')
    row = {
        "user_id": user_id,
        "message": str(message).decode('utf-8'),
        "time": time,
    }
    if os.path.exists("log.json"):
        with open("log.json", "a+") as f:
            f.read()
            f.truncate(f.tell() - 1)
            f.seek(f.tell())
            f.write(',\n')
            f.write(json.dumps(row, ensure_ascii=False).encode('utf8'))
            f.write(']')
    else:
        with open("log.json", "a+") as f:
            f.write('[')
            f.write(json.dumps(row, ensure_ascii=False).encode('utf8'))
            f.write(']')


def send_msg(text, chat_id):
    url = tgurl + '/sendMessage'
    params = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }
    res = requests.get(url, params=params)
    return res


def get_updates(offset=0):
    try:
        params = {
            'offset': offset,
            'timeout': 30
        }
        result = requests.get(tgurl + '/getUpdates', params=params).json()
        return result['result']
    except KeyboardInterrupt:
        print 'Остановка по Ctrl-C'
        sys.exit()
    except Exception as e:
        print e
        print 'Ошибка подключения'
        return False


def check_tags(text):
    tags = ""
    for tag in text.split():
        if tag.startswith("#"):
            tag = "".join(c.lower() for c in tag if c.isalpha())
            tags += "|{tag}|".format(tag=tag)
    return tags


def check_input_tag(values):
    tag = values.split(" ")[0].lower()
    if "#" in tag:
        tag = tag[1:]
    return tag


def check_input_tags(values):
    tags = values.split(", ")
    for i, tag in enumerate(tags):
        if "#" in tag:
            tags[i] = tag[1:]
    return tags


def check_command(message):
    if message["entities"][0]["type"] == "bot_command":
        pattern = r"^\/[a-z]*(_[a-z]*)?\s"
        text = message["text"]
        values = ''
        if " " not in text:
            command = text[1:]
        else:
            command = re.search(pattern, text)
            if command:
                command = command.group()[1:].strip()
                values = text[len(command)+2:]
        return get_command(command, values, message)


def get_command(cmd, values, message):
    user_id = message['from']['id']
    chat_id = message['chat']['id']

    if cmd == "start":
        db.add_user(user_id)

    elif cmd == "write":
        if len(values) > 0:
            tags = check_tags(values)
            rez = db.add_message(user_id, values, tags)
            if rez is not None and rez[0]:
                send_msg("Заметка {} сохранена".format(rez[1]), chat_id)
            else:
                send_msg("Ошибка", chat_id)
        else:
            send_msg("Вы не ввели заметку", chat_id)

    elif cmd == "read_last":
        rez = db.read_last_message(user_id)
        if rez is not None and rez[0]:
            send_msg(rez[1], chat_id)
        else:
            send_msg("Ошибка", chat_id)

    elif cmd == "read":
        if len(values) > 0:
            try:
                values = int(values)
                rez = db.read_message_by_id(user_id, values)
                if rez is not None and rez[0]:
                    send_msg(rez[1], chat_id)
                else:
                    send_msg("Ошибка", chat_id)
            except ValueError:
                send_msg("Вы отправили не численный ID заметки", chat_id)
        else:
            send_msg("Вы не отправили численный ID заметки", chat_id)

    elif cmd == "read_all":
        rez = db.read_all(user_id)
        if rez is not None and rez[0]:
            send_msg(rez[1], chat_id)
        else:
            send_msg("Ошибка", chat_id)

    elif cmd == "read_tag":
        if len(values) > 0:
            tag = check_input_tag(values)
            rez = db.read_tag(user_id, tag)
            if rez is not None and rez[0]:
                send_msg(rez[1], chat_id)
            else:
                send_msg("Ошибка", chat_id)
        else:
            send_msg("Вы не ввели тэг", chat_id)

    elif cmd == "write_tag":
        if len(values) > 0:
            tag = check_input_tag(values)
            desc = values[len(tag)+1:]
            rez = db.write_tag(user_id, tag, desc)
            if rez is not None and rez[0]:
                send_msg(rez[1], chat_id)
            else:
                send_msg("Ошибка", chat_id)
        else:
            send_msg("Вы не ввели тэг и его описание", chat_id)

    elif cmd == "tag":
        if len(values) > 0:
            tags = check_input_tags(values)
            rez = db.get_tags(user_id, tags)
            if rez is not None and rez[0]:
                send_msg(rez[1], chat_id)
            else:
                send_msg("Ошибка", chat_id)
        else:
            send_msg("Вы не ввели тэги для поиска", chat_id)

    elif cmd == "tag_all":
        rez = db.get_all_tags(user_id)
        if rez is not None and rez[0]:
            send_msg(rez[1], chat_id)
        else:
            send_msg("Ошибка", chat_id)

    else:
        send_msg("Команда не распознана", chat_id)


def main():
    update_id = get_updates()[-1]['update_id']
    while True:
        messages = get_updates(update_id)
        if messages is not False:
            for message in messages:
                if update_id < message['update_id']:
                    json_write(message["message"]["from"]["id"], message["message"]["text"], message["message"]["date"])
                    update_id = message['update_id']
                    if "entities" in message["message"]:
                        check_command(message["message"])


if __name__ == "__main__":
    db = DB()
    main()
