import yandex_music as ym
from yandex_music.exceptions import *

import socket
import multiprocessing as mp

from exceptions import *


def is_connected_to_internet():
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False


def init_client(token: str = "") -> ym.Client:
    if not is_connected_to_internet():
        return None

    if not token:
        raise InvalidToken("Invalid Token")
    while True:
        try:
            return ym.Client(token=token).init()
        except NetworkError:
            continue


def fetch_track(client: ym.Client, short_track: ym.TrackShort) -> ym.Track or None:
    if not is_connected_to_internet():
        return None

    while True:
        try:
            return client.tracks(short_track.id)[0]
        except NetworkError:
            continue


def fetch_tracks(client: ym.Client, short_tracks_list: list, pool: mp.Pool = None) -> list:
    if not short_tracks_list:
        return []

    if not is_connected_to_internet():
        return []

    args = [(client, short_tracks_list[i]) for i in range(len(short_tracks_list))]
    pool = mp.Pool(mp.cpu_count() - 1) if pool is None else pool
    return pool.starmap(fetch_track, args)


def fetch_playlist(client: ym.Client, playlist: ym.Playlist) -> dict:
    if not is_connected_to_internet():
        return {}

    while True:
        try:
            playlist = client.users_playlists(playlist.kind, playlist.owner.uid)
            break
        except NetworkError:
            continue
    title = playlist.title
    kind = playlist.kind
    owner_id = playlist.owner.uid
    cover = playlist.cover
    short_tracks_list = [short_track for short_track in playlist.tracks]

    return {
        "title": title,
        "kind": kind,
        "owner_id": owner_id,
        "cover": cover,
        "short_tracks_list": short_tracks_list
    }


def get_liked_playlist(client: ym.Client) -> dict:
    if not is_connected_to_internet():
        return {}

    title = "Понравившиеся"
    kind = None
    owner_id = None
    cover = None
    short_tracks = None
    while True:
        try:
            short_tracks = client.users_likes_tracks()
            break
        except NetworkError:
            continue
    short_tracks_list = [short_track for short_track in short_tracks]

    return {
        "title": title,
        "kind": kind,
        "owner_id": owner_id,
        "cover": cover,
        "short_tracks_list": short_tracks_list
    }


def get_users_playlists(client: ym.Client, pool: mp.Pool = None) -> list:
    if not is_connected_to_internet():
        return []

    raw_playlists = []
    while True:
        try:
            raw_playlists = [playlist for playlist in client.users_playlists_list()]
            break
        except NetworkError:
            continue

    if not raw_playlists:
        return []

    args = [(client, raw_playlists[i]) for i in range(len(raw_playlists))]

    pool = mp.Pool(mp.cpu_count() - 1) if pool is None else pool
    return pool.starmap(fetch_playlist, args)


def get_all_users_playlists(client: ym.Client) -> list:
    return [get_liked_playlist(client)] + get_users_playlists(client)


def get_track_download_url(client: ym.Client, track: ym.Track or ym.TrackShort) -> str:
    if not is_connected_to_internet():
        return ""

    while True:
        try:
            link = sorted(client.tracks_download_info(track.id, True),
                          key=lambda x: x["bitrate_in_kbps"],
                          reverse=True)[0].get_direct_link()
            return link
        except NetworkError:
            print("ERROR")
            continue


def get_tracks_download_urls(client: ym.Client, tracks: list, pool: mp.Pool = None) -> list:
    args = [(client, track) for track in tracks]
    pool = mp.Pool(mp.cpu_count() - 1) if pool is None else pool
    return pool.starmap(get_track_download_url, args)
