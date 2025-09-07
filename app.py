# Verificar que Flask funciona
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# Cargar variables de entorno (archivo .env)
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = os.urandom(24) # Para manejar las sesiones de forma segura.

# Configuración de Spotify
SCOPE = SCOPE = "user-top-read user-read-recently-played user-read-email user-follow-read"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
        scope=SCOPE
    )

def get_spotify_client():
    # Obtiene un cliente de Spotify autenticado
    if 'token_info' not in session:
        return None
    
    # Verificar si el token necesita renovarse
    auth_manager = create_spotify_oauth()
    token_info = session['token_info']

    if auth_manager.is_token_expired(token_info):
        token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    return spotipy.Spotify(auth=token_info['access_token'])

# Definir ruta principal de la web
@app.route('/')
def index():
    return render_template('index.html')

# Definir ruta para iniciar autenticación
@app.route('/login')
def login():
    auth_manager = create_spotify_oauth()
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

# Ruta de callback (donde Spotify nos redirige después del login)
@app.route('/callback')
def callback():
    auth_manager = create_spotify_oauth()

    # Obtener el código de autorización
    code = request.args.get('code')
    if code:
        # Intercambiar el código por un token
        token_info = auth_manager.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('profile'))
    
    return redirect(url_for('index'))

# Ruta del perfil (donde mostraré las estadísticas)
@app.route('/profile')
def profile():
    # Verificar autenticación
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))
    
    try:
        # Obtener información del ususario
        user_info = sp.current_user()

        # Obtener top canciones (Últimos 6 meses)
        top_tracks = sp.current_user_top_tracks(limit=10, time_range='medium_term')

        # Obtener top artistas (Últimos 6 meses)
        top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')

        # Obtener canciones recientes
        recent_tracks = sp.current_user_recently_played(limit=10)

        # Obtener artistas que sigue el usuario
        following_artists = sp.current_user_followed_artists(limit=10)

        return render_template('profile.html',
                               user=user_info,
                               top_tracks=top_tracks['items'],
                               top_artists=top_artists['items'],
                               recent_tracks=recent_tracks['items'],
                               following_artists=following_artists['artists']['items'])

    except Exception as e:
        return f"Error al obtener datos: {str(e)}"

@app.route('/stats/<time_range>')
def stats_by_time(time_range):
    # Estadísticas por rango de tiempo específico.
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))
    
    # Validar rango de tiempo
    valid_ranges = {'short_term': '4 semanas', 'medium_term': '6 meses', 'long_term': 'varios años'}
    if time_range not in valid_ranges:
        return redirect(url_for('profile'))
    
    try:
        user_info = sp.current_user()
        top_tracks = sp.current_user_top_tracks(limit=20, time_range=time_range)
        top_artists = sp.current_user_top_artists(limit=20, time_range=time_range)

        # Análisis de géneros
        genres = {}
        for artist in top_artists['items']:
            for genre in artist['genres']:
                genres[genre] = genres.get(genre, 0) + 1

        # Ordenar géneros por popularidad
        top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]

        return render_template('detailed_stats.html',
                               user=user_info,
                             top_tracks=top_tracks['items'],
                             top_artists=top_artists['items'],
                             top_genres=top_genres,
                             time_range=time_range,
                             time_range_name=valid_ranges[time_range])
    
    except Exception as e:
        return f"Error al obtener estadísticas: {str(e)}"

@app.route('/logout')
def logout():
    # Cerrar sesión
    session.clear()
    return redirect(url_for('index'))

# Ruta de prueba para credenciales (SIN mostra el secret)
'''@app.route('/test')
def test_credentials():
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    return f"<h1>Test de credenciales</h1><p>Client ID cargado: {'✅ Sí' if client_id else '❌ No'}</p>"
'''

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000, ssl_context='adhoc')

