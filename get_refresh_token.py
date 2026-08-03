"""
Помощник для получения refresh_token от Twitch.
Запуск: python get_refresh_token.py
Спросит Client ID и Client Secret, откроет браузер для авторизации,
сам поймает код и обменяет его на токены.
"""
import http.server
import threading
import urllib.parse
import webbrowser
import requests

REDIRECT_PORT = 3000
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
SCOPE = "moderator:manage:chat_messages"

received_code = {}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        if "code" in params:
            received_code["code"] = params["code"][0]
            self.wfile.write("<h2>Готово! Можно закрыть эту вкладку и вернуться в консоль.</h2>".encode("utf-8"))
        else:
            self.wfile.write("<h2>Ошибка авторизации, код не получен.</h2>".encode("utf-8"))

    def log_message(self, format, *args):
        pass  # не засорять консоль логами сервера


def main():
    client_id = input("Введите Client ID: ").strip()
    client_secret = input("Введите Client Secret: ").strip()

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    auth_url = (
        "https://id.twitch.tv/oauth2/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        f"&scope={urllib.parse.quote(SCOPE)}"
    )

    print("\nОткрываю браузер для авторизации...")
    print("Если не открылся автоматически, перейдите по ссылке:")
    print(auth_url)
    webbrowser.open(auth_url)

    thread.join()  # ждём, пока сервер поймает один запрос (код)

    if "code" not in received_code:
        print("Не удалось получить код авторизации.")
        return

    code = received_code["code"]
    print(f"\nКод получен, обмениваю на токены...")

    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )

    if resp.status_code != 200:
        print(f"Ошибка обмена кода на токен: {resp.status_code}")
        print(resp.text)
        return

    data = resp.json()
    print("\n=== Готово! ===")
    print(f"refresh_token: {data['refresh_token']}")
    print("\nЭто значение нужно положить в GitHub Secret с именем TWITCH_REFRESH_TOKEN.")
    print("Client ID и Client Secret тоже понадобятся отдельными secrets (TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET).")


if __name__ == "__main__":
    main()
