
import logging

logger = logging.getLogger(__name__)

class ImageETL:
    
    def __init__(self, file):
        self.file = file
        self.reader = "SET_READER"
        self.loader = "SET_LOADER"

    def extract_image_data():
        """extracts text using OCR"""
        pass

    def transform_image_to_render_image():
        """For each image create a render image"""
        pass

    def load_image_data():
        """Save image data to a vector db"""
        pass

    def execute(self):
        """Apply etl pipeline"""
        logger.warn(f"status=WIP {self.file.name} will not be processed")
