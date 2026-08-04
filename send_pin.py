"""
Отправляет сообщение(я) из message.txt в чат Twitch и закрепляет последнее.
Чтобы отправить 2 (или больше) сообщения — разделите их в message.txt строкой '---' на отдельной строке.
Пример:
    Первое сообщение (будет закреплено)
    ---
    Второе сообщение
Требует env: TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REFRESH_TOKEN
Выводит новый refresh_token в stdout в формате NEW_REFRESH_TOKEN=... (для сохранения в secrets).
"""
import os
import sys
import requests

CLIENT_ID = os.environ["TWITCH_CLIENT_ID"]
CLIENT_SECRET = os.environ["TWITCH_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["TWITCH_REFRESH_TOKEN"]

MESSAGE_FILE = os.path.join(os.path.dirname(__file__), "message.txt")


def refresh_access_token():
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"], data["refresh_token"]


def get_user_id(access_token):
    resp = requests.get(
        "https://api.twitch.tv/helix/users",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": CLIENT_ID,
        },
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["id"]


def clear_chat(access_token, broadcaster_id):
    resp = requests.delete(
        "https://api.twitch.tv/helix/moderation/chat",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": CLIENT_ID,
        },
        params={
            "broadcaster_id": broadcaster_id,
            "moderator_id": broadcaster_id,
        },
    )
    resp.raise_for_status()


def send_message(access_token, broadcaster_id, message):
    payload = {
        "broadcaster_id": broadcaster_id,
        "sender_id": broadcaster_id,
        "message": message,
    }

    resp = requests.post(
        "https://api.twitch.tv/helix/chat/messages",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": CLIENT_ID,
            "Content-Type": "application/json",
        },
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


def pin_message(access_token, broadcaster_id, message_id):
    resp = requests.put(
        "https://api.twitch.tv/helix/chat/pins",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": CLIENT_ID,
        },
        params={
            "broadcaster_id": broadcaster_id,
            "moderator_id": broadcaster_id,
            "message_id": message_id,
        },
    )
    resp.raise_for_status()


def load_messages():
    """
    Читает message.txt. Несколько сообщений разделяются строкой '---' на отдельной строке.
    Если разделителя нет — считается, что сообщение одно (весь файл).
    """
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    parts = [p.strip() for p in content.split("\n---\n")]
    # на случай разделителя в самом конце/начале файла без лишних пустых частей
    messages = [p for p in parts if p]
    return messages


def main():
    messages = load_messages()

    if not messages:
        print("message.txt пуст, нечего отправлять", file=sys.stderr)
        sys.exit(1)

    access_token, new_refresh_token = refresh_access_token()
    broadcaster_id = get_user_id(access_token)

    clear_chat(access_token, broadcaster_id)
    print("Чат очищен")

    for i, message in enumerate(messages):
        is_first = i == 0
        try:
            result = send_message(access_token, broadcaster_id, message)
        except requests.HTTPError as e:
            print(f"Сообщение {i + 1}/{len(messages)} НЕ отправлено: {message!r}", file=sys.stderr)
            print(f"Ошибка Twitch: {e.response.status_code} {e.response.text}", file=sys.stderr)
            continue

        print(f"Сообщение {i + 1}/{len(messages)} отправлено: {message!r}")
        print(result)

        if is_first:
            message_id = result["data"][0]["message_id"]
            try:
                pin_message(access_token, broadcaster_id, message_id)
                print("Сообщение закреплено")
            except requests.HTTPError as e:
                print(f"Не удалось закрепить: {e.response.status_code} {e.response.text}", file=sys.stderr)

    if new_refresh_token != REFRESH_TOKEN:
        print(f"NEW_REFRESH_TOKEN={new_refresh_token}")


if __name__ == "__main__":
    main()
