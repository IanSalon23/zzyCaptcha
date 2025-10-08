import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import io
import random
import string
import time
import uuid
import sqlite3
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, Response, g, flash, redirect, url_for

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
WIDTH = 320
HEIGHT = 120
CHANNELS = 3
LOOP_FRAMES = 30
SCROLL_SPEED = 2
FONT_SIZE = 75
CAPTCHA_LENGTH = 5
FONT_PATH = os.path.join("resources", "Roboto-SemiBold.ttf")
CHALLENGE_EXPIRATION_SECONDS = 300  # Challenges expire after 5 minutes
DATABASE_PATH = "captcha.db"

# --- Security & Environment ---
SITE_KEY = os.getenv("SITE_KEY", "site_key_12345")
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key_abcde")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://127.0.0.1:5000")

# --- Flask Application ---
app = Flask(__name__)
app.secret_key = SECRET_KEY # Needed for flash messages

# --- Database Management ---
def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db_command():
    """Initializes the database and creates the table if it doesn't exist."""
    db = get_db()
    # Drop existing tables and recreate
    db.execute("DROP TABLE IF EXISTS challenges;")
    db.execute("""
        CREATE TABLE challenges (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        );
    """)
    db.commit()
    print("Database initialized.")

# Register a command that can be called from the flask CLI
@app.cli.command('init-db')
def init_db_cli():
    """Clear existing data and create new tables."""
    init_db_command()

def cleanup_expired_challenges():
    """Deletes expired challenges from the database."""
    db = get_db()
    current_time = int(time.time())
    db.execute("DELETE FROM challenges WHERE expires_at < ?", (current_time,))
    db.commit()

# --- Core CAPTCHA Generation Logic (Unchanged) ---
def create_text_mask(text, font_size, offset):
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()
    img = Image.new('L', (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    draw.text(offset, text, font=font, fill=255)
    text_layer = np.array(img)
    mask[text_layer > 128] = True
    return mask

def generate_looping_noise(width, height, channels):
    noise = np.random.choice([0, 255], size=(height, width), p=[0.5, 0.5]).astype(np.uint8)
    return np.stack([noise] * channels, axis=-1)

def generate_frame(frame_index, text_mask, noise_texture):
    frame = np.zeros((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)
    noise_height = noise_texture.shape[0]
    y_coords = np.arange(HEIGHT).reshape(-1, 1)
    x_coords = np.arange(WIDTH).reshape(1, -1)
    text_offset = (frame_index * SCROLL_SPEED)
    bg_offset = -(frame_index * SCROLL_SPEED)
    text_noise_y = (y_coords + text_offset) % noise_height
    bg_noise_y = (y_coords + bg_offset) % noise_height
    text_pixels = noise_texture[text_noise_y, x_coords]
    bg_pixels = noise_texture[bg_noise_y, x_coords]
    frame[text_mask] = text_pixels[text_mask]
    frame[~text_mask] = bg_pixels[~text_mask]
    return frame

def generate_captcha_gif(text):
    text_mask = create_text_mask(text, FONT_SIZE, (15, 22))
    noise_height = LOOP_FRAMES * SCROLL_SPEED
    noise_texture = generate_looping_noise(WIDTH, noise_height, CHANNELS)
    frames = [Image.fromarray(generate_frame(i, text_mask, noise_texture)) for i in range(LOOP_FRAMES)]
    gif_bytes = io.BytesIO()
    frames[0].save(gif_bytes, format='GIF', save_all=True, append_images=frames[1:], optimize=True, duration=40, loop=0)
    return gif_bytes.getvalue()

# --- API Endpoints ---
@app.route('/')
def index():
    return "zzyCaptcha Service is running. Visit /demo to see it in action."

@app.route('/demo')
def demo():
    """Serves the developer demo page."""
    return render_template("demo.html", site_key=SITE_KEY)

@app.route('/api/challenge/<string:site_key>')
def get_challenge(site_key):
    """Generates and serves the CAPTCHA challenge page."""
    if site_key != SITE_KEY:
        return "Invalid site key", 403
    
    cleanup_expired_challenges()

    challenge_id = str(uuid.uuid4())
    captcha_text = ''.join(random.choices(string.ascii_uppercase, k=CAPTCHA_LENGTH))
    expires_at = int(time.time()) + CHALLENGE_EXPIRATION_SECONDS

    db = get_db()
    db.execute(
        "INSERT INTO challenges (id, text, expires_at) VALUES (?, ?, ?)",
        (challenge_id, captcha_text, expires_at)
    )
    db.commit()
    
    return render_template("challenge.html", challenge_id=challenge_id, site_key=site_key, allowed_origin=ALLOWED_ORIGIN)

@app.route('/api/captcha.gif')
def get_captcha_gif():
    """Generates and returns the CAPTCHA GIF image."""
    challenge_id = request.args.get('id')
    if not challenge_id:
        return "Missing challenge ID", 400

    db = get_db()
    challenge = db.execute("SELECT text FROM challenges WHERE id = ?", (challenge_id,)).fetchone()

    if not challenge:
        return "Invalid or expired challenge", 404
        
    gif_data = generate_captcha_gif(challenge['text'])
    return Response(gif_data, mimetype='image/gif')

@app.route('/api/check_answer', methods=['POST'])
def check_answer():
    """Checks a user's answer. On failure, generates a new text for the same ID."""
    data = request.get_json()
    challenge_id = data.get('challenge_id')
    user_answer = data.get('user_answer', '').upper()

    if not challenge_id or not user_answer:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    db = get_db()
    challenge = db.execute("SELECT text, expires_at FROM challenges WHERE id = ?", (challenge_id,)).fetchone()

    if not challenge or challenge['expires_at'] < int(time.time()):
        return jsonify({"success": False, "error": "Invalid or expired challenge ID"})

    if user_answer == challenge['text']:
        return jsonify({"success": True})
    else:
        new_captcha_text = ''.join(random.choices(string.ascii_uppercase, k=CAPTCHA_LENGTH))
        db.execute("UPDATE challenges SET text = ? WHERE id = ?", (new_captcha_text, challenge_id))
        db.commit()
        return jsonify({"success": False, "error": "Incorrect answer"})

# --- This endpoint is not used by the new demo flow, but kept for API completeness ---
@app.route('/api/verify', methods=['POST'])
def verify_captcha():
    """Verifies the user's CAPTCHA submission (for server-to-server use)."""
    # This function is now a wrapper around the internal logic for external API calls.
    response, _ = verify_captcha_internally(request.get_json())
    return jsonify(response)

@app.route('/submit_form', methods=['POST'])
def handle_form_submission():
    """Handles the submission from the demo form, verifying the captcha server-side."""
    challenge_id = request.form.get('zzy_challenge_id')
    user_answer = request.form.get('zzy_user_answer')

    verification_result, status_code = verify_captcha_internally({
        'challenge_id': challenge_id,
        'user_answer': user_answer,
        'secret_key': SECRET_KEY
    })

    if verification_result.get("success"):
        flash("Verification Successful! Your form has been submitted.", "success")
    else:
        error_message = verification_result.get("error", "Unknown error")
        flash(f"Verification Failed: {error_message}. Please try the CAPTCHA again.", "error")
    
    return redirect(url_for('demo'))

def verify_captcha_internally(data):
    """A helper to call the verification logic internally. Returns (dict, status_code)."""
    challenge_id = data.get('challenge_id')
    user_answer = data.get('user_answer', '').upper()
    secret_key = data.get('secret_key')

    if secret_key != SECRET_KEY:
        return {"success": False, "error": "Invalid secret key"}, 403

    if not challenge_id or not user_answer:
        return {"success": False, "error": "Missing challenge data"}, 400

    db = get_db()
    challenge = db.execute("SELECT text, expires_at FROM challenges WHERE id = ?", (challenge_id,)).fetchone()

    if not challenge or challenge['expires_at'] < int(time.time()):
        return {"success": False, "error": "Invalid or expired CAPTCHA. Please try again."}, 400

    # Consume the challenge ID immediately
    db.execute("DELETE FROM challenges WHERE id = ?", (challenge_id,))
    db.commit()

    if user_answer == challenge['text']:
        return {"success": True}, 200
    else:
        return {"success": False, "error": "The characters you entered did not match."}, 400

# This block is for running with the Flask development server and the init-db command.
# To run in production, use `waitress-serve --host 0.0.0.0 --port 5000 app:app`
if __name__ == '__main__':
    # When running directly, initialize the DB and use the dev server.
    # This is for convenience in development.
    with app.app_context():
        init_db_command()
    app.run(host='0.0.0.0', port=5000, debug=True)
