#!/usr/bin/env python3
"""
YouTube API using yt-dlp and ffmpeg
Developer: Mr Senal
Easy project for downloading, searching, and converting YouTube videos
"""

import os
import json
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import yt_dlp
import ffmpeg
import requests
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'fallback-secret-key')

# Create directories for downloads and temp files
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
TEMP_DIR = os.path.join(os.getcwd(), 'temp')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def clean_filename(filename):
    """Clean filename for safe storage"""
    return secure_filename(filename)[:100]  # Limit length

def get_video_id_from_url(url):
    """Extract video ID from YouTube URL"""
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0]
    elif 'youtube.com/watch' in url:
        parsed = urlparse(url)
        return parse_qs(parsed.query).get('v', [None])[0]
    return None

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'message': 'YouTube API by Mr Senal',
        'endpoints': {
            'POST /download': 'Download video by URL',
            'GET /search': 'Search YouTube videos',
            'GET /info': 'Get video information',
            'GET /thumbnail': 'Get video thumbnail',
            'POST /convert': 'Convert video format/quality'
        },
        'developer': 'Mr Senal'
    })

@app.route('/download', methods=['POST'])
def download_video():
    """Download YouTube video"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        format_type = data.get('format', 'mp4')  # mp4 or mp3
        quality = data.get('quality', 'best')   # best, worst, 720p, 480p, etc.
        
        # Configure yt-dlp options
        if format_type == 'mp3':
            # Normalize MP3 quality
            quality_map = {'low': '64', 'medium': '128', 'high': '192', 'best': '320'}
            if quality in quality_map:
                bitrate = quality_map[quality]
            elif quality.endswith('kbps'):
                bitrate = quality[:-4]  # Remove 'kbps'
            elif quality.isdigit():
                bitrate = quality
            else:
                bitrate = '192'  # Default
                
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }],
            }
        else:
            if quality == 'best':
                format_selector = 'best[ext=mp4]'
            elif quality == 'worst':
                format_selector = 'worst[ext=mp4]'
            else:
                # Quality like 720p, 480p, 144p
                format_selector = f'best[height<={quality[:-1]}][ext=mp4]'
            
            ydl_opts = {
                'format': format_selector,
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({'error': 'Could not extract video information'}), 500
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
        return jsonify({
            'success': True,
            'title': title,
            'duration': duration,
            'format': format_type,
            'quality': quality,
            'message': f'Downloaded: {title}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_videos():
    """Search YouTube videos"""
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Search query "q" is required'}), 400
        
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 50)  # Max 50 results
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(
                f'ytsearch{limit}:{query}',
                download=False
            )
            
            videos = []
            if search_results and 'entries' in search_results:
                for entry in search_results['entries']:
                    if entry:
                        videos.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'thumbnail': entry.get('thumbnail'),
                            'duration': entry.get('duration'),
                            'uploader': entry.get('uploader'),
                            'view_count': entry.get('view_count')
                        })
            
            return jsonify({
                'success': True,
                'query': query,
                'results': videos,
                'count': len(videos)
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/info', methods=['GET'])
def get_video_info():
    """Get video information and metadata"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400
        
        ydl_opts = {
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({'error': 'Could not extract video information'}), 500
            
            video_info = {
                'id': info.get('id'),
                'title': info.get('title'),
                'description': (info.get('description') or '')[:500],  # Limit description
                'duration': info.get('duration'),
                'upload_date': info.get('upload_date'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'thumbnail': info.get('thumbnail'),
                'tags': (info.get('tags') or [])[:10],  # Limit tags
                'categories': info.get('categories') or [],
                'formats': []
            }
            
            # Add available formats
            formats = info.get('formats') or []
            for fmt in formats:
                if fmt and (fmt.get('vcodec') != 'none' or fmt.get('acodec') != 'none'):
                    video_info['formats'].append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'resolution': fmt.get('resolution'),
                        'filesize': fmt.get('filesize'),
                        'vcodec': fmt.get('vcodec'),
                        'acodec': fmt.get('acodec')
                    })
            
            return jsonify({
                'success': True,
                'video_info': video_info
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/thumbnail', methods=['GET'])
def get_thumbnail():
    """Download and serve video thumbnail"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': 'URL parameter is required'}), 400
        
        ydl_opts = {
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({'error': 'Could not extract video information'}), 500
            thumbnail_url = info.get('thumbnail')
            
            if not thumbnail_url:
                return jsonify({'error': 'No thumbnail found'}), 404
            
            # Download thumbnail
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                # Save thumbnail temporarily
                video_id = info.get('id', 'unknown')
                thumbnail_path = os.path.join(TEMP_DIR, f'{video_id}_thumb.jpg')
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                def remove_file(path):
                    """Remove file after sending it"""
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except:
                        pass
                
                # Schedule cleanup after sending file
                from threading import Timer
                Timer(1.0, remove_file, args=[thumbnail_path]).start()
                
                return send_file(thumbnail_path, mimetype='image/jpeg')
            else:
                return jsonify({'error': 'Failed to download thumbnail'}), 500
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/convert', methods=['POST'])
def convert_video():
    """Convert video format/quality using ffmpeg"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        output_format = data.get('format', 'mp4')
        quality = data.get('quality', 'medium')
        
        # First download the video
        temp_file = os.path.join(TEMP_DIR, f'temp_{get_video_id_from_url(url) or "video"}')
        
        ydl_opts = {
            'outtmpl': temp_file + '.%(ext)s',
            'format': 'best'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({'error': 'Could not extract video information'}), 500
            title = info.get('title', 'converted_video')
            
        # Find the downloaded file
        downloaded_file = None
        for ext in ['mp4', 'webm', 'mkv']:
            potential_file = f'{temp_file}.{ext}'
            if os.path.exists(potential_file):
                downloaded_file = potential_file
                break
        
        if not downloaded_file:
            return jsonify({'error': 'Failed to download source video'}), 500
        
        # Set conversion parameters
        output_file = os.path.join(DOWNLOAD_DIR, f'{clean_filename(title)}.{output_format}')
        
        if output_format == 'mp3':
            # Audio conversion
            quality_map = {
                'low': '64k',
                'medium': '128k', 
                'high': '192k',
                'best': '320k'
            }
            audio_bitrate = quality_map.get(quality, '128k')
            
            ffmpeg.input(downloaded_file).output(
                output_file,
                acodec='libmp3lame',
                audio_bitrate=audio_bitrate
            ).overwrite_output().run()
            
        else:
            # Video conversion - normalize quality and handle scaling properly
            if quality.endswith('p'):
                quality = quality[:-1]  # Remove 'p' from 720p, 480p, etc.
            
            quality_map = {
                'low': {'width': '480', 'height': '270', 'crf': '28'},
                'medium': {'width': '720', 'height': '480', 'crf': '23'},
                'high': {'width': '1280', 'height': '720', 'crf': '18'},
                'best': {'crf': '15'},
                '480': {'width': '480', 'height': '270', 'crf': '28'},
                '720': {'width': '1280', 'height': '720', 'crf': '23'},
                '1080': {'width': '1920', 'height': '1080', 'crf': '18'}
            }
            
            params = quality_map.get(quality, quality_map['medium'])
            
            stream = ffmpeg.input(downloaded_file)
            if 'width' in params:
                stream = ffmpeg.filter(stream, 'scale', params['width'], params['height'])
            
            ffmpeg.output(stream, output_file, vcodec='libx264', crf=params['crf']).overwrite_output().run()
        
        # Clean up temp file
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        
        return jsonify({
            'success': True,
            'title': title,
            'output_format': output_format,
            'quality': quality,
            'output_file': os.path.basename(output_file),
            'message': f'Converted: {title} to {output_format.upper()}'
        })
        
    except Exception as e:
        # Clean up on error
        if 'downloaded_file' in locals() and downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'YouTube API is running',
        'developer': 'Mr Senal'
    })

if __name__ == '__main__':
    print("YouTube API by Mr Senal")
    print("Starting Flask server...")
    # Use debug=False for production deployment
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)