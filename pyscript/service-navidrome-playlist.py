import requests
import random, time

QUEUE = []
MEDIA_PLAYER    = "media_player.home_player"
NAVIDROME_URL   = "https://NAVIDROME-RUL/rest"
USER            = ""
PASSWORD        = ""


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
    QUEUE = [f"{NAVIDROME_URL}/stream?u={USER}&p={PASSWORD}&v=1.9&c=1&id={eid}" for eid in entry_ids]
    _log(f"Loaded {len(QUEUE)} songs into queue from playlist {playlist_id}")

async def play_queue():
    global _playing, _index, _playing_task
    _index = 0
    last_duration = None

    while _playing and _index < len(QUEUE):
        current_song = QUEUE[_index]
        _log(f"Playing song {_index+1}/{len(QUEUE)}: {current_song}")

        service.call(
            "media_player",
            "play_media",
            media_content_type="music",
            media_content_id=current_song,
            entity_id=MEDIA_PLAYER
        )
        
        # ---- WAIT FOR NEW METADATA ----
        startup_timeout = time.time() + 13
        while True:
            if not _playing:   # Jeśli odtwarzanie zostało zatrzymane
                _log("Playback stopped during startup wait.")
                return

            attrs = state.getattr(MEDIA_PLAYER)
            pos = attrs.get("media_position")
            dur = attrs.get("media_duration")
            
            
            if pos is not None and pos < 1:
                if dur is None or dur != last_duration:
                    break

            if time.time() > startup_timeout:
                _log("Timeout waiting for new track metadata.")
                
                break

            await task.sleep(1)

        last_duration = attrs.get("media_duration")
        started = time.time()

        # ---- MONITOR PLAYBACK ----
        while True:
            if not _playing:      
                _log("Playback stopped by user while playing.")
                
                return

            st = state.get(MEDIA_PLAYER)
            attrs = state.getattr(MEDIA_PLAYER)

            pos = attrs.get("media_position")
            dur = attrs.get("media_duration")

            _log(f"Waiting for new track metadata, pos: {pos}, dur: {dur}", log_type="debug")
 
            # Media player turned off
            if st == "off":
                _log("Media player turned off.")
                return

            if pos is None or dur is None or dur == 0:
                await task.sleep(2)
                continue

            if pos >= dur * 0.98:
                _log(f"Song {_index+1} finished after {int(time.time() - started)} seconds")
                _index += 1
                break

            await task.sleep(2)

    _log("Queue finished.")
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
        service.call(
            "media_player",
            "play_media",
            media_content_type="music",
            media_content_id=QUEUE[_index],
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
        service.call(
            "media_player",
            "play_media",
            media_content_type="music",
            media_content_id=QUEUE[_index],
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

