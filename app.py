# Verificar que Flask funciona
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from spotipy.oauth2 import SpotifyClientCredentials

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
        scope=SCOPE,
        show_dialog=True # Forzar el diálogo de selección/consetimiento
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

def get_top_global_albums(limit=15):    
    try:
        # Crear cliente con Client Credentials
        auth_manager = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIPY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        print("✓ Cliente de Spotify creado exitosamente")
        
        # Lista de artistas populares
        popular_artists = [
            'Taylor Swift', 'Bad Bunny', 'Drake', 'The Weeknd', 
            'Ed Sheeran', 'Ariana Grande', 'Billie Eilish', 
            'Post Malone', 'Dua Lipa', 'Harry Styles'
        ]
        
        unique_albums = []
        albums_seen = set()
        
        for artist_name in popular_artists:
            if len(unique_albums) >= limit:
                break
                
            print(f"Buscando álbumes de {artist_name}...")
            # Buscar el artista
            results = sp.search(q=artist_name, type='artist', limit=1)
            
            if results['artists']['items']:
                artist_id = results['artists']['items'][0]['id']
                
                # Obtener álbumes del artista
                albums = sp.artist_albums(artist_id, album_type='album', limit=3)
                
                for album in albums['items']:
                    album_id = album.get('id')
                    
                    if album_id and album_id not in albums_seen:
                        albums_seen.add(album_id)
                        
                        album_data = {
                            'name': album.get('name', 'Unknown Album'),
                            'artist': album.get('artists', [{}])[0].get('name', 'Unknown Artist'),
                            'image': album.get('images', [{}])[0].get('url') if album.get('images') else None,
                            'url': album.get('external_urls', {}).get('spotify', '#'),
                            'release_date': album.get('release_date', 'Unknown')
                        }
                        unique_albums.append(album_data)
                        print(f"  [{len(unique_albums)}] Álbum agregado: {album_data['name']} - {album_data['artist']}")
                        
                        if len(unique_albums) >= limit:
                            break
        
        print(f"\n✓ Total de álbumes obtenidos: {len(unique_albums)}")
        print("=== FIN get_top_global_albums ===\n")
        return unique_albums
    
    except Exception as e:
        print(f"\n✗ ERROR al obtener álbumes: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("=== FIN get_top_global_albums (CON ERROR) ===\n")
        return []

# Definir ruta principal de la web
@app.route('/')
def index():
    # Obtener álbumes del top Global para mostrar
    top_albums = get_top_global_albums(limit=10)
    return render_template('index.html', top_albums=top_albums)

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

    code = request.args.get('code') # Obtener el código de autorización
    if code:
        token_info = auth_manager.get_access_token(code) # Intercambiar el código por un token
        session['token_info'] = token_info
        return redirect(url_for('profile'))
    
    return redirect(url_for('index'))

# Ruta del perfil (donde mostraré las estadísticas)
@app.route('/profile')
def profile():
    sp = get_spotify_client() # Verificar autenticación
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
    # Obtener token antes de limpiar la sesión
    token_info = session.get('token_info')

    # Limpiar la clave del token
    session.pop('token_info', None)
    session.clear() # Limpiar toda la sesión de Flask

    # Intento de limpiar cache de spotipy
    try:
        auth_manager = create_spotify_oauth()
        cache_handler = getattr(auth_manager, 'cache_handler', None)
        if cache_handler:
            if hasattr(cache_handler, 'delete'):
                cache_handler
            elif hasattr(cache_handler, 'clear_cache'):
                cache_handler.clear_cache()
            elif hasattr(cache_handler, 'cache_path'):
                try:
                    os.remove(cache_handler.cache_path)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error limpiando cache de spotipy: {e}")

    # Redirigir al index; limpiar cookies de la sesión
    response = redirect(url_for('index'))
    response.set_cookie('session', '', expires=0)
    return response

# Ruta de prueba para credenciales (SIN mostra el secret)
'''@app.route('/test')
def test_credentials():
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    return f"<h1>Test de credenciales</h1><p>Client ID cargado: {'✅ Sí' if client_id else '❌ No'}</p>"
'''

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000, ssl_context='adhoc')

