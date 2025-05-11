import os
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from googleapiclient.discovery import build

app = Flask(__name__)
YOUTUBE_API_KEY = 'AIzaSyBNLDTSgS_C6jSwlpDx_1eN1I_Kjj2iyyA'  # Pylex'te direkt olarak kullanabilirsiniz
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Tuana Özür Dilerim</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
    <style>
        :root {
            --primary-color: #ff4d4d;
            --bg-color: #000000;
            --text-color: #fff;
            --message-bg: rgba(255,77,77,0.1);
            --message-text: #fff;
            --message-border: #ff4d4d;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            position: relative;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        .watermark {
            content: " TUANA ÖZÜR DİLERİM ";
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            text-align: center;
            font-size: 48px;
            color: rgba(255,77,77,0.2);
            font-weight: bold;
            pointer-events: none;
            z-index: 0;
            padding: 20px 0;
            font-family: "Segoe UI Emoji", "Apple Color Emoji", sans-serif;
        }
        #messages {
            margin-bottom: 60px;
        }
        #roomSetup { 
            padding: 20px;
            background-color: rgba(0,0,0,0.7);
            border-radius: 15px;
            border: 2px solid #ff4d4d;
        }
        #musicRoom { 
            display: none;
            padding: 20px;
        }
        .room-container {
            max-width: 600px;
            width: 95%;
            margin: 0 auto;
            text-align: center;
            padding: 15px;
            background-color: rgba(0,0,0,0.7);
            border-radius: 15px;
            border: 2px solid #ff4d4d;
        }
        h2, h3 { 
            color: #ff4d4d;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        button {
            background-color: #ff4d4d !important;
            color: white !important;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 16px;
            width: 100%;
            max-width: 300px;
            margin: 10px 0;
        }
        button:hover {
            background-color: #ff1a1a !important;
            transform: scale(1.05);
        }
        input {
            background-color: var(--bg-color);
            border: 1px solid var(--primary-color);
            color: var(--text-color);
            padding: 12px;
            border-radius: 20px;
            margin: 5px;
            width: calc(100% - 30px);
            max-width: 300px;
            font-size: 16px;
        }
        .message {
            margin: 5px;
            padding: 10px;
            background: var(--message-bg);
            color: var(--message-text);
            border-left: 3px solid var(--message-border);
            border-radius: 5px;
        }
        .room-option {
            margin: 20px;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        #musicRoom.active {
            display: flex !important;
            flex-direction: row;
        }
        .main-content { 
            flex: 1; 
            padding: 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            width: 100%;
            max-width: 100%;
        }
        .search-container {
            margin-bottom: 20px;
            width: 100%;
            max-width: 640px;
        }
        #searchResults {
            display: none;
        }
        #searchResults.active {
            display: block;
        }
        .main-content {
            position: relative;
            min-height: 100vh;
        }

        .player-container {
            position: relative;
            width: 100%;
            max-width: 640px;
            aspect-ratio: 16/9;
        }

        .player-container.custom-fullscreen {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: calc(100vw - 300px) !important;
            height: 100vh !important;
            z-index: 9999 !important;
            background: black !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .player-container.custom-fullscreen #player {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .player-container.custom-fullscreen ~ .chat-container {
            position: fixed !important;
            top: 0 !important;
            right: 0 !important;
            width: 300px !important;
            height: 100vh !important;
            z-index: 10000 !important;
            background: var(--bg-color) !important;
            display: flex !important;
            margin: 0 !important;
            padding: 10px !important;
        }

        .player-container.custom-fullscreen ~ * {
            display: none !important;
        }

        .player-container.custom-fullscreen ~ .chat-container * {
            display: block !important;
        }

        @media (max-width: 768px) {
            .player-container.custom-fullscreen {
                width: 100%;
                height: calc(100vh - 400px);
            }

            .player-container.custom-fullscreen #player {
                position: absolute;
                width: 100% !important;
                height: 100% !important;
            }
        }

        .chat-container { 
            flex: 1; 
            padding: 10px; 
            border-left: none;
            border-top: 1px solid #ccc;
            width: 100%;
            max-width: 100%;
            margin-top: 20px;
            display: flex;
            flex-direction: column;
        }
        @media (min-width: 768px) {
            .chat-container {
                border-left: 1px solid #ccc;
                border-top: none;
                max-width: 300px;
                margin-top: 0;
            }
            #musicRoom.active {
                flex-direction: row !important;
            }
        }
        .video-item {
            display: flex;
            align-items: center;
            margin: 10px 0;
            cursor: pointer;
            padding: 5px;
        }
        .video-item:hover { background-color: #f0f0f0; }
        .video-item img { margin-right: 10px; }
        #messages { height: 400px; overflow-y: auto; margin-bottom: 10px; }

        .fullscreen-button {
            margin: 10px 0;
            padding: 10px 20px;
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            width: auto !important;
            max-width: none !important;
            transition: all 0.3s;
        }

        .fullscreen-button:hover {
            transform: scale(1.05);
            background-color: var(--primary-color) !important;
        }

        .fullscreen-exit-button {
            margin: 10px 0;
            padding: 10px 20px;
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            width: auto !important;
            max-width: none !important;
            transition: all 0.3s;
            display: none; /* Initially hidden */
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
        }

        .player-container.custom-fullscreen ~ .fullscreen-exit-button,
        .player-container.custom-fullscreen .fullscreen-exit-button {
            display: block; /* Show when fullscreen */
        }

        .fullscreen-exit-button:hover {
            transform: scale(1.05);
            background-color: var(--primary-color) !important;
        }
    </style>
</head>
<body>
    <div id="roomSetup">
        <div class="room-container">
            <h2>Tuana Özür Dilerim</h2>
            <div class="room-option">
                <h3>Yeni Oda Oluştur</h3>
                <input type="text" id="createUsername" placeholder="Kullanıcı Adı">
                <button onclick="createRoom()">Oda Oluştur</button>
            </div>
            <div class="room-option">
                <h3>Odaya Katıl</h3>
                <input type="text" id="roomId" placeholder="Oda ID">
                <input type="text" id="username" placeholder="Kullanıcı Adı">
                <button onclick="joinRoom()">Odaya Katıl</button>
            </div>
        </div>
    </div>

    <div class="watermark">Tuana Özür Dilerim</div>
    <div id="musicRoom">
        <div class="main-content">
            <h2 id="roomIdDisplay" style="display: none;">Oda: <span id="currentRoomId"></span></h2>
            <div class="search-container">
                <input type="text" id="searchQuery" placeholder="Şarkı adı">
                <button onclick="searchVideo()">Ara</button>
                <div id="searchResults"></div>
            </div>
            <div class="player-container">
                <div id="player"></div>
                <button class="fullscreen-button" onclick="toggleCustomFullscreen()">Tam Ekran</button>
                <button class="fullscreen-exit-button" onclick="toggleCustomFullscreen()">Tam Ekrandan Çık</button>
            </div>
            <div class="theme-menu" style="position: absolute; top: 10px; left: 10px;" id="themeMenu">
                <div class="theme-dots" onclick="toggleThemeSelector()" style="cursor: pointer; font-size: 24px;">⚙️</div>
                <div class="theme-selector" style="display: none; position: absolute; background: var(--bg-color); border: 1px solid var(--primary-color); padding: 10px; border-radius: 5px; z-index: 100; min-width: 200px;">
                    <div style="text-align: center; margin-bottom: 10px; font-weight: bold;">Ayarlar</div>
                    <h3 style="margin-top: 0;">Tema Seç</h3>
                    <select id="themeSelect" onchange="setTheme(this.value)" style="width: 100%; padding: 5px; margin-bottom: 10px; background: var(--bg-color); color: var(--text-color); border: 1px solid var(--primary-color);">
                        <option value="default">Varsayılan</option>
                        <option value="love">Aşk Teması</option>
                        <option value="monochrome">Monochrome</option>
                        <option value="dark">Dark</option>
                        <option value="instagram-light">Instagram Light</option>
                        <option value="instagram-dark">Instagram Dark</option>
                        <option value="sunset">Sunset</option>
                    </select>
                </div>
            </div>
            <div class="queue-container">
                <h3>Şarkı Sırası</h3>
                <div id="songQueue"></div>
                <button onclick="skipCurrentSong()" id="skipButton">Sonraki Şarkıya Geç</button>
            </div>
        </div>
        <div class="chat-container" style="display: none;">
            <h3>Sohbet</h3>
            <div id="messages"></div>
            <input type="text" id="messageInput" placeholder="Mesajınız...">
            <button onclick="sendMessage()">Gönder</button>
            <button class="fullscreen-exit-button" onclick="toggleCustomFullscreen()">Tam Ekrandan Çık</button>
        </div>
    </div>

    <script>
        var socket = io();
        var player;
        var currentRoom = '';
        var songQueue = [];

        let isRoomCreator = false;
        const themes = {
            'default': {
                '--primary-color': '#ff4d4d',
                '--bg-color': '#000000',
                '--text-color': '#fff',
                'watermark': 'Sadece Biz',
                'title': '🎵 Müzik Odası 🎵',
                '--message-bg': 'rgba(255,77,77,0.1)',
                '--message-text': '#fff',
                '--message-border': '#ff4d4d'
            },
            'love': {
                '--primary-color': '#ff69b4',
                '--bg-color': '#ffe4e1',
                '--text-color': '#ff1493',
                'watermark': 'Sadece Biz 💗',
                'title': '💕 Aşkımızın Şarkıları 💕',
                '--message-bg': 'rgba(255,105,180,0.3)',
                '--message-text': '#ff1493',
                '--message-border': '#ff69b4'
            },
            'monochrome': {
                '--primary-color': '#ffffff',
                '--bg-color': '#1a1a1a',
                '--text-color': '#e0e0e0',
                'watermark': 'MONO BEATS',
                'title': '⚫ Siyah & Beyaz ⚪',
                '--message-bg': 'rgba(255,255,255,0.1)',
                '--message-text': '#e0e0e0',
                '--message-border': '#ffffff'

            },
            'dark': {
                '--primary-color': '#2c3e50',
                '--bg-color': '#1a1a1a',
                '--text-color': '#ecf0f1',
                'watermark': 'DARK MODE',
                'title': '🌑 Karanlık Tema 🌑',
                '--message-bg': 'rgba(44,62,80,0.3)',
                '--message-text': '#ecf0f1',
                '--message-border': '#2c3e50'
            },
            'instagram-light': {
                '--primary-color': '#405de6',
                '--bg-color': '#fafafa',
                '--text-color': '#262626',
                'watermark': 'INSTA MUSIC',
                'title': '📸 Sosyal Müzik 📸',
                '--message-bg': 'rgba(64,93,230,0.1)',
                '--message-text': '#262626',
                '--message-border': '#405de6'
            },
            'instagram-dark': {
                '--primary-color': '#405de6',
                '--bg-color': '#121212',
                '--text-color': '#ffffff',
                'watermark': 'NIGHT INSTA',
                'title': '🌃 Gece Modu 🌃',
                '--message-bg': 'rgba(64,93,230,0.2)',
                '--message-text': '#ffffff',
                '--message-border': '#405de6'
            },
            'sunset': {
                '--primary-color': '#ff7e5f',
                '--bg-color': '#2c3e50',
                '--text-color': '#feb47b',
                'watermark': 'SUNSET VIBES',
                'title': '🌅 Günbatımı 🌅',
                '--message-bg': 'rgba(255,126,95,0.3)',
                '--message-text': '#feb47b',
                '--message-border': '#ff7e5f'
            }
        };

        function setTheme(themeName) {
            const theme = themes[themeName];
            for (const [property, value] of Object.entries(theme)) {
                if (property.startsWith('--')) {
                    document.documentElement.style.setProperty(property, value);
                } else if (property === 'watermark') {
                    document.querySelector('.watermark').textContent = value;
                } else if (property === 'title') {
                    document.querySelector('h2').innerHTML = value;
                }
            }
            socket.emit('theme_change', {room: currentRoom, theme: themeName});
        }

        socket.on('theme_change', function(data) {
            document.getElementById('themeSelect').value = data.theme;
            const theme = themes[data.theme];
            for (const [property, value] of Object.entries(theme)) {
                if (property.startsWith('--')) {
                    document.documentElement.style.setProperty(property, value);
                } else if (property === 'watermark') {
                    document.querySelector('.watermark').textContent = value;
                } else if (property === 'title') {
                    document.querySelector('h2').innerHTML = value;
                }
            }
        });

        function addToQueue(videoId, title) {
            songQueue.push({videoId, title});
            updateQueueDisplay();
            socket.emit('update_queue', {room: currentRoom, queue: songQueue});
        }

        function updateQueueDisplay() {
            const queueDiv = document.getElementById('songQueue');
            queueDiv.innerHTML = songQueue.map((song, index) => 
                `<div class="queue-item">${index + 1}. ${song.title}</div>`
            ).join('');
        }

        function skipCurrentSong() {
            if (songQueue.length > 0) {
                if (player && player.getPlayerState() !== null) {
                    const nextSong = songQueue.shift();
                    updateQueueDisplay();
                    player.loadVideoById(nextSong.videoId);
                    socket.emit('update_queue', {room: currentRoom, queue: songQueue});
                    socket.emit('play_video', {videoId: nextSong.videoId, room: currentRoom});
                }
            }
        }

        function toggleCustomFullscreen() {
            const playerContainer = document.querySelector('.player-container');
            const fullscreenIcon = document.getElementById('fullscreenIcon');
            const isFullscreen = playerContainer.classList.contains('custom-fullscreen');

            if (isFullscreen) {
                playerContainer.classList.remove('custom-fullscreen');
                fullscreenIcon.textContent = '⛶';
            } else {
                playerContainer.classList.add('custom-fullscreen');
                fullscreenIcon.textContent = '⮌';
            }
        }

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const playerContainer = document.querySelector('.player-container');
                const fullscreenIcon = document.getElementById('fullscreenIcon');
                if (playerContainer.classList.contains('custom-fullscreen')) {
                    playerContainer.classList.remove('custom-fullscreen');
                    fullscreenIcon.textContent = '⛶';
                }
            }
        });

        function toggleThemeSelector() {
            const selector = document.querySelector('.theme-selector');
            selector.style.display = selector.style.display === 'none' ? 'block' : 'none';
        }

        function createRoom() {
            const username = document.getElementById('createUsername').value;
            isRoomCreator = true;
            if (!username) {
                alert('Lütfen kullanıcı adı girin!');
                return;
            }
            const roomId = Math.random().toString(36).substring(2, 8).toUpperCase();
            currentRoom = roomId;
            document.getElementById('currentRoomId').textContent = roomId;
            document.getElementById('roomIdDisplay').style.display = 'block';
            socket.emit('join', {room: roomId, username: username, is_creator: true});
            showMusicRoom();
        }

        function showMusicRoom() {
            document.getElementById('roomSetup').style.display = 'none';
            document.getElementById('musicRoom').classList.add('active');
            document.querySelector('.chat-container').style.display = 'flex';
            if (!player) {
                initializePlayer();
            }
        }

        let playerReady = false;
        function initializePlayer() {
            if (typeof YT !== 'undefined' && YT.loaded) {
                player = new YT.Player('player', {
                    height: '360',
                    width: '640',
                    videoId: '',
                    playerVars: {'autoplay': 0, 'controls': 1},
                    events: {
                        'onReady': onPlayerReady,
                        'onStateChange': onPlayerStateChange
                    }
                });
            } else {
                setTimeout(initializePlayer, 100);
            }
        }

        function onYouTubeIframeAPIReady() {
            initializePlayer();
        }

        function onPlayerReady(event) {
            playerReady = true;
            player = event.target;
        }

        function joinRoom() {
            const roomId = document.getElementById('roomId').value;
            const username = document.getElementById('username').value;
            if (roomId && username) {
                currentRoom = roomId;
                document.getElementById('currentRoomId').textContent = roomId;
                socket.emit('join', {room: roomId, username: username, is_creator: false});
                showMusicRoom();
            } else {
                alert('Lütfen oda ID ve kullanıcı adı girin!');
            }
        }

        function sendMessage() {
            if (!currentRoom) return;
            const message = document.getElementById('messageInput').value;
            const username = document.getElementById('username').value || document.getElementById('createUsername').value;
            if (message && username) {
                socket.emit('chat_message', {
                    room: currentRoom,
                    username: username,
                    message: message
                });
                document.getElementById('messageInput').value = '';
            }
        }

        function addMessage(username, message) {
            const messages = document.getElementById('messages');
            messages.innerHTML += `<div class="message"><strong>${username}:</strong> ${message}</div>`;
            messages.scrollTop = messages.scrollHeight;
        }

        function searchVideo() {
            var query = document.getElementById('searchQuery').value;
            fetch('/search/' + encodeURIComponent(query))
                .then(response => response.json())
                .then(videos => {
                    var resultsHtml = '';
                    videos.forEach(video => {
                        resultsHtml += `
                            <div class="video-item" onclick="playVideo('${video.id}', '${video.title.replace(/'/g, "\\'")}')">
                                <img src="${video.thumbnail}" width="120">
                                <span>${video.title}</span>
                            </div>`;
                    });
                    const searchResults = document.getElementById('searchResults');
                    searchResults.innerHTML = resultsHtml;
                    searchResults.classList.add('active');
                });
        }

        function playVideo(videoId, title) {
            if (!currentRoom) {
                alert('Lütfen önce bir odaya katılın!');
                return;
            }

            if (player && player.getPlayerState() === 1) {
                addToQueue(videoId, title);
            } else {
                socket.emit('play_video', {videoId: videoId, room: currentRoom});
            }
            document.getElementById('searchResults').classList.remove('active');
        }


        let syncInterval;
        let lastSyncTime = 0;
        function onPlayerStateChange(event) {
            if (!currentRoom) return;

            if (event.data == YT.PlayerState.PLAYING) {
                const currentTime = player.getCurrentTime();
                if (Math.abs(currentTime - lastSyncTime) > 2) {
                    socket.emit('player_state', {
                        state: 'PLAYING', 
                        room: currentRoom,
                        time: currentTime
                    });
                    lastSyncTime = currentTime;
                }
            } else if (event.data == YT.PlayerState.PAUSED) {
                socket.emit('player_state', {
                    state: 'PAUSED', 
                    room: currentRoom,
                    time: player.getCurrentTime()
                });
                clearInterval(syncInterval);
            } else if (event.data == YT.PlayerState.ENDED) {
                skipCurrentSong(); // Şarkı bittiğinde otomatik olarak sıradakine geç
            }
        }

        socket.on('play_video', function(data) {
            if (playerReady && player) {
                player.loadVideoById(data.videoId);
            }
        });

        socket.on('sync_time', function(data) {
            if (!playerReady || !player) return;
            player.seekTo(data.time);
            lastSyncTime = data.time;
        });

        socket.on('player_state', function(data) {
            if (!playerReady || !player) return;

            if (data.state === 'PLAYING') {
                player.seekTo(data.time);
                player.playVideo();
            } else if (data.state === 'PAUSED') {
                player.seekTo(data.time);
                player.pauseVideo();
            }
        });

        socket.on('chat_message', function(data) {
            addMessage(data.username, data.message);
        });

        socket.on('request_video_state', function(data) {
            if (player && player.getPlayerState) {
                socket.emit('video_state_update', {
                    room: currentRoom,
                    videoId: player.getVideoData().video_id,
                    currentTime: player.getCurrentTime(),
                    state: player.getPlayerState()
                });
            }
        });

        socket.on('video_state_update', function(data) {
            if (player && player.loadVideoById) {
                player.loadVideoById({
                    videoId: data.videoId,
                    startSeconds: data.currentTime
                });
                if (data.state === YT.PlayerState.PAUSED) {
                    setTimeout(() => player.pauseVideo(), 1000);
                }
            }
        });

        socket.on('room_error', function(data) {
            alert(data.message);
        });

        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/search/<query>')
def search(query):
    try:
        request = youtube.search().list(part="id,snippet",
                                        q=query,
                                        type="video",
                                        maxResults=5)
        response = request.execute()

        if 'items' not in response:
            return jsonify([])

        videos = []
        for item in response['items']:
            if 'videoId' in item.get('id', {}):
                videos.append({
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'thumbnail': item['snippet']['thumbnails']['default']['url']
                })
        return jsonify(videos)
    except Exception as e:
        print("Search error:", str(e))
        return jsonify([])


active_rooms = set()

@socketio.on('join')
def on_join(data: dict) -> None:
    room: str = data['room']
    if room not in active_rooms and not data.get('is_creator', False):
        emit('room_error', {'message': 'Bu oda mevcut değil!'})
        return
    if data.get('is_creator', False):
        active_rooms.add(room)
    join_room(room)
    emit('chat_message', {
        'username': 'Sistem',
        'message': f"{data['username']} odaya katıldı"
    }, to=room)
    # Yeni kullanıcı için video durumunu iste
    emit('request_video_state', {'room': room}, to=room, include_self=False)


@socketio.on('chat_message')
def handle_message(data: dict) -> None:
    emit('chat_message', data, to=data['room'])


@socketio.on('play_video')
def handle_play(data: dict) -> None:
    emit('play_video', data, to=data['room'])


@socketio.on('video_time')
def handle_time(data: dict) -> None:
    emit('sync_time', data, to=data['room'])


@socketio.on('player_state')
def handle_state(data: dict) -> None:
    emit('player_state', data, to=data['room'])

@socketio.on('video_state_update')
def handle_video_state(data: dict) -> None:
    emit('video_state_update', data, to=data['room'])

@socketio.on('theme_change')
def handle_theme_change(data: dict) -> None:
    emit('theme_change', data, to=data['room'])


if __name__ == '__main__':
    print("\nServer started on http://0.0.0.0:11481")
    socketio.run(app, host='0.0.0.0', port=11481, allow_unsafe_werkzeug=True, use_reloader=True, log_output=True)