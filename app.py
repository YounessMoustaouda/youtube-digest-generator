from flask import Flask, render_template, request, redirect, url_for, Blueprint
from youtube_transcript_api import YouTubeTranscriptApi
import sqlite3
import argparse
import openai
import tiktoken
from pytube import YouTube

enc = tiktoken.get_encoding("cl100k_base") # this is the tokenizer used by gpt-3.5-turbo
openai.api_key = ""
max_tokens_risposta = 1000
languages = ['en', 'en-US', 'it']
url_prefix = '/project_prefix'
port = 5000

bp = Blueprint('bp', __name__, template_folder='templates', static_folder='static', static_url_path=url_prefix+'/static')

app = Flask(__name__)


def get_subtitles(youtube_url):
    try:
        # Get video id from url
        video_id = youtube_url.split("v=")[1]
        
        
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(languages)
        
        try:
            lang = transcript.language
        except:
            lang = 'English'
        
        captions = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        subtitle_text = "\n".join([caption['text'] for caption in captions])
        return subtitle_text, lang
    except Exception as e:
        print("Error:", e)
        return None,None

def create_digest(subtitles,current_model,language):
    if 'Italian' in language:
        prompt = f"Riassumi i seguenti sottotitoli:\n{subtitles}"
    else:
        prompt = f"Summarize the following subtitles:\n{subtitles}"
    response = openai.ChatCompletion.create(
        model=current_model,
        messages=[{"role": "system", "content": "You are a helpful assistant that summarizes subtitles."},
                  {"role": "user", "content": prompt}],
        max_tokens=max_tokens_risposta
    )
    digest = response.choices[0].message["content"].strip()
    return digest
    
    
    
    

def create_tables():
    conn = sqlite3.connect('digests.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            video_url TEXT,
            video_title TEXT,
            original_captions TEXT,
            digest TEXT
        )
    ''')

    conn.commit()
    conn.close()

create_tables()

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/generate', methods=['POST'])
def generate_digest():
    video_url = request.form['video_url']

    video = YouTube(video_url) # maybe there is a more elegant way to do this i.e. a simple request to the api
    video_title = video.title    
    
    subtitles, language = get_subtitles(video_url)
    # print(subtitles)
    
    if not subtitles:
        return 'No subtitles available for the provided YouTube video'
    
    
    token_number = len(enc.encode(subtitles))
    
    if token_number + max_tokens_risposta > 4000:
        current_model = "gpt-3.5-turbo-16k"
    else:
        current_model = "gpt-3.5-turbo"
    # print(f"You are about to send a {current_model} API request with {len(enc.encode(subtitles))} tokens, press enter to proceed")
    
    digest = create_digest(subtitles,current_model,language)
    # print("Generated Digest:\n", digest)
    
    conn = sqlite3.connect('digests.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO digests (video_url, video_title, original_captions, digest)
        VALUES (?, ?, ?, ?)
    ''', (video_url, video_title, subtitles, digest))

    conn.commit()
    conn.close()

    return redirect(url_for('bp.view_digests'))

@bp.route('/view_digests')
def view_digests():
    conn = sqlite3.connect('digests.db')
    cursor = conn.cursor()
    
    
    """
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            video_url TEXT,
            video_title TEXT,
            original_captions TEXT,
            digest TEXT
    """
    
    
    cursor.execute('''
        SELECT
            id,
            datetime( strftime('%Y-%m-%d %H:%M:%S', timestamp) ,'+2 hour' ) AS local_timestamp,
            video_url,
            video_title,
            original_captions,
            digest
        FROM digests
        ORDER BY timestamp DESC
    ''')
    digests = cursor.fetchall()

    conn.close()

    return render_template('view_digests.html', digests=digests)


if __name__ == '__main__':
    app.register_blueprint(bp, url_prefix=url_prefix)
    app.run(debug=True,port=port)