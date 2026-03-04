import cloudinary
import cloudinary.uploader
import tempfile
import os

from core.config_manager import ConfigManager


class CloudinaryService:

    def __init__(self):

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

    # =====================================================
    # PRODUCTION TEST CONNECTION (NO 404)
    # =====================================================

    def test_connection(self):
        try:
            # create temporary small file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(b"GNX Cloudinary Test")
                tmp_path = tmp.name

            # upload small raw file
            result = cloudinary.uploader.upload(
                tmp_path,
                resource_type="raw",
                folder="gnx_test"
            )

            public_id = result.get("public_id")

            # delete uploaded test file
            if public_id:
                cloudinary.uploader.destroy(
                    public_id,
                    resource_type="raw"
                )

            os.remove(tmp_path)

            return True

        except Exception as e:
            raise Exception(f"Cloudinary connection failed: {str(e)}")

    # =====================================================
    # VIDEO UPLOAD (PRODUCTION)
    # =====================================================

    def upload_video(self, file_path):

        result = cloudinary.uploader.upload_large(
            file_path,
            resource_type="video"
        )

        return result.get("secure_url")