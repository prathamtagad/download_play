import os
import threading
import glob
import shutil
from flask import Flask, request, send_from_directory, jsonify, render_template_string

app = Flask(__name__, static_folder='.')
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/download', methods=['POST'])
def download_song():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Check if it's a URL or a search query
        # URLs typically start with http://, https://, or contain typical URL patterns
        if url.lower().startswith(('http://', 'https://', 'youtube.com', 'youtu.be', 'ytsearch', 'ytmusic')):
            search_query = url
        else:
            # If it's not a URL, treat it as a song name search on YouTube
            search_query = f"ytsearch1:{url}"
        
        audio_format = data.get('format', 'mp3')
        output_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
        prmpt = f"yt-dlp --extract-audio --audio-format {audio_format} -o \"{output_template}\" \"{search_query}\""

        def download():
            try:
                os.system(prmpt)
                # Move any leftover files from current directory to downloads folder
                for ext in ['mp3', 'm4a', 'opus', 'wav', 'flac']:
                    for file in glob.glob(f'*.{ext}'):
                        try:
                            shutil.move(file, os.path.join(DOWNLOAD_FOLDER, file))
                            print(f"Moved {file} to {DOWNLOAD_FOLDER}")
                        except Exception as e:
                            print(f"Error moving {file}: {e}")
            except Exception as e:
                print(f"Download error: {e}")
        
        thread = threading.Thread(target=download)
        thread.daemon = True
        thread.start()
        
        return jsonify({"status": "Download started", "format": audio_format, "search_query": search_query}), 202

    except Exception as e:
        print(f"Error in /download: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/downloads/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route('/downloads-list', methods=['GET'])
def list_downloads():
    try:
        files = os.listdir(DOWNLOAD_FOLDER)
        # Sort by modification time, newest first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_FOLDER, x)), reverse=True)
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/file-size/<path:filename>', methods=['GET'])
def get_file_size(filename):
    try:
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            return jsonify({"filename": filename, "size": size}), 200
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"status": "File deleted", "filename": filename}), 200
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)