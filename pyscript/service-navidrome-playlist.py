import requests
import random, time, asyncio

QUEUE = []
MEDIA_PLAYER    = "media_player.PLAYER_NAME"
NAVIDROME_URL   = "https://URL_NAMER/rest"
USER            = "USER"
PASSWORD        = "PWD"


_playing = False
_index = 0
_playing_task = None

def _log(msg: str, log_type="info"):
    if log_type == "info":
        log.info(f"navidrome_queue: {msg}")
    if log_type == "debug":
        log.debug(f"navidrome_queue: {msg}")
    if log_type == "warning":
        log.warning(f"navidrome_queue: {msg}")
    elif log_type == "error":
        log.error(f"navidrome_queue: {msg}")

def _get_all_songs(playlist_id: int):

    url = f"{NAVIDROME_URL}/getPlaylist?id={playlist_id}&u={USER}&p={PASSWORD}&v=1&c=100"
    
    xml_string = task.executor(requests.get, url).text
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_string)
    entry_ids = [entry.attrib['id'] for entry in root.findall('.//{http://subsonic.org/restapi}entry')]
    random.shuffle(entry_ids)
    global QUEUE
    QUEUE = [eid for eid in entry_ids]
    _log(f"Loaded {len(QUEUE)} songs into queue from playlist {playlist_id}")

async def play_queue():
    global _playing, _index, _playing_task
    _index = 0
    _playing_task = True

    _log("Queue start.")

    while _playing and _index < len(QUEUE):

        song_id = QUEUE[_index]
        scrobble_url = f"{NAVIDROME_URL}/scrobble?u={USER}&p={PASSWORD}&submission=true&id={song_id}&v=1.9&c=1"
        current_song = f"{NAVIDROME_URL}/stream?id={song_id}&u={USER}&p={PASSWORD}&v=1&c=100"

        _log(f"PLAY: {_index+1}/{len(QUEUE)} - {current_song}")

        # --- PLAY TRACK ---    
        service.call(
            "media_player",
            "play_media",
            media_content_type="music",
            media_content_id=current_song,
            entity_id=MEDIA_PLAYER
        )

        # --- Czekamy aż player realnie zacznie grać ---
        for _ in range(20):   # max 10s
            st = state.get(MEDIA_PLAYER)
            if st == "playing":
                break
            await task.sleep(0.5)

        idle_since = None
        last_pos = None
        pos_stuck_since = None

        while True:

            if not _playing:
                _log("Stopped by user.")
                _playing_task = None
                return

            st = state.get(MEDIA_PLAYER)
            attrs = state.getattr(MEDIA_PLAYER)
            pos = attrs.get("media_position")
            dur = attrs.get("media_duration")

            now = time.time()

            # --- CHWILOWE idle/off — ignorujemy do 5 sekund ---
            if st in ("off", "idle"):
                if idle_since is None:
                    idle_since = now
                elif now - idle_since > 5:  # realny idle
                    _log("Media player idle >5s — stop.")
                    _playing_task = None
                    return
            else:
                idle_since = None

            # --- Brak metadanych ---
            if pos is None or dur is None or dur == 0:
                await task.sleep(0.5)
                continue

            # --- Pozycja stoi w miejscu? (utrata strumienia) ---
            if last_pos is not None and pos == last_pos:
                if pos_stuck_since is None:
                    pos_stuck_since = now
                elif now - pos_stuck_since > 8:
                    _log("Position stuck >8s — restart/stop.")
                    _playing_task = None
                    return
            else:
                pos_stuck_since = None
                last_pos = pos

            # --- Koniec utworu ---
            if pos >= dur * 0.98:
                _log(f"Finished: {current_song}")
                task.executor(requests.get, scrobble_url)
                _log(f"Scrobbled: {scrobble_url}")
                _index += 1
                break

            await task.sleep(1)

    _log("Queue done.")
    _playing_task = None




@service()
def start_queue(playlist_id = "50fe70a3-77b6-40e8-bd3e-2fc1e834038b"):
    task.unique(start_queue)
    global QUEUE, _index, _playing, _playing_task
    _log(f"Hit start_queue service, _playing_task {_playing_task}, playliust_id: {playlist_id}")
    if _playing_task is None:
        QUEUE.clear()
        _get_all_songs(playlist_id)
        _playing_task = task.create(play_queue)
        _playing = True 
    
    return {"status": "playing", "queue_length": len(QUEUE)}

@service()
def stop_queue():
    global _playing, _playing_task
    _playing_task = None
    _playing = False
    if state.get(MEDIA_PLAYER) == "playing":
        service.call("media_player", "media_stop", entity_id=MEDIA_PLAYER)
    _log("queue stopped by user")


@service()
def next_queue_song():
    global _index, _playing
    if not _playing: 
        _log("Playback not active.")
        return {"status": "stopped", "message": "Playback not active"}
    
    if _index < len(QUEUE) - 1: 
        _index += 1
        _log(f"Skipping to next song {_index+1}/{len(QUEUE)}: {QUEUE[_index]}")
        current_song = f"{NAVIDROME_URL}/stream?id={QUEUE[_index]}&u={USER}&p={PASSWORD}&v=1&c=100"

        service.call(
            "media_player",
            "play_media",
            media_content_type="music",
            media_content_id=current_song,
            entity_id=MEDIA_PLAYER
        )
        return {"status": "playing", "current_song": QUEUE[_index]}
    else:
        _log("Already on the last song in the queue.")
        return {"status": "finished", "message": "Already on the last song"}

@service()
def previous_queue_song():
    global _index, _playing
    if not _playing: 
        _log("Playback not active.")
        return {"status": "stopped", "message": "Playback not active"}
    
    if _index > 0: 
        _index -= 1
        _log(f"Skipping to previous song {_index+1}/{len(QUEUE)}: {QUEUE[_index]}")
        current_song = f"{NAVIDROME_URL}/stream?id={QUEUE[_index]}&u={USER}&p={PASSWORD}&v=1&c=100"
        service.call(
            "media_player",
            "play_media",
            media_content_type="music",
            media_content_id=current_song,
            entity_id=MEDIA_PLAYER
        )
        return {"status": "playing", "current_song": QUEUE[_index]}
    else:
        _log("Already on the first song in the queue.")
        return {"status": "finished", "message": "Already on the first song"}


@service(supports_response="both")
def navidrome_select_playlist(name=None) :
    url = f"{NAVIDROME_URL}/getPlaylists?u={USER}&p={PASSWORD}&v=1&c=100"
    xml_string = task.executor(requests.get, url).text
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_string)
    playlists = []
    for pl in root.findall('.//{http://subsonic.org/restapi}playlist'):
        playlists.append({
            "id": pl.attrib['id'],
            "name": pl.attrib['name'],
            "songCount": pl.attrib['songCount']
        })
    if name:
        for pl in playlists:
            if pl['name'].lower() == name.lower():
                return {"data": pl}
        return {"error": "Playlist not found"}
        
    return {"data": playlists}


@service()
def navidrome_add_to_favorite():
    attrs = state.getattr(MEDIA_PLAYER)
    media_id = attrs.get("media_content_id").split("id=")[-1]
    _log(f"Adding media id {media_id} to favorites", log_type="error")
    url = f"{NAVIDROME_URL}/star?u={USER}&p={PASSWORD}&id={media_id}&v=1.9&c=1"
    task.executor(requests.get, url)