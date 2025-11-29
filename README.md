# ESP-S3 Box Player with Navidrome and Home Assistant Integration

This project integrates an ESP32-S3 Box with Navidrome and Home Assistant to create a music player with a touchscreen interface. It allows users to control playback, select playlists, and monitor media player states.

## Features

- **Playlist Management**: Load and play playlists from Navidrome.
- **Playback Control**: Play, stop, skip to the next/previous song, and adjust volume.
- **Touchscreen Interface**: Control playback and select playlists directly from the ESP32-S3 Box touchscreen.
- **Home Assistant Integration**: Synchronize media player states and control additional devices.

---

## Components

### 1. Python Script: `service-navidrome-playlist.py`

This script handles the interaction with the Navidrome API and manages the playback queue.

#### Key Features:
- Fetches songs from a Navidrome playlist and shuffles them.
- Controls playback (start, stop, next, previous).
 - Provides a service to select playlists by name.
- Logs playback events for debugging.

#### Services:
- `start_queue(playlist_id)`: Starts playback of the specified playlist.
- `stop_queue()`: Stops playback.
- `next_queue_song()`: Skips to the next song in the queue.
- `previous_queue_song()`: Returns to the previous song in the queue.
- `navidrome_select_playlist()`: Retrieves playlists from Navidrome, optionally filtering by name.

---

### 2. ESPHome Configuration: `esp-s3-box-playa.yaml`

This configuration sets up the ESP32-S3 Box with a touchscreen interface for controlling playback.

#### Key Features:

- **Hardware Buttons**:
  - Top left button - adjustable switch entity (toggle)
  - Home button - adjustable brightness (4 varius levels)

- **Touchscreen Buttons**:
  - Play, Stop, Next, Previous, Volume Up, Volume Down, Add to Favourite.
  - Dropdown menu for playlist selection.
- **Display**:
  - Shows current song title, artist, and playback status.
  - Displays sensor data at the bottom of the screen.
- **Home Assistant Integration**:
  - Mirrors media player state and controls additional devices (e.g., switches, sensors).

#### Substitutions:
- `playlists_text`: Display names of playlists.
- `player_name`: Home Assistant media player entity.
- `switch_1` and `switch_2`: Additional switches for toggling devices.
- `sensor_1` to `sensor_4`: Sensors displayed on the screen.

#### Globals:
- `playlist_options`: Stores playlist names and IDs.
- `selected_playlist_id`: Tracks the currently selected playlist.

#### Fonts:
- Custom fonts for text and icons.

#### API and OTA:
- Enables remote updates and API communication.

---

## Setup Instructions

### 1. Python Script

1. Configure the script:
   - Set `NAVIDROME_URL`, `USER`, and `PASSWORD` in `service-navidrome-playlist.py`.
2. Deploy the script to your Home Assistant `pyscript` directory.

### 2. ESPHome Configuration
1. Update the `esp-s3-box-playa.yaml` file:
   - Replace `static_ip`, `gateway`, and `dns1` with your network configuration.
   - Set `wifi_ssid` and `wifi_password` in your ESPHome secrets file.
   - Update `playlists_text` and `playlist_options` with your Navidrome playlists.
2. Flash the configuration to your ESP32-S3 Box.

---

## Usage

### Touchscreen Controls
- **Play**: Starts playback of the selected playlist.
- **Stop**: Stops playback.
- **Next/Previous**: Skips to the next or previous song.
- **Volume Up/Down**: Adjusts the volume.
- **Dropdown Menu**: Selects a playlist.

### Home Assistant
- Use the `pyscript` services to control playback:
  - `pyscript.start_queue`
  - `pyscript.stop_queue`
  - `pyscript.next_queue_song`
  - `pyscript.previous_queue_song`
  - `pyscript.navidrome_select_playlist`

---

## Example Interface

Below is an example of the ESP32-S3 Box interface:

![Example Interface](screen.jpg)

---

## Example Playlist Configuration

In `esp-s3-box-playa.yaml`:
```yaml
playlists_text:
  - Samochodowa
  - Sorround
  - Ulubione
  - Sweta
```
Please also modify the IDs in the same order the above on lines 342:
```yaml
- lambda: |-
    if (id(playlist_options).empty()) {
     id(playlist_options).push_back("Samochodowa|13452774-17c4-42e5-a15b-ef816b8bcb9d");
      id(playlist_options).push_back("Sorround|db5b3414-ca58-4560-a50b-0268366be8f2");
       id(playlist_options).push_back("Ulubione|50fe70a3-77b6-40e8-bd3e-2fc1e834038b");
       id(playlist_options).push_back("Sweta|1c59c757-778e-4d02-99da-7bfed7a33e2e");
    }
```

**Note**: Ensure that the playlist IDs in `playlist_options` are provided in the same order as their corresponding names in `playlists_text`. This mapping is critical for proper functionality.

---

## Troubleshooting

- **Playback Issues**: Check the logs in Home Assistant for errors.
- **Touchscreen Not Responding**: Verify the `i2c` and `touchscreen` configuration in `esp-s3-box-playa.yaml`.
- **Network Issues**: Ensure the ESP32-S3 Box is connected to the correct Wi-Fi network.

---

## License

This project is licensed under the MIT License.
