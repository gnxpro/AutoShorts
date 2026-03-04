import cloudinary
import cloudinary.uploader
import tempfile
import os
import time
from pathlib import Path


from core.config_manager import ConfigManager


class CloudinaryService:
    """
    Service untuk upload video ke Cloudinary.
    Menangani upload file video besar dan validasi file.
    """

    def __init__(self):
        """Initialize Cloudinary service dengan credentials dari config."""
        self.config = ConfigManager()
        cloud_conf = self.config.get_cloudinary()

        self.cloud_name = cloud_conf.get("cloud_name")
        self.api_key = cloud_conf.get("api_key")
        self.api_secret = cloud_conf.get("api_secret")

        if not all([self.cloud_name, self.api_key, self.api_secret]):
            raise Exception("Cloudinary credentials missing")

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    def _validate_file(self, file_path):
        """
        Validate that file exists and is readable.
        
        Args:
            file_path (str): Path to file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not readable or too small
        """
        if not file_path:
            raise ValueError("file_path cannot be empty")
        
        # Convert to Path object for better handling
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"File is not readable: {file_path}")
        
        # Check file size (must be at least 1KB)
        file_size = path.stat().st_size
        if file_size < 1024:
            raise ValueError(f"File is too small ({file_size} bytes): {file_path}")
        
        return True

    def _wait_for_file(self, file_path, max_wait_seconds=30):
        """
        Wait for file to be completely written to disk.
        
        Useful when file is being written by another process.
        
        Args:
            file_path (str): Path to file
            max_wait_seconds (int): Maximum time to wait
            
        Raises:
            TimeoutError: If file is not ready within timeout
        """
        start_time = time.time()
        last_size = 0
        stable_count = 0
        
        while time.time() - start_time < max_wait_seconds:
            try:
                if os.path.exists(file_path):
                    current_size = os.path.getsize(file_path)
                    
                    # If file size hasn't changed for 2 checks, it's probably done
                    if current_size == last_size and current_size > 0:
                        stable_count += 1
                        if stable_count >= 2:
                            return True
                    else:
                        stable_count = 0
                    
                    last_size = current_size
            except OSError:
                pass
            
            time.sleep(0.5)
        
        raise TimeoutError(f"File not ready after {max_wait_seconds} seconds: {file_path}")

    def test_connection(self):
        """
        Test Cloudinary connection.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            Exception: If connection fails
        """
        try:
            # Create temporary small file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(b"GNX Cloudinary Test")
                tmp_path = tmp.name

            # Upload small raw file
            result = cloudinary.uploader.upload(
                tmp_path,
                resource_type="raw",
                folder="gnx_test"
            )

            public_id = result.get("public_id")

            # Delete uploaded test file
            if public_id:
                cloudinary.uploader.destroy(
                    public_id,
                    resource_type="raw"
                )

            os.remove(tmp_path)

            return True

        except Exception as e:
            raise Exception(f"Cloudinary connection failed: {str(e)}")

    def upload_video(self, file_path, wait_for_file=True, max_wait_seconds=30):
        """
        Upload video to Cloudinary.
        
        Args:
            file_path (str): Path to video file
            wait_for_file (bool): Wait for file to be completely written
            max_wait_seconds (int): Maximum time to wait for file
            
        Returns:
            str: Secure URL of uploaded video
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid
            Exception: If upload fails
        """
        
        # Normalize path
        file_path = os.path.abspath(file_path)
        
        # Wait for file to be ready if requested
        if wait_for_file:
            try:
                self._wait_for_file(file_path, max_wait_seconds)
            except TimeoutError as e:
                raise TimeoutError(f"Video file not ready: {e}")
        
        # Validate file
        try:
            self._validate_file(file_path)
        except (FileNotFoundError, ValueError, PermissionError) as e:
            raise ValueError(f"Invalid video file: {e}")
        
        # Get file info for logging
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        try:
            # Upload large video file
            result = cloudinary.uploader.upload_large(
                file_path,
                resource_type="video",
                folder="gnx_videos",
                timeout=600  # 10 minutes timeout for large files
            )
            
            secure_url = result.get("secure_url")
            
            if not secure_url:
                raise Exception("Upload successful but no URL returned")
            
            return secure_url
            
        except cloudinary.exceptions.Error as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")


# Example usage for testing
if __name__ == "__main__":
    try:
        service = CloudinaryService()
        
        # Test connection
        print("Testing Cloudinary connection...")
        if service.test_connection():
            print("✓ Connection successful!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
