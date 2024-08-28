from flask import Flask, request, send_file, abort
from flask_cors import CORS
from pytubefix import YouTube
import os
from moviepy.editor import VideoFileClip, AudioFileClip


app = Flask(__name__)
CORS(app)

# Added higher resolutions up to 4K (2160p)
QUALITY_MAP = {
    "144p": "144p",
    "240p": "240p",
    "360p": "360p",
    "480p": "480p",
    "720p": "720p",
    "1080p": "1080p",
    "1440p": "1440p",  # 2K
    "2160p": "2160p"   # 4K
}

@app.route('/download-youtube-video', methods=['GET'])
def download_youtube_video():
    url = request.args.get('url')
    quality = request.args.get('quality', '720p')  # Default to 720p if quality not provided

    if not url:
        return abort(400, 'Missing URL parameter')

    if quality not in QUALITY_MAP:
        return abort(400, 'Invalid quality parameter')

    try:
        yt = YouTube(url)

        # Get video stream for the requested quality or fallback to highest resolution available
        video_stream = yt.streams.filter(res=QUALITY_MAP[quality], only_video=True).first()
        audio_stream = yt.streams.filter(only_audio=True).first()

        # If no video stream is found for the requested quality, fallback to the highest available
        if not video_stream:
            video_stream = yt.streams.filter(only_video=True).order_by('resolution').desc().first()

        if not video_stream or not audio_stream:
            return abort(404, "No suitable video/audio stream found")

        # Log for debugging
        print(f"Selected video stream: {video_stream.resolution} - {video_stream.mime_type}")
        print(f"Selected audio stream: {audio_stream.abr} - {audio_stream.mime_type}")

        # Download video and audio
        video_file_path = video_stream.download(output_path="/tmp", filename="temp_video.mp4")
        audio_file_path = audio_stream.download(output_path="/tmp", filename="temp_audio.mp4")

        # Combine video and audio (for higher quality resolutions)
        combined_file_path = "/tmp/combined_video.mp4"
        video_clip = VideoFileClip(video_file_path)
        audio_clip = AudioFileClip(audio_file_path)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(combined_file_path, codec="libx264", audio_codec="aac")

        return send_file(combined_file_path, as_attachment=True, download_name=f"{yt.title}_{quality}.mp4")

    except Exception as e:
        return abort(500, f"Failed to download video: {str(e)}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
