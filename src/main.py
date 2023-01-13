from ui import *
from PyQt5.QtWidgets import QApplication

from yandex_oauth import *

import os
import sys


def oauth_close_event(obj):
    token_ = obj.token

    if token_ is None:
        return

    with open("./cache/.token.txt", "w", encoding='utf-8') as f_:
        f_.write(token_)

    global ui
    ui = YandexMusicApp(token_)
    ui.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if not os.path.exists("./cache"):
        os.makedirs("./cache")
    if not os.path.exists("./cache/playlists_covers"):
        os.makedirs("./cache/playlists_covers")
    if not os.path.exists("./cache/tracks_covers_cache"):
        os.makedirs("./cache/tracks_covers_cache")
    f = open("./cache/queue.txt", "w", encoding="utf-8")
    f.close()
    if os.path.exists("./cache/playing_track_info"):
        os.remove("./cache/playing_track_info")
    if os.path.exists("./cache/lyrics"):
        os.remove("./cache/lyrics")
    if not os.path.exists("./cache/titles_cache.txt"):
        f = open("./cache/titles_cache.txt", "w", encoding="utf-8")
        f.close()

    if os.path.exists("./cache/.token.txt"):
        token = open("./cache/.token.txt", "r", encoding="utf-8").read().strip()
        ui = YandexMusicApp(token)
        ui.show()
    else:
        oauth = YandexOauth()
        oauth.close_event = oauth_close_event
        oauth.show()

    sys.exit(app.exec())
