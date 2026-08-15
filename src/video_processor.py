"""
Video Processor Module
Processes downloaded videos to meet YouTube Shorts specifications.
Includes viral optimization features: hook generation, seamless looping, and auto-captions.
"""
import os
import logging
from typing import Optional, Tuple, List
import numpy as np
from moviepy import VideoFileClip, CompositeVideoClip, TextClip, ImageClip, AudioClip, CompositeAudioClip, AudioFileClip
from moviepy.video import fx as video_fx
from moviepy.audio import fx as audio_fx

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
        
        Args:
            input_path: Path to input video
            output_path: Path to save processed video
            add_hook: Whether to add 3-second hook (cut first 2s + overlay text)
            add_captions: Whether to add Alex Hormozi-style captions
            enable_seamless_loop: Whether to enable seamless loop cutting
            trending_audio_path: Path to trending audio file to overlay
            voiceover_path: Path to AI voiceover file to mix with trending audio
            
        Returns:
            Path to processed video or None if failed
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
                # Take the most interesting part (middle section)
                start_time = (clip.duration - self.max_duration) / 2
                clip = clip.subclip(start_time, start_time + self.max_duration)
                logger.info(f"Trimmed video to {clip.duration} seconds")
            
            # Step 4: Ensure minimum duration
            if clip.duration < self.min_duration:
                # Loop the video to reach minimum duration
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
            if voiceover_path and os.path.exists(voiceover_path):
                # Generate voiceover and mix with trending audio
                clip = self._mix_audio_tracks(clip, trending_audio_path, voiceover_path)
                logger.info(f"Mixed voiceover ({voiceover_path}) with trending audio")
            elif trending_audio_path and os.path.exists(trending_audio_path):
                # Just add trending audio without voiceover
                clip = self._add_trending_audio(clip, trending_audio_path)
                logger.info(f"Added trending audio: {trending_audio_path}")
            elif clip.audio is None:
                # Create silent audio track
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
        """
        Crop video to 9:16 vertical aspect ratio.
        
        Args:
            clip: Input video clip
            
        Returns:
            Cropped video clip
        """
        width, height = clip.size
        
        # Target aspect ratio: 9:16 (width:height)
        target_ratio = 9 / 16
        current_ratio = width / height
        
        if current_ratio > target_ratio:
            # Video is wider than target, crop width
            new_width = int(height * target_ratio)
            x_center = width / 2
            x1 = x_center - new_width / 2
            x2 = x_center + new_width / 2
            clip = clip.crop(x1=x1, y1=0, x2=x2, y2=height)
        elif current_ratio < target_ratio:
            # Video is taller than target, crop height
            new_height = int(width / target_ratio)
            y_center = height / 2
            y1 = y_center - new_height / 2
            y2 = y_center + new_height / 2
            clip = clip.crop(x1=0, y1=y1, x2=width, y2=y2)
        
        logger.info(f"Cropped to vertical: {clip.size}")
        return clip

    def _resize_to_shorts(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Resize video to YouTube Shorts optimal resolution.
        
        Args:
            clip: Input video clip
            
        Returns:
            Resized video clip
        """
        width, height = clip.size
        
        # Target height is 1920 for best quality
        target_height = self.max_resolution[1]
        
        if height < target_height:
            # Upscale to target height
            clip = clip.resize(height=target_height)
        elif height > target_height:
            # Downscale to target height
            clip = clip.resize(height=target_height)
        
        # Ensure width doesn't exceed max
        width, height = clip.size
        if width > self.max_resolution[0]:
            clip = clip.resize(width=self.max_resolution[0])
        
        logger.info(f"Resized to: {clip.size}")
        return clip

    def _add_hook_overlay(self, clip: VideoFileClip, text: str) -> VideoFileClip:
        """
        Add a high-contrast hook text overlay to the first few seconds of the video.
        
        Args:
            clip: Input video clip
            text: Hook text to display
            
        Returns:
            Video clip with hook overlay
        """
        try:
            # Create text clip with high contrast styling (Alex Hormozi style)
            txt_clip = TextClip(
                text,
                fontsize=70,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(clip.w * 0.9, None),
                text_align='center'
            )
            
            # Position at top center of screen
            txt_clip = txt_clip.set_position(('center', 100)).set_duration(min(3.5, clip.duration))
            
            # Composite the text over the video
            composite = CompositeVideoClip([clip, txt_clip])
            
            logger.info(f"Added hook overlay: '{text}'")
            return composite
            
        except Exception as e:
            logger.warning(f"Could not add hook overlay: {e}, returning original clip")
            return clip

    def _apply_seamless_loop(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Apply seamless loop optimization by finding similar frames at start and end.
        Cuts the video to create a smooth transition when looping.
        
        Args:
            clip: Input video clip
            
        Returns:
            Video clip optimized for seamless looping
        """
        try:
            duration = clip.duration
            
            # For videos longer than min_duration, cut a small portion from the end
            # to find a frame that matches better with the beginning
            if duration > self.min_duration + 2:
                # Analyze frames near the end to find one similar to the first frame
                cut_duration = 0.5  # Amount to potentially cut
                
                # Get first frame for comparison
                first_frame = clip.get_frame(0)
                
                # Sample frames from the last 2 seconds
                sample_times = np.linspace(duration - 2, duration - 0.3, 8)
                
                best_cut_time = duration - cut_duration
                min_diff = float('inf')
                
                for t in sample_times:
                    try:
                        current_frame = clip.get_frame(t)
                        # Calculate frame difference (simplified MSE)
                        diff = np.mean((first_frame - current_frame) ** 2)
                        
                        if diff < min_diff:
                            min_diff = diff
                            best_cut_time = t
                    except:
                        continue
                
                # Cut at the best matching point
                if best_cut_time > self.min_duration:
                    clip = clip.subclip(0, best_cut_time)
                    logger.info(f"Applied seamless loop cut at {best_cut_time:.2f}s")
            
            return clip
            
        except Exception as e:
            logger.warning(f"Could not apply seamless loop: {e}, returning original clip")
            return clip

    def _add_hormozi_captions(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Add Alex Hormozi-style auto-captions to the video.
        Uses Whisper for transcription and renders dynamic word-by-word captions.
        
        Args:
            clip: Input video clip
            
        Returns:
            Video clip with captions overlay
        """
        try:
            # Try to import whisper for speech-to-text
            import whisper
            
            # Extract audio and transcribe
            audio_path = "/tmp/video_audio.mp3"
            clip.audio.write_audiofile(audio_path, logger=None)
            
            # Load whisper model (tiny for speed)
            model = whisper.load_model("tiny")
            result = model.transcribe(audio_path, language="en")
            
            segments = result.get("segments", [])
            
            if not segments:
                logger.warning("No speech detected in video")
                return clip
            
            caption_clips = []
            
            for segment in segments:
                start_time = segment["start"]
                end_time = segment["end"]
                text = segment["text"].strip()
                
                # Split into words for word-by-word animation
                words = text.split()
                word_duration = (end_time - start_time) / max(len(words), 1)
                
                current_time = start_time
                for i, word in enumerate(words):
                    # Create individual word clip
                    word_clip = TextClip(
                        word,
                        fontsize=56,
                        color='yellow',
                        font='Arial-Bold',
                        stroke_color='black',
                        stroke_width=2,
                    )
                    
                    # Position in center-bottom area
                    word_clip = word_clip.set_position(('center', clip.h * 0.75))
                    word_clip = word_clip.set_start(current_time).set_duration(word_duration)
                    
                    caption_clips.append(word_clip)
                    current_time += word_duration
            
            # Composite all caption clips over the video
            if caption_clips:
                composite = CompositeVideoClip([clip] + caption_clips)
                logger.info(f"Added {len(caption_clips)} caption segments")
                return composite
            
            return clip
            
        except ImportError:
            logger.warning("Whisper not installed, skipping auto-captions")
            return clip
        except Exception as e:
            logger.warning(f"Could not add captions: {e}, returning original clip")
            return clip

    def _add_trending_audio(self, clip: VideoFileClip, audio_path: str) -> VideoFileClip:
        """
        Replace original audio with trending audio track.
        
        Args:
            clip: Input video clip
            audio_path: Path to trending audio file
            
        Returns:
            Video clip with trending audio
        """
        try:
            from moviepy.editor import AudioFileClip
            from moviepy.audio.fx import volumex
            
            # Load the trending audio
            trending_audio = AudioFileClip(audio_path)
            
            # Trim or loop audio to match video duration
            if trending_audio.duration > clip.duration:
                trending_audio = trending_audio.subclip(0, clip.duration)
            elif trending_audio.duration < clip.duration:
                # Loop the audio to fill the video
                trending_audio = trending_audio.loop(duration=clip.duration)
            
            # Adjust volume to avoid overpowering
            trending_audio = volumex(trending_audio, 0.8)
            
            # Set the new audio
            clip = clip.set_audio(trending_audio)
            
            logger.info(f"Added trending audio ({trending_audio.duration:.2f}s)")
            return clip
            
        except Exception as e:
            logger.warning(f"Could not add trending audio: {e}, keeping original audio")
            return clip

    def _generate_edge_voiceover(self, script: str, output_path: str) -> Optional[str]:
        """
        Generate a realistic AI voiceover using Edge-TTS (Microsoft Azure voices).
        
        Args:
            script: Text script for the voiceover
            output_path: Path to save the generated audio
            
        Returns:
            Path to generated voiceover file or None if failed
        """
        try:
            import edge_tts
            import asyncio
            
            # 'en-US-AndrewMultilingualNeural' is deep and engaging (great for food/hacks)
            # Other great options: 'en-US-JennyNeural' (upbeat), 'en-GB-SoniaNeural'
            voice = "en-US-AndrewMultilingualNeural" 
            
            logger.info(f"Generating Edge-TTS voiceover with voice: {voice}")
            
            # Edge-TTS is async, so we run it in an event loop
            communicate = edge_tts.Communicate(script, voice)
            asyncio.run(communicate.save(output_path))
            
            logger.info(f"Voiceover saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate voiceover: {e}")
            return None

    def _mix_audio_tracks(self, video_clip: VideoFileClip, trending_audio_path: str, voiceover_path: str) -> VideoFileClip:
        """
        Mix Trending Music (quiet) with AI Voiceover (loud).
        
        Args:
            video_clip: Input video clip
            trending_audio_path: Path to trending music file
            voiceover_path: Path to AI voiceover file
            
        Returns:
            Video clip with mixed audio tracks
        """
        try:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            from moviepy.audio.fx import volumex
            
            # Load tracks
            music = AudioFileClip(trending_audio_path)
            voice = AudioFileClip(voiceover_path)
            
            # Trim/loop music to match video length
            if music.duration > video_clip.duration:
                music = music.subclip(0, video_clip.duration)
            else:
                music = music.loop(duration=video_clip.duration)
                
            # Trim voice if it's longer than video
            if voice.duration > video_clip.duration:
                voice = voice.subclip(0, video_clip.duration)

            # CRITICAL VOLUMES:
            music = volumex(music, 0.15)  # Music at 15% volume (background vibe)
            voice = volumex(voice, 1.2)   # Voice at 120% volume (clear and loud)
            
            # Composite them together
            final_audio = CompositeAudioClip([music, voice])
            
            # Attach to video
            video_clip = video_clip.set_audio(final_audio)
            
            logger.info("Successfully mixed Trending Audio + AI Voiceover")
            return video_clip
            
        except Exception as e:
            logger.error(f"Error mixing audio: {e}")
            return video_clip

    def validate_video(self, video_path: str) -> bool:
        """
        Validate that a video meets YouTube Shorts requirements.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            clip = VideoFileClip(video_path)
            
            # Check duration
            if clip.duration > self.max_duration:
                logger.warning(f"Video too long: {clip.duration}s > {self.max_duration}s")
                return False
            
            if clip.duration < self.min_duration:
                logger.warning(f"Video too short: {clip.duration}s < {self.min_duration}s")
                return False
            
            # Check aspect ratio
            width, height = clip.size
            aspect_ratio = width / height
            target_ratio = 9 / 16
            
            # Allow 5% tolerance
            if abs(aspect_ratio - target_ratio) > 0.05:
                logger.warning(f"Invalid aspect ratio: {aspect_ratio}")
                return False
            
            clip.close()
            return True
            
        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return False


if __name__ == "__main__":
    # Test the processor
    processor = VideoProcessor()
    
    # Example usage
    test_input = "/tmp/test_video.mp4"
    test_output = "/tmp/test_processed.mp4"
    
    if os.path.exists(test_input):
        result = processor.process_video(test_input, test_output)
        if result:
            print(f"Processed video saved to: {result}")
            is_valid = processor.validate_video(result)
            print(f"Video valid for YouTube Shorts: {is_valid}")
    else:
        print(f"Test video not found: {test_input}")
