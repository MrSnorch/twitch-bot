"""
Отправляет сообщение из message.txt в чат Twitch и закрепляет его.
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


def send_and_pin_message(access_token, broadcaster_id, message):
    resp = requests.post(
        "https://api.twitch.tv/helix/chat/messages",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": CLIENT_ID,
            "Content-Type": "application/json",
        },
        json={
            "broadcaster_id": broadcaster_id,
            "sender_id": broadcaster_id,
            "message": message,
            "pin": True,
        },
    )
    resp.raise_for_status()
    return resp.json()


def main():
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        message = f.read().strip()

    if not message:
        print("message.txt пуст, нечего отправлять", file=sys.stderr)
        sys.exit(1)

    access_token, new_refresh_token = refresh_access_token()
    broadcaster_id = get_user_id(access_token)
    result = send_and_pin_message(access_token, broadcaster_id, message)

    print(f"Отправлено и закреплено: {message!r}")
    print(result)

    if new_refresh_token != REFRESH_TOKEN:
        print(f"NEW_REFRESH_TOKEN={new_refresh_token}")


if __name__ == "__main__":
    main()
