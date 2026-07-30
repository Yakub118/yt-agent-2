"""
Main Agent Module
Orchestrates the entire Pinterest to YouTube Shorts automation workflow.
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PinterestToYouTubeAgent:
    """
    Main agent that orchestrates the complete workflow:
    1. Download food videos from Pinterest
    2. Process videos for YouTube Shorts format
    3. Generate SEO-optimized metadata
    4. Upload to YouTube at optimal times
    """

    def __init__(self):
        """Initialize all components of the agent."""
        logger.info("Initializing Pinterest to YouTube Agent...")
        
        # Import and initialize components
        from src.pinterest_downloader import PinterestDownloader
        from src.video_processor import VideoProcessor
        from src.metadata_generator import MetadataGenerator
        from src.youtube_uploader import create_youtube_uploader_from_env
        from src.scheduler import UploadScheduler
        
        # Initialize downloader
        pinterest_token = os.getenv("PINTEREST_ACCESS_TOKEN", "")
        self.downloader = PinterestDownloader(pinterest_token) if pinterest_token else None
        
        # Initialize processor
        self.processor = VideoProcessor()
        
        # Initialize metadata generator
        self.metadata_gen = MetadataGenerator()
        
        # Initialize uploader (requires credentials)
        try:
            self.uploader = create_youtube_uploader_from_env()
        except Exception as e:
            logger.warning(f"YouTube uploader not initialized: {e}")
            self.uploader = None
        
        # Initialize scheduler
        timezone = os.getenv("TIMEZONE", "America/New_York")
        self.scheduler = UploadScheduler(timezone)
        
        logger.info("Agent initialization complete!")

    def run_daily_workflow(self, force_upload: bool = False) -> Dict:
        """
        Run the complete daily workflow.
        
        Args:
            force_upload: If True, upload immediately regardless of schedule
            
        Returns:
            Workflow execution results
        """
        logger.info("=" * 60)
        logger.info("Starting Daily Pinterest to YouTube Workflow")
        logger.info("=" * 60)
        
        results = {
            "success": False,
            "videos_downloaded": 0,
            "videos_processed": 0,
            "videos_uploaded": 0,
            "errors": [],
            "uploaded_videos": [],
        }
        
        try:
            # Step 1: Check if we should upload now
            if not force_upload:
                should_upload = self.scheduler.should_upload_now()
                if not should_upload:
                    next_upload = self.scheduler.get_next_upload_time()
                    logger.info(f"Not within upload window. Next upload: {next_upload}")
                    results["success"] = True
                    results["message"] = f"Waiting for scheduled time: {next_upload}"
                    return results
            
            # Step 2: Download videos from Pinterest
            if self.downloader:
                logger.info("\n📥 Step 1: Downloading videos from Pinterest...")
                downloaded_videos = self.downloader.get_food_videos(count=3)
                results["videos_downloaded"] = len(downloaded_videos)
                logger.info(f"Downloaded {len(downloaded_videos)} videos")
            else:
                logger.warning("Pinterest downloader not configured")
                downloaded_videos = []
            
            if not downloaded_videos:
                results["errors"].append("No videos downloaded")
                return results
            
            # Step 3: Process videos for YouTube Shorts
            logger.info("\n✂️ Step 2: Processing videos for YouTube Shorts...")
            processed_videos = []
            
            from config.settings import PROCESSED_VIDEOS_DIR
            
            for video_path in downloaded_videos:
                filename = os.path.basename(video_path)
                output_path = os.path.join(PROCESSED_VIDEOS_DIR, f"processed_{filename}")
                
                processed_path = self.processor.process_video(video_path, output_path)
                if processed_path:
                    # Validate the processed video
                    is_valid = self.processor.validate_video(processed_path)
                    if is_valid:
                        processed_videos.append({
                            "path": processed_path,
                            "keyword": filename.split("_")[0],
                        })
                        logger.info(f"✓ Processed: {filename}")
                    else:
                        logger.warning(f"Invalid video after processing: {filename}")
                else:
                    logger.error(f"Failed to process: {filename}")
            
            results["videos_processed"] = len(processed_videos)
            
            if not processed_videos:
                results["errors"].append("No videos successfully processed")
                return results
            
            # Step 4: Generate metadata and upload to YouTube
            if self.uploader:
                logger.info("\n📤 Step 3: Uploading videos to YouTube...")
                
                for video_info in processed_videos:
                    video_path = video_info["path"]
                    keyword = video_info.get("keyword", "food recipe")
                    
                    # Generate metadata
                    metadata = self.metadata_gen.generate_full_metadata(keyword)
                    
                    # Upload video
                    upload_result = self.uploader.upload_video(
                        video_path=video_path,
                        title=metadata["title"],
                        description=metadata["description"],
                        tags=metadata["tags"],
                        category_id="26",  # Howto & Style (includes cooking)
                        privacy_status="public",
                    )
                    
                    if upload_result and upload_result.get("success"):
                        results["videos_uploaded"] += 1
                        results["uploaded_videos"].append(upload_result)
                        logger.info(f"✓ Uploaded: {metadata['title']}")
                        logger.info(f"  URL: {upload_result.get('url')}")
                    else:
                        error_msg = upload_result.get("error", "Unknown error") if upload_result else "Upload failed"
                        results["errors"].append(f"Failed to upload {video_path}: {error_msg}")
                        logger.error(f"✗ Upload failed: {error_msg}")
            else:
                logger.warning("YouTube uploader not configured - skipping upload step")
                results["message"] = "Videos processed but not uploaded (no YouTube credentials)"
            
            # Step 5: Summary
            logger.info("\n" + "=" * 60)
            logger.info("Workflow Complete!")
            logger.info("=" * 60)
            logger.info(f"Videos Downloaded: {results['videos_downloaded']}")
            logger.info(f"Videos Processed: {results['videos_processed']}")
            logger.info(f"Videos Uploaded: {results['videos_uploaded']}")
            
            if results["errors"]:
                logger.warning(f"Errors: {len(results['errors'])}")
                for error in results["errors"]:
                    logger.warning(f"  - {error}")
            
            results["success"] = results["videos_uploaded"] > 0 or not self.uploader
            return results
            
        except Exception as e:
            logger.error(f"Workflow failed with error: {e}")
            results["errors"].append(str(e))
            return results

    def check_channel_status(self) -> Dict:
        """
        Check YouTube channel status and monetization progress.
        
        Returns:
            Channel status information
        """
        if not self.uploader:
            return {"error": "YouTube uploader not configured"}
        
        return self.uploader.check_channel_status()

    def print_schedule(self):
        """Print the upload schedule."""
        print("\n" + self.scheduler.format_upload_schedule())


def main():
    """Main entry point for the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pinterest to YouTube Shorts Agent")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force upload immediately, ignoring schedule",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Print upload schedule and exit",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check YouTube channel status",
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = PinterestToYouTubeAgent()
    
    if args.schedule:
        agent.print_schedule()
        return
    
    if args.status:
        status = agent.check_channel_status()
        print("\nChannel Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return
    
    # Run workflow
    results = agent.run_daily_workflow(force_upload=args.force)
    
    # Exit with appropriate code
    if results.get("success"):
        print("\n✅ Workflow completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Workflow completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
