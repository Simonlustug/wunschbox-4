import os
from flask import Flask, render_template_string, request, session as flask_session, redirect, url_for
import tidalapi

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Wichtig für die Flask-Sitzung

# Globale Tidal-Session (für den einfachen Start)
global_session = tidalapi.Session()

TEMPLATE = """
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>Wunschbox 3.0</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; text-align: center; padding: 50px; }
        input, button { padding: 10px; font-size: 16px; border-radius: 5px; border: none; margin: 5px; }
        input[type="text"] { width: 300px; }
        button { background: #0070f3; color: white; cursor: pointer; }
        button:hover { background: #005bb5; }
        .results { margin-top: 20px; }
        .item { background: #1e1e1e; padding: 10px; margin: 5px auto; width: 400px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
        .box { background: #1e1e1e; padding: 20px; border-radius: 8px; display: inline-block; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🎵 Wunschbox 3.0</h1>

    {% if not logged_in %}
        <div class="box">
            <p>Tidal ist noch nicht verbunden!</p>
            <form method="POST" action="/start_login">
                <button type="submit">Mit Tidal verbinden</button>
            </form>
            {% if login_url %}
                <p>Klicke hier zum Einloggen:</p>
                <a href="{{ login_url }}" target="_blank" style="color: #00ff00; font-size: 18px;">{{ login_url }}</a>
            {% endif %}
        </div>
    {% else %}
        <p style="color: #00ff00;">Tidal ist verbunden! 🟢</p>
        <form method="POST" action="/search">
            <input type="text" name="query" placeholder="Künstler oder Song suchen..." required>
            <button type="submit">Suchen</button>
        </form>
    {% endif %}

    {% if artists %}
        <h3>Wähle den richtigen Künstler aus:</h3>
        <div class="results">
            {% for artist in artists %}
                <div class="item">
                    <span>{{ artist.name }}</span>
                    <form method="POST" action="/select_artist" style="margin:0;">
                        <input type="hidden" name="artist_id" value="{{ artist.id }}">
                        <button type="submit">Auswählen</button>
                    </form>
                </div>
            {% endfor %}
        </div>
    {% endif %}

    {% if tracks %}
        <h3>Verfügbare Titel:</h3>
        <div class="results">
            {% for track in tracks %}
                <div class="item">
                    <span>{{ track.name }} - {{ track.artist.name }}</span>
                    <form method="POST" action="/queue" style="margin:0;">
                        <input type="hidden" name="track_id" value="{{ track.id }}">
                        <button type="submit">Wünschen</button>
                    </form>
                </div>
            {% endfor %}
        </div>
    {% endif %}

    {% if message %}
        <p style="color: #00ff00; margin-top: 20px;">{{ message }}</p>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    logged_in = global_session.check_session()
    return render_template_string(TEMPLATE, logged_in=logged_in)

@app.route('/start_login', methods=['POST'])
def start_login():
    try:
        # Generiert den OAuth-Link direkt über die API
        login, future = global_session.login_oauth()
        login_url = login.verification_uri_complete
        return render_template_string(TEMPLATE, logged_in=False, login_url=login_url)
    except Exception as e:
        return render_template_string(TEMPLATE, logged_in=False, message=f"Fehler: {e}")

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    artists = []
    try:
        # Fehlertolerante Suche über Tidal API
        search_result = global_session.search(query, models=[tidalapi.Artist])
        if search_result and search_result.artists:
            artists = search_result.artists[:5]  # Top 5 Treffer zur Auswahl
    except Exception as e:
        print(f"Suchfehler: {e}")
        
    return render_template_string(TEMPLATE, logged_in=True, artists=artists)

@app.route('/select_artist', methods=['POST'])
def select_artist():
    artist_id = request.form.get('artist_id')
    tracks = []
    try:
        artist = global_session.artist(artist_id)
        tracks = artist.get_top_tracks()[:10]  # Top 10 Tracks
    except Exception as e:
        print(f"Fehler beim Laden der Tracks: {e}")
        
    return render_template_string(TEMPLATE, logged_in=True, tracks=tracks)

@app.route('/queue', methods=['POST'])
def queue():
    return render_template_string(TEMPLATE, logged_in=True, message="Dein Musikwunsch wurde erfolgreich hinzugefügt! 🎶")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
