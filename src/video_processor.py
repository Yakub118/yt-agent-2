"""
Video Processor Module
Processes downloaded videos to meet YouTube Shorts specifications.
Includes viral optimization features: hook generation, seamless looping, auto-captions, and AI voiceovers.
"""
import os
import logging
from typing import Optional
import numpy as np

# CORRECT IMPORTS for moviepy==1.0.3
from moviepy.editor import (
    VideoFileClip, CompositeVideoClip, TextClip, 
    AudioClip, CompositeAudioClip, AudioFileClip
)
from moviepy.audio.fx.all import volumex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos for YouTube Shorts format with viral optimizations."""

    def __init__(self):
        from config.settings import (
            MAX_VIDEO_DURATION_SECONDS,
            MIN_VIDEO_DURATION_SECONDS,
            SHORTS_MAX_RESOLUTION,
            SHORTS_MIN_RESOLUTION,
        )
        
        self.max_duration = MAX_VIDEO_DURATION_SECONDS
        self.min_duration = MIN_VIDEO_DURATION_SECONDS
        self.max_resolution = SHORTS_MAX_RESOLUTION
        self.min_resolution = SHORTS_MIN_RESOLUTION
        
        # Viral hook settings
        self.hook_duration = 2.0  # Seconds to cut from start
        self.hook_texts = [
            "Wait for the end...",
            "You've been cooking this wrong",
            "This will change everything",
            "Don't skip this!",
            "The secret revealed at 0:45",
            "Try this NOW!",
            "Game changer recipe!",
        ]

    def process_video(self, input_path: str, output_path: str, 
                      add_hook: bool = True, add_captions: bool = True,
                      enable_seamless_loop: bool = True,
                      trending_audio_path: str = None,
                      voiceover_path: str = None) -> Optional[str]:
        """
        Process a video to meet YouTube Shorts specifications with viral optimizations.
        """
        try:
            logger.info(f"Processing video: {input_path}")
            
            # Load the video
            clip = VideoFileClip(input_path)
            
            # Step 1: Apply 3-second hook (cut first 2 seconds)
            if add_hook and clip.duration > self.hook_duration + self.min_duration:
                clip = clip.subclip(self.hook_duration)
                logger.info(f"Applied hook: cut first {self.hook_duration} seconds")
            
            # Step 2: Add hook text overlay
            if add_hook:
                hook_text = np.random.choice(self.hook_texts)
                clip = self._add_hook_overlay(clip, hook_text)
                logger.info(f"Added hook overlay: '{hook_text}'")
            
            # Step 3: Trim to max duration if needed
            if clip.duration > self.max_duration:
                start_time = (clip.duration - self.max_duration) / 2
                clip = clip.subclip(start_time, start_time + self.max_duration)
                logger.info(f"Trimmed video to {clip.duration} seconds")
            
            # Step 4: Ensure minimum duration
            if clip.duration < self.min_duration:
                clip = clip.loop(duration=self.min_duration)
                logger.info(f"Looped video to {clip.duration} seconds")
            
            # Step 5: Apply seamless loop cutter
            if enable_seamless_loop:
                clip = self._apply_seamless_loop(clip)
                logger.info("Applied seamless loop optimization")
            
            # Step 6: Crop to 9:16 aspect ratio (vertical)
            clip = self._crop_to_vertical(clip)
            
            # Step 7: Resize to optimal resolution
            clip = self._resize_to_shorts(clip)
            
            # Step 8: Add Alex Hormozi-style captions
            if add_captions:
                clip = self._add_hormozi_captions(clip)
                logger.info("Added Hormozi-style captions")
            
            # Step 9: Set FPS to standard value
            clip = clip.set_fps(30)
            
            # Step 10: Handle audio - mix trending audio and voiceover if provided
            if voiceover_path and os.path.exists(voiceover_path) and trending_audio_path and os.path.exists(trending_audio_path):
                # Mix Voiceover and Trending Audio together
                clip = self._mix_audio_tracks(clip, trending_audio_path, voiceover_path)
                logger.info("Mixed AI Voiceover + Trending Audio")
            elif trending_audio_path and os.path.exists(trending_audio_path):
                # Just add trending audio without voiceover
                clip = self._add_trending_audio(clip, trending_audio_path)
                logger.info(f"Added trending audio: {trending_audio_path}")
            elif clip.audio is None:
                # Create silent audio track if no audio at all
                make_frame = lambda t: [0, 0]
                clip = clip.set_audio(AudioClip(make_frame, duration=clip.duration))
            
            # Write the processed video
            clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                logger=None,  # Suppress moviepy logger
            )
            
            # Clean up
            clip.close()
            
            logger.info(f"Video processed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return None

    def _crop_to_vertical(self, clip: VideoFileClip) -> VideoFileClip:
        """Crop video to 9:16 vertical aspect ratio."""
        width, height = clip.size
        target_ratio = 9 / 16
        current_ratio = width / height
        
        if current_ratio > target_ratio:
            new_width = int(height * target_ratio)
            x_center = width / 2
            x1 = x_center - new_width / 2
            x2 = x_center + new_width / 2
            clip = clip.crop(x1=x1, y1=0, x2=x2, y2=height)
        elif current_ratio < target_ratio:
            new_height = int(width / target_ratio)
            y_center = height / 2
            y1 = y_center - new_height / 2
            y2 = y_center + new_height / 2
            clip = clip.crop(x1=0, y1=y1, x2=width, y2=y2)
        
        logger.info(f"Cropped to vertical: {clip.size}")
        return clip

    def _resize_to_shorts(self, clip: VideoFileClip) -> VideoFileClip:
        """Resize video to YouTube Shorts optimal resolution."""
        width, height = clip.size
        target_height = self.max_resolution[1]
        
        if height != target_height:
            clip = clip.resize(height=target_height)
        
        width, height = clip.size
        if width > self.max_resolution[0]:
            clip = clip.resize(width=self.max_resolution[0])
        
        logger.info(f"Resized to: {clip.size}")
        return clip

    def _add_hook_overlay(self, clip: VideoFileClip, text: str) -> VideoFileClip:
        """Add a high-contrast hook text overlay to the first few seconds."""
        try:
            # FIXED: 'text_align' is not valid in MoviePy 1.0.3, changed to 'align'
            txt_clip = TextClip(
                text,
                fontsize=70,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(clip.w * 0.9, None),
                align='center'
            )
            txt_clip = txt_clip.set_position(('center', 100)).set_duration(min(3.5, clip.duration))
            composite = CompositeVideoClip([clip, txt_clip])
            return composite
        except Exception as e:
            logger.warning(f"Could not add hook overlay: {e}")
            return clip

    def _apply_seamless_loop(self, clip: VideoFileClip) -> VideoFileClip:
        """Apply seamless loop optimization by finding similar frames at start and end."""
        try:
            duration = clip.duration
            if duration > self.min_duration + 2:
                first_frame = clip.get_frame(0)
                sample_times = np.linspace(duration - 2, duration - 0.3, 8)
                
                best_cut_time = duration - 0.5
                min_diff = float('inf')
                
                for t in sample_times:
                    try:
                        current_frame = clip.get_frame(t)
                        diff = np.mean((first_frame - current_frame) ** 2)
                        if diff < min_diff:
                            min_diff = diff
                            best_cut_time = t
                    except:
                        continue
                
                if best_cut_time > self.min_duration:
                    clip = clip.subclip(0, best_cut_time)
                    logger.info(f"Applied seamless loop cut at {best_cut_time:.2f}s")
            return clip
        except Exception as e:
            logger.warning(f"Could not apply seamless loop: {e}")
            return clip

    def _add_hormozi_captions(self, clip: VideoFileClip) -> VideoFileClip:
        """Add Alex Hormozi-style auto-captions using Whisper."""
        try:
            # SAFEGUARD: Check if video has audio before trying to transcribe
            if clip.audio is None:
                logger.warning("No audio in video, skipping captions")
                return clip

            import whisper
            audio_path = "/tmp/video_audio.mp3"
            clip.audio.write_audiofile(audio_path, logger=None)
            
            model = whisper.load_model("tiny")
            result = model.transcribe(audio_path, language="en")
            segments = result.get("segments", [])
            
            if not segments:
                return clip
            
            caption_clips = []
            for segment in segments:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"].strip()
                words = text.split()
                word_duration = (end_time - start_time) / max(len(words), 1)
                
                current_time = start_time
                for word in words:
                    word_clip = TextClip(
                        word, fontsize=56, color='yellow', font='Arial-Bold',
                        stroke_color='black', stroke_width=2,
                    )
                    word_clip = word_clip.set_position(('center', clip.h * 0.75))
                    word_clip = word_clip.set_start(current_time).set_duration(word_duration)
                    caption_clips.append(word_clip)
                    current_time += word_duration
            
            if caption_clips:
                return CompositeVideoClip([clip] + caption_clips)
            return clip
            
        except Exception as e:
            logger.warning(f"Could not add captions: {e}")
            return clip

    def _add_trending_audio(self, clip: VideoFileClip, audio_path: str) -> VideoFileClip:
        """Replace original audio with trending audio track."""
        try:
            trending_audio = AudioFileClip(audio_path)
            if trending_audio.duration > clip.duration:
                trending_audio = trending_audio.subclip(0, clip.duration)
            elif trending_audio.duration < clip.duration:
                trending_audio = trending_audio.loop(duration=clip.duration)
            
            trending_audio = volumex(trending_audio, 0.8)
            clip = clip.set_audio(trending_audio)
            return clip
        except Exception as e:
            logger.warning(f"Could not add trending audio: {e}")
            return clip

    def _generate_edge_voiceover(self, script: str, output_path: str) -> Optional[str]:
        """Generate a realistic AI voiceover using Edge-TTS."""
        try:
            import edge_tts
            import asyncio
            
            voice = "en-US-AndrewMultilingualNeural"
            communicate = edge_tts.Communicate(script, voice)
            asyncio.run(communicate.save(output_path))
            
            logger.info(f"Voiceover saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate voiceover: {e}")
            return None

    def _mix_audio_tracks(self, video_clip: VideoFileClip, trending_audio_path: str, voiceover_path: str) -> VideoFileClip:
        """Mix Trending Music (quiet) with AI Voiceover (loud)."""
        try:
            music = AudioFileClip(trending_audio_path)
            voice = AudioFileClip(voiceover_path)
            
            if music.duration > video_clip.duration:
                music = music.subclip(0, video_clip.duration)
            else:
                music = music.loop(duration=video_clip.duration)
                
            if voice.duration > video_clip.duration:
                voice = voice.subclip(0, video_clip.duration)

            # CRITICAL VOLUMES
            music = volumex(music, 0.15)  # Music at 15% volume
            voice = volumex(voice, 1.2)   # Voice at 120% volume
            
            final_audio = CompositeAudioClip([music, voice])
            video_clip = video_clip.set_audio(final_audio)
            
            logger.info("Successfully mixed Trending Audio + AI Voiceover")
            return video_clip
        except Exception as e:
            logger.error(f"Error mixing audio: {e}")
            return video_clip

    def validate_video(self, video_path: str) -> bool:
        """Validate that a video meets YouTube Shorts requirements."""
        try:
            clip = VideoFileClip(video_path)
            if clip.duration > self.max_duration or clip.duration < self.min_duration:
                return False
            width, height = clip.size
            if abs((width / height) - (9 / 16)) > 0.05:
                return False
            clip.close()
            return True
        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return False


if __name__ == "__main__":
    processor = VideoProcessor()
    print("Video Processor module loaded successfully!")
