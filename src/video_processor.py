"""
Video Processor Module
Processes downloaded videos to meet YouTube Shorts specifications.
"""
import os
import logging
from typing import Optional, Tuple
from moviepy.editor import VideoFileClip, CompositeVideoClip
from moviepy.video.fx.all import crop, resize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos for YouTube Shorts format."""

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

    def process_video(self, input_path: str, output_path: str) -> Optional[str]:
        """
        Process a video to meet YouTube Shorts specifications.
        
        Args:
            input_path: Path to input video
            output_path: Path to save processed video
            
        Returns:
            Path to processed video or None if failed
        """
        try:
            logger.info(f"Processing video: {input_path}")
            
            # Load the video
            clip = VideoFileClip(input_path)
            
            # Step 1: Trim to max duration if needed
            if clip.duration > self.max_duration:
                # Take the most interesting part (middle section)
                start_time = (clip.duration - self.max_duration) / 2
                clip = clip.subclip(start_time, start_time + self.max_duration)
                logger.info(f"Trimmed video to {clip.duration} seconds")
            
            # Step 2: Ensure minimum duration
            if clip.duration < self.min_duration:
                # Loop the video to reach minimum duration
                clip = clip.loop(duration=self.min_duration)
                logger.info(f"Looped video to {clip.duration} seconds")
            
            # Step 3: Crop to 9:16 aspect ratio (vertical)
            clip = self._crop_to_vertical(clip)
            
            # Step 4: Resize to optimal resolution
            clip = self._resize_to_shorts(clip)
            
            # Step 5: Set FPS to standard value
            clip = clip.set_fps(30)
            
            # Step 6: Add audio if missing
            if clip.audio is None:
                # Create silent audio track
                from moviepy.audio.AudioClip import AudioClip
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
