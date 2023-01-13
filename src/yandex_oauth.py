from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtCore import QUrl, QRect


class YandexOauth(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(YandexOauth, self).__init__(*args, **kwargs)

        self.close_event = None
        self.token = None

        self.setWindowTitle("Yandex Oauth")
        self.setFixedSize(450, 700)

        self.browser = QWebEngineView()
        #self.browser.setGeometry(QRect(0, 0, 500, 700))

        self.profile = QWebEngineProfile("yandex-music-qt", self.browser)

        self.cookies = []
        self.profile.cookieStore().cookieAdded.connect(lambda cookie: self.cookies.append(cookie))

        self.page = QWebEnginePage(self.profile)
        self.browser.setPage(self.page)
        self.profile = self.browser.page().profile()

        url = "https://oauth.yandex.ru/authorize?response_type=token&client_id=23cabbbdc6cd418abb4b39c32c41195d"
        self.browser.load(QUrl(url))
        #self.browser.setUrl(QUrl(url))

        self.browser.urlChanged.connect(self.url_changed)

        self.setCentralWidget(self.browser)

    def url_changed(self, url):
        global token
        url = url.url()
        if "#access_token" not in url:
            return
        token = url.split("#access_token=")[1].split("&")[0]
        self.token = token
        self.close()

    def closeEvent(self, a0):
        if self.close_event is None:
            return
        self.profile.cookieStore().deleteAllCookies()
        self.close_event(self)
