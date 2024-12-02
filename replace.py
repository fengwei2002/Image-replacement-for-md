import os
import re
import hashlib
import requests
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Tuple
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_downloader.log', encoding='utf-8', mode='a')  # Changed to append mode
    ]
)

logger = logging.getLogger(__name__)  # Get a logger instance for this module

class ImageDownloader:
    def __init__(self, base_dir: str, max_retries: int = 3):
        self.base_dir = Path(base_dir)
        self.max_retries = max_retries
        self.session = requests.Session()
        self.processed_files = 0
        self.processed_images = 0
        self.failed_downloads = 0
        logger.info(f"Initializing ImageDownloader for directory: {base_dir}")
        
    def create_working_copy(self) -> Optional[Path]:
        """Create a working copy of the directory for processing."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            working_dir = self.base_dir.parent / f"{self.base_dir.name}_processed_{timestamp}"
            
            print(Fore.CYAN + f"📁 Creating working copy at: {working_dir}")
            logger.info(f"Creating working copy at: {working_dir}")
            
            shutil.copytree(self.base_dir, working_dir)
            logger.info(f"Working copy created successfully at: {working_dir}")
            print(Fore.GREEN + f"✅ Working copy created successfully")
            
            self.original_dir = self.base_dir
            self.base_dir = working_dir
            return working_dir
            
        except Exception as e:
            error_msg = f"Failed to create working copy: {str(e)}"
            logger.error(error_msg)
            print(Fore.RED + f"❌ {error_msg}")
            raise

    def get_image_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """Determine image extension from URL or content-type."""
        if content_type:
            ext_map = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/gif': 'gif',
                'image/webp': 'webp',
                'image/svg+xml': 'svg',
                'image/x-icon': 'ico'
            }
            ext = ext_map.get(content_type.lower(), '')
            if ext:
                return ext

        # Try to get extension from URL
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1]
        if ext:
            return ext[1:].lower()  # Remove the dot and convert to lowercase
            
        # Default to jpg if no extension can be determined
        return 'jpg'

    def download_image(self, url: str, output_path: Path) -> Tuple[bool, Optional[str]]:
        """Download image with retry mechanism and validation."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Download attempt {attempt}/{self.max_retries}: {url}")
                print(Fore.CYAN + f"⬇️  Downloading ({attempt}/{self.max_retries}): {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    error_msg = f"Invalid content type: {content_type}"
                    logger.warning(error_msg)
                    raise ValueError(error_msg)

                ext = self.get_image_extension(url, content_type)
                final_path = output_path.with_suffix(f".{ext}")

                final_path.write_bytes(response.content)
                success_msg = f"Successfully downloaded: {final_path.name}"
                logger.info(success_msg)
                print(Fore.GREEN + f"✅ {success_msg}")
                return True, str(final_path)

            except Exception as e:
                error_msg = f"Download attempt {attempt} failed: {str(e)}"
                logger.warning(error_msg)
                print(Fore.YELLOW + f"⚠️  {error_msg}")
                
                if attempt == self.max_retries:
                    self.failed_downloads += 1
                    final_error = f"Download failed after {self.max_retries} attempts: {url}"
                    logger.error(final_error)
                    print(Fore.RED + f"❌ {final_error}")
                    return False, None

    def process_markdown_file(self, file_path: Path) -> None:
        """Process a single markdown file."""
        try:
            logger.info(f"Processing file: {file_path}")
            print(Fore.CYAN + f"\n📄 Processing file: {file_path.name}")
            
            content = file_path.read_text(encoding='utf-8')
            image_links = re.findall(r'!\[(.*?)\]\((http[^)]+)\)', content)
            
            if not image_links:
                logger.info(f"No images found in file: {file_path}")
                print(Fore.YELLOW + "ℹ️  No images found in file")
                return

            image_dir = file_path.parent / "local_images"
            image_dir.mkdir(exist_ok=True)
            logger.info(f"Created/verified local_images directory: {image_dir}")

            for alt_text, image_url in image_links:
                image_hash = hashlib.md5(image_url.encode()).hexdigest()
                temp_path = image_dir / f"{image_hash}"
                
                existing_images = list(image_dir.glob(f"{image_hash}.*"))
                if existing_images:
                    msg = f"Image already exists: {existing_images[0].name}"
                    logger.info(msg)
                    print(Fore.BLUE + f"ℹ️  {msg}")
                    local_path = existing_images[0]
                else:
                    success, downloaded_path = self.download_image(image_url, temp_path)
                    if not success:
                        continue
                    local_path = Path(downloaded_path)

                relative_path = local_path.relative_to(file_path.parent)
                new_link = f"![{alt_text}]({relative_path})"
                content = content.replace(f"![{alt_text}]({image_url})", new_link)
                self.processed_images += 1
                logger.info(f"Replaced link: {image_url} -> {relative_path}")

            file_path.write_text(content, encoding='utf-8')
            self.processed_files += 1
            logger.info(f"Successfully processed file: {file_path}")
            print(Fore.GREEN + f"✅ File processed successfully")

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            print(Fore.RED + f"❌ {error_msg}")

    def process_directory(self) -> None:
        """Process all markdown files in directory."""
        try:
            # Create working copy
            working_dir = self.create_working_copy()
            if not working_dir:
                print(Fore.RED + "❌ Failed to create working copy, aborting process")
                return

            markdown_files = list(self.base_dir.rglob("*.md"))
            if not markdown_files:
                print(Fore.YELLOW + f"⚠️  No markdown files found in {self.base_dir}")
                return

            for file_path in markdown_files:
                self.process_markdown_file(file_path)

            self.print_summary()

        except Exception as e:
            print(Fore.RED + f"❌ Error processing directory: {str(e)}")

    def print_summary(self) -> None:
        """Print processing summary."""
        summary = [
            "="*50,
            "Processing Summary:",
            f"Original directory: {self.original_dir}",
            f"Processed directory: {self.base_dir}",
            f"Files processed: {self.processed_files}",
            f"Images processed: {self.processed_images}",
            f"Failed downloads: {self.failed_downloads}",
            "="*50
        ]
        
        # Log summary to file
        logger.info("\n".join(summary))
        
        # Print colored summary to console
        print("\n" + "="*50)
        print(Fore.CYAN + "📊 Processing Summary:")
        print(Fore.WHITE + f"📁 Original directory: {self.original_dir}")
        print(Fore.WHITE + f"📁 Processed directory: {self.base_dir}")
        print(Fore.GREEN + f"✅ Files processed: {self.processed_files}")
        print(Fore.GREEN + f"✅ Images processed: {self.processed_images}")
        print(Fore.RED + f"❌ Failed downloads: {self.failed_downloads}")
        print("="*50)

def main():
    """Main entry point."""
    try:
        directory = sys.argv[1] if len(sys.argv) > 1 else '.'
        logger.info(f"Starting image downloader for directory: {directory}")
        
        print(Fore.CYAN + f"\n📂 Target directory: {directory}")
        print(Fore.YELLOW + "ℹ️  A new directory will be created for processing.")
        print(Fore.YELLOW + "ℹ️  Original directory will remain unchanged.")
        response = input(Fore.WHITE + "Continue? (y/N): ").lower()
        
        if response != 'y':
            logger.info("Operation cancelled by user")
            print(Fore.YELLOW + "⚠️  Operation cancelled by user.")
            return
            
        downloader = ImageDownloader(directory)
        downloader.process_directory()

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        print(Fore.YELLOW + "\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(Fore.RED + f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Starting new session")
    main()