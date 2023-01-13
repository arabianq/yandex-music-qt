from raw_ui import *
from PyQt5.QtCore import QSize, QUrl, QTimer
from PyQt5.QtWidgets import QMainWindow, QMenu, QTextEdit
from PyQt5.Qt import QIcon, QSystemTrayIcon, QAction, QListWidgetItem, QImage, QColor, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import yamusic
import lyricsgenius

import os
import random
import multiprocessing as mp


class YandexMusicApp(Ui_YaMusic, QMainWindow):
    def __init__(self, token: str):
        super().__init__()

        """ Setting up main window """
        self.show()
        self.setupUi(self)
        self.setWindowTitle("Яндекс Музыка")
        self.setFixedSize(QSize(1066, 748))
        self.setWindowIcon(QIcon("./data/icons/icon.svg"))
        self.playPlaylistButton.setHidden(True)

        """ Setting up variables"""
        self.media_player = QMediaPlayer()
        self.client = yamusic.init_client(token)

        self.genius = lyricsgenius.Genius("ErZjOUJo3Thxh3hsgA2jWvSPDRQw8yN6u12gCQxJVb2UuIpeMcShj1kgEe3POJqs")
        self.genius.verbose = False
        self.genius.remove_section_headers = True
        self.genius.skip_non_songs = True

        self.playing_queue = []
        self.showing_queue = []
        self.users_playlists = yamusic.get_all_users_playlists(self.client)

        self.is_track_playing = False
        self.was_track_playing = False
        self.auto_move_lyrics = True

        self.playing_track_index = 0
        self.loop_state = 0  # 0 - don't loop, 1 - loop playlist, 2 - loop track

        self.current_playing_track = None
        self.current_playing_track_url = None
        self.current_playing_track_path = None
        self.current_playing_track_lyrics = None
        self.current_playing_track_info = None
        self.current_playing_playlist = None
        self.showing_playlist = None

        self.queue_loading_process = None
        self.track_loader_process = None
        self.genius_fetching_process = None

        """ Setting up update timer """
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(False)
        self.update_timer.setInterval(10)
        self.update_timer.timeout.connect(self.update_func)
        self.update_timer.start()

        """ Setting up icons """
        self.playButton.setIcon(QIcon("./data/icons/play.svg"))
        self.playButton.setIconSize(QSize(32, 32))

        self.nextTrack.setIcon(QIcon("./data/icons/next.svg"))
        self.nextTrack.setIconSize(QSize(32, 32))

        self.prevTrack.setIcon(QIcon("./data/icons/prev.svg"))
        self.prevTrack.setIconSize(QSize(32, 32))

        self.shuffleButton.setIcon(QIcon("./data/icons/shuffle.svg"))
        self.shuffleButton.setIconSize(QSize(24, 24))

        self.loopButton.setIcon(QIcon("./data/icons/loop0.svg"))
        self.loopButton.setIconSize(QSize(24, 24))

        self.playerToolButton.setIcon(QIcon("./data/icons/menu.svg"))
        self.playerToolButton.setIconSize(QSize(16, 16))

        self.showQueueButton.setIcon(QIcon("./data/icons/queue.svg"))
        self.showQueueButton.setIconSize(QSize(16, 16))

        """ Setting up tray icon """
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("./data/icons/icon.png"))

        show_action = QAction("Показать", self)
        # show_action.triggered.connect()

        exit_action = QAction("Закрыть", self)
        # exit_action.triggered.connect()

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

        """ Setting up lyrics window """
        self.lyrics_ui = QMainWindow()
        self.lyrics_ui.setWindowTitle("Текст")
        self.lyrics_text_edit = QTextEdit(self.lyrics_ui)
        self.lyrics_text_edit.setMinimumSize(100, 100)
        self.lyrics_ui.resize(300, self.height())
        self.lyrics_text_edit.setReadOnly(True)
        self.lyrics_ui.setCentralWidget(self.lyrics_text_edit)

        """ Setting up media player tools """
        self.playerToolMenu = QMenu(self.playerToolButton)
        self.playerToolButton.setMenu(self.playerToolMenu)

        lyrics_action = QAction(parent=self, text="Текст Трека")
        lyrics_action.triggered.connect(self.get_track_lyrics)
        self.playerToolMenu.addAction(lyrics_action)

        """ Setting up library widget """
        self.libraryList.clear()
        for playlist in self.users_playlists:
            title = playlist["title"]
            item = QListWidgetItem(title)
            self.libraryList.addItem(item)
        self.libraryList.itemClicked.connect(self.playPlaylistButton.show)

        """ Binding events """
        self.libraryList.itemClicked.connect(lambda i: self.show_playlist(i))
        self.queueList.itemClicked.connect(lambda i: self.set_track(i))

        self.showQueueButton.clicked.connect(lambda: self.show_playlist(playlist=self.current_playing_playlist,
                                                                        title="Очередь воспроизведения"))

        self.playButton.clicked.connect(self.pause_unpause_track)
        self.nextTrack.clicked.connect(self.set_next_track)
        self.prevTrack.clicked.connect(self.set_previous_track)
        self.playPlaylistButton.clicked.connect(lambda: self.play_playlist(self.showing_playlist))
        self.shuffleButton.clicked.connect(lambda: self.shuffle())
        self.loopButton.clicked.connect(self.change_loop)

        self.timeSlider.sliderPressed.connect(lambda: self.pause_unpause_track() if self.is_track_playing else None)
        self.timeSlider.sliderReleased.connect(lambda: self.pause_unpause_track() if self.was_track_playing else None)
        self.timeSlider.sliderMoved.connect(lambda value: self.media_player.setPosition(value))

        self.volumeSlider.valueChanged.connect(lambda value: self.media_player.setVolume(value))
        self.volumeSlider.valueChanged.connect(lambda value: self.volumeSlider.setToolTip(str(value)))

        self.queueSearchLineEdit.textEdited.connect(self.update_queue_widget)

    def update_func(self):
        pass

        if self.auto_move_lyrics:
            main_x, main_y = self.x(), self.y()
            main_width = self.width()
            lyrics_width = self.lyrics_ui.width()
            if main_x - lyrics_width >= 0:
                self.lyrics_ui.move(main_x - lyrics_width, main_y)
            else:
                self.lyrics_ui.move(main_x + main_width, main_y)

        """ Selecting current playing track """
        if self.current_playing_track and self.current_playing_track_info:
            for i in range(self.queueList.count()):
                item = self.queueList.item(i)
                item_text = item.text()
                current_title = self.current_playing_track_info["title"]
                current_artists = self.current_playing_track_info["artists"]
                current_track_name = current_title + " - " + current_artists
                if len(current_track_name) > 50:
                    current_track_name = current_track_name[:50] + "..."
                if current_track_name == item_text:
                    item.setSelected(True)
                    break

        """ Set next track if current one is over """
        if self.media_player.state() == 0 and self.is_track_playing:
            self.set_next_track()

        """ Update time indicator according to time slider """
        seconds = self.timeSlider.value() // 1000
        minutes = seconds // 60
        seconds -= minutes * 60

        if minutes < 10:
            minutes = "0" + str(minutes)
        if seconds < 10:
            seconds = "0" + str(seconds)

        self.trackTimer.setText(f"{minutes}:{seconds}")

        """ Sync time slider to media player """
        if self.is_track_playing:
            time_passed = self.media_player.position()
            self.timeSlider.setValue(time_passed)

        """ Completely remove queue loading process if it is not alive anymore """
        if self.queue_loading_process and not self.queue_loading_process.is_alive():
            self.queue_loading_process = None

        """ Update queue list widget if there are new tracks """
        if self.queueList.count() != len(self.showing_queue):
            self.update_queue_widget()

        """ Get new track info """
        if os.path.exists("./cache/playing_track_info"):
            with open("./cache/playing_track_info", "r", encoding="utf-8") as f:
                info = f.read().strip().split(":/:")
                if info:
                    track_id = info[0]
                    title = info[1]
                    artists = info[2]
                    url = info[3]
                    track_duration = info[4]
                    is_available = info[5]
                    lyrics = info[6]

                    self.current_playing_track_info = {
                        "track_id": track_id,
                        "title": title,
                        "artists": artists,
                        "url": url,
                        "track_duration": track_duration,
                        "lyrics": lyrics
                    }

                    self.trackTitle.setText(title)
                    self.trackAuthor.setText(artists)
                    self.current_playing_track_url = url

                    cover_img = QImage(f"./cache/tracks_covers_cache/{track_id}.png")
                    cover_pixmap = QPixmap(cover_img)
                    self.trackCover.setPixmap(cover_pixmap)

                    self.timeSlider.setMaximum(int(track_duration))

                    os.remove("./cache/playing_track_info")

                    if is_available == "True":
                        self.play_track()
                    else:
                        self.set_next_track()

        """ Get genius lyrics """
        if os.path.exists("./cache/lyrics") and self.current_playing_track_info:
            self.current_playing_track_info["lyrics"] = open("./cache/lyrics", "r", encoding='utf-8').read().strip()
            if self.current_playing_track_info["lyrics"]:
                self.lyrics_ui.setWindowTitle(self.current_playing_track_info["title"] + " - Текст (Genius)")
                self.lyrics_text_edit.setText(self.current_playing_track_info["lyrics"])
            else:
                self.lyrics_ui.setWindowTitle(self.current_playing_track_info["title"] + " - Текст")
                self.lyrics_text_edit.setText("Текст не найден")
            os.remove("./cache/lyrics")

    def set_track(self, item: QListWidgetItem = None):
        self.stop_track()

        if self.track_loader_process and self.track_loader_process.is_alive():
            self.track_loader_process.terminate()
        self.track_loader_process = None

        if item is not None:
            short_track = self.showing_queue[self.queueList.row(item)]
            self.playing_track_index = self.queueList.row(item)
            self.playing_queue = self.showing_queue
            self.current_playing_playlist = self.showing_playlist
        else:
            short_track = self.playing_queue[self.playing_track_index]

        self.current_playing_track = short_track

        self.track_loader_process = mp.Process(target=self.load_track_info, args=(self.playing_track_index,))
        self.track_loader_process.daemon = True
        self.track_loader_process.start()

    def update_queue_widget(self):
        with open("./cache/queue.txt") as f:
            queue = [line.strip() for line in f.readlines()]
            if queue:
                self.queueList.clear()
                for i in range(len(queue)):
                    title = queue[i]
                    item = QListWidgetItem(title)

                    track_id = self.showing_queue[i].id
                    if os.path.exists(f"./cache/tracks_covers_cache/{track_id}.png"):
                        item.setIcon(QIcon(f"./cache/tracks_covers_cache/{track_id}.png"))

                    self.queueList.addItem(item)

                    filtering_text = self.queueSearchLineEdit.text()
                    if filtering_text and filtering_text.lower() not in title.lower():
                        item.setHidden(True)

    def show_playlist(self, item: QListWidgetItem = None, playlist=None, title=None):
        if playlist is None and item is None:
            return

        if playlist is None:
            playlist: dict = self.users_playlists[self.libraryList.row(item)]
            item.setSelected(True)
        else:
            for i in range(self.libraryList.count()):
                item = self.libraryList.item(i)
                item.setSelected(False)
        self.showing_playlist = playlist

        if self.queue_loading_process:
            if self.queue_loading_process.is_alive():
                self.queue_loading_process.terminate()
            self.queue_loading_process = None

        with open("./cache/queue.txt", "w", encoding="utf-8") as f:
            f.close()

        if title is None:
            title = playlist["title"]
        self.queueLabel.setText(title)

        self.showing_queue = playlist["short_tracks_list"]
        self.queueList.clear()
        self.queue_loading_process = mp.Process(target=self.load_queue)
        self.queue_loading_process.daemon = True
        self.queue_loading_process.start()

    def load_queue(self):
        titles_cache_file = open("./cache/titles_cache.txt", "r", encoding="utf-8")
        titles_cache_lines = [line.strip() for line in titles_cache_file.readlines()]
        titles_cache_file.close()
        titles_cache = {}
        for line in titles_cache_lines:
            line = line.split(":/:")
            titles_cache[line[0]] = [line[1], line[2]]

        for short_track in self.showing_queue:
            f = open("./cache/queue.txt", "a", encoding="utf-8")
            track_id = str(short_track.id)

            track = None

            if not os.path.exists(f"./cache/tracks_covers_cache/{track_id}.png"):
                track = yamusic.fetch_track(self.client, short_track)
                if track.cover_uri:
                    track.download_cover(f"./cache/tracks_covers_cache/{track_id}.png", "50x50")
                else:
                    img = QImage(50, 50, QImage.Format_RGB32)
                    img.fill(QColor(0, 0, 0))
                    img.save(f"./cache/tracks_covers_cache/{track_id}.png")

            if track_id in titles_cache.keys():
                title = titles_cache[track_id][0]
                artists = titles_cache[track_id][1]
            else:
                track = yamusic.fetch_track(self.client, short_track) if track is None else track
                title = track.title
                artists = ", ".join([artist.name for artist in track.artists])

                titles_cache[track_id] = [title, artists]

                titles_cache_file = open("./cache/titles_cache.txt", "a", encoding="utf-8")
                titles_cache_file.write(f"{track_id}:/:{title}:/:{artists}\n")
                titles_cache_file.close()

            res = title + " - " + artists
            if len(res) > 50:
                res = res[:50] + "..."

            f.write(res + "\n")
            f.close()

    def load_track_info(self, track_index: int = None, short_track: yamusic.ym.TrackShort = None):
        if os.path.exists("./cache/playing_track_info"):
            os.remove("./cache/playing_track_info")

        if short_track is None and track_index is None:
            return
        elif short_track is None:
            short_track = self.playing_queue[track_index]

        track = yamusic.fetch_track(self.client, short_track)

        if not os.path.exists(f"./cache/tracks_covers_cache/{track.id}.png"):
            if track.cover_uri:
                track.download_cover(f"./cache/tracks_covers_cache/{track.id}.png", "50x50")
            else:
                img = QImage(50, 50, QImage.Format_RGB32)
                img.fill(QColor(0, 0, 0))
                img.save(f"./cache/tracks_covers_cache/{track.id}.png")

        cover_img = QImage(f"./cache/tracks_covers_cache/{track.id}.png")
        cover_pixmap = QPixmap(cover_img)
        self.trackCover.setPixmap(cover_pixmap)

        title = track.title
        artists = ", ".join([artist.name for artist in track.artists])
        track_id = track.id
        is_available = track.available
        url = yamusic.get_track_download_url(self.client, track) if is_available else " "
        track_duration = track.duration_ms if is_available else 0
        additional_info = self.client.track_supplement(track_id)
        lyrics = additional_info.lyrics.full_lyrics if additional_info.lyrics else " "

        playing_track_info = f"{track_id}:/:{title}:/:{artists}:/:{url}:/:{track_duration}:/:{is_available}:/:{lyrics}"

        with open("cache/playing_track_info", "w", encoding="utf-8") as f:
            f.write(playing_track_info)

    def play_track(self):
        self.was_track_playing = self.is_track_playing
        self.is_track_playing = True

        if self.current_playing_track_url:
            url = QUrl(self.current_playing_track_url)
        else:
            url = None
            return
        content = QMediaContent(url)
        self.media_player.setMedia(content)
        self.media_player.setVolume(self.volumeSlider.value())
        self.media_player.play()

        self.playButton.setIcon(QIcon("./data/icons/pause.svg"))

    def stop_track(self):
        self.was_track_playing = self.is_track_playing
        self.is_track_playing = False

        self.current_playing_track = None
        self.current_playing_track_url = None
        self.current_playing_track_path = None
        self.current_playing_track_lyrics = None
        self.current_playing_track_info = None

        if self.track_loader_process is not None and self.track_loader_process.is_alive():
            self.track_loader_process.terminate()
        self.track_loader_process = None

        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())

        self.timeSlider.setValue(0)
        self.playButton.setIcon(QIcon("./data/icons/play.svg"))

    def pause_unpause_track(self):
        self.was_track_playing = self.is_track_playing
        self.is_track_playing = not self.is_track_playing

        if self.media_player.state() == 1:
            self.media_player.pause()
            self.playButton.setIcon(QIcon("./data/icons/play.svg"))
        elif self.media_player.state() == 2:
            self.media_player.play()
            self.playButton.setIcon(QIcon("./data/icons/pause.svg"))

    def play_playlist(self, playlist):
        if playlist is None:
            return

        self.current_playing_playlist = playlist

        tracks = playlist["short_tracks_list"]
        self.playing_queue = tracks
        self.playing_track_index = 0

        self.set_track()

    def shuffle(self, queue=None):
        if queue is None:
            queue = self.playing_queue

        if not queue:
            return

        self.stop_track()
        random.shuffle(queue)
        self.current_playing_playlist["short_tracks_list"] = queue
        self.set_track()
        self.show_playlist(playlist=self.current_playing_playlist)

    def change_loop(self):
        if self.loop_state == 0:
            self.loop_state = 1
            self.loopButton.setIcon(QIcon("./data/icons/loop1.svg"))
        elif self.loop_state == 1:
            self.loop_state = 2
            self.loopButton.setIcon(QIcon("./data/icons/loop2.svg"))
        elif self.loop_state == 2:
            self.loop_state = 0
            self.loopButton.setIcon(QIcon("./data/icons/loop0.svg"))

    def set_next_track(self):
        self.stop_track()
        if self.loop_state == 0:
            if self.playing_track_index + 1 == len(self.playing_queue):
                return
            self.playing_track_index += 1
        elif self.loop_state == 1:
            if self.playing_track_index + 1 == len(self.playing_queue):
                self.playing_track_index = 0
            else:
                self.playing_track_index += 1
        elif self.loop_state == 2:
            pass

        self.set_track()

    def set_previous_track(self):
        self.stop_track()
        if self.loop_state == 0:
            if self.playing_track_index - 1 == -1:
                return
            self.playing_track_index -= 1
        elif self.loop_state == 1:
            if self.playing_track_index - 1 == -1:
                self.playing_track_index = len(self.playing_queue) - 1
            else:
                self.playing_track_index -= 1
        elif self.loop_state == 2:
            pass

        self.set_track()

    def get_track_lyrics(self):
        if self.current_playing_track_info is None:
            return

        self.lyrics_ui.close()

        lyrics = self.current_playing_track_info["lyrics"]
        if not lyrics:
            if self.genius_fetching_process and self.genius_fetching_process.is_alive():
                self.genius_fetching_process.terminate()
            self.genius_fetching_process = None

            self.genius_fetching_process = mp.Process(target=self.fetch_lyrics_from_genius)
            self.genius_fetching_process.daemon = True
            self.genius_fetching_process.start()

        self.lyrics_ui.setWindowTitle(self.current_playing_track_info["title"] + " - Текст (Яндекс Музыка)")
        self.lyrics_text_edit.setText(lyrics if lyrics else "Поиск текста...")
        self.lyrics_ui.show()

    def fetch_lyrics_from_genius(self):
        if not yamusic.is_connected_to_internet():
            return ""

        lyrics = ""
        song = self.genius.search_song(
            title=self.current_playing_track_info["title"],
            artist=self.current_playing_track_info["artists"].split(",")[0],
        )

        if song is None:
            song = self.genius.search_song(
                title=self.current_playing_track_info["title"])

        if song:
            lyrics = song.lyrics

        with open("./cache/lyrics", "w", encoding="utf-8") as f:
            f.write(lyrics)
