import os
import json
import base64
from typing import Dict, List, Any
from datetime import datetime
import zipfile
import io
import streamlit as st

def get_download_link(image_data, filename: str, file_type: str = "image/png") -> str:
    """Generate a download link for image data
    
    Args:
        image_data: Image data as bytes
        filename: Filename to use for download
        file_type: MIME type of the file
        
    Returns:
        str: HTML download link
    """
    if isinstance(image_data, str):
        # For backward compatibility with file paths
        try:
            with open(image_data, "rb") as file:
                image_data = file.read()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return ""
    
    if image_data is None:
        return ""
        
    b64 = base64.b64encode(image_data).decode()
    href = f'<a href="data:{file_type};base64,{b64}" download="{filename}" class="download-button">Download {filename}</a>'
    return href

def save_json_data(data: List[Dict[str, Any]], filename: str) -> str:
    """Save data to a JSON file
    
    Args:
        data: Data to save
        filename: Filename to save to
        
    Returns:
        str: Path to the saved file
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

def create_zip_file(data: List[Dict[str, Any]], file_prefix: str = "data") -> str:
    """Create a ZIP file containing JSON data and image files
    
    Args:
        data: Data containing image data
        temp_dir: Deprecated parameter, kept for backward compatibility
        file_prefix: Prefix for the ZIP and JSON filenames
        
    Returns:
        str: HTML download link for the ZIP file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{file_prefix}_{timestamp}.zip"
    json_filename = f"{file_prefix}_{timestamp}.json"
    
    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add JSON data to the ZIP file
        # Create a copy of data without the image binary data to reduce JSON size
        json_data_copy = []
        for item in data:
            item_copy = item.copy()
            # Remove binary image data from JSON, keep URLs
            for key in ["template_image", "mockup_image"]:
                if key in item_copy:
                    del item_copy[key]
            
            # Also remove template_image from nested templates
            if "templates" in item_copy:
                for template in item_copy["templates"]:
                    if "template_image" in template:
                        del template["template_image"]
                        
            json_data_copy.append(item_copy)
            
        json_data = json.dumps(json_data_copy, indent=2, ensure_ascii=False)
        zip_file.writestr(json_filename, json_data)
        
        # Add all image data to the ZIP file
        for item in data:
            # Handle template and mockup images
            for image_key, path_key, prefix in [("template_image", "template_path", "template"), 
                                               ("mockup_image", "mockup_path", "mockup")]:
                # Check for new image data format
                if image_key in item and item[image_key]:
                    image_filename = f"{prefix}_{item.get('catalog_product_id', '')}_{item.get('placement', '')}.png"
                    zip_file.writestr(image_filename, item[image_key])
                # Backward compatibility with file paths
                elif path_key in item and item[path_key] and isinstance(item[path_key], str) and os.path.exists(item[path_key]):
                    image_filename = os.path.basename(item[path_key])
                    zip_file.write(item[path_key], arcname=image_filename)
            
            # Handle nested templates
            if "templates" in item:
                for template in item["templates"]:
                    if "template_image" in template and template["template_image"]:
                        image_filename = f"template_{template.get('variant_id', '')}.png"
                        zip_file.writestr(image_filename, template["template_image"])
                    elif "template_path" in template and template["template_path"] and isinstance(template["template_path"], str) and os.path.exists(template["template_path"]):
                        image_filename = os.path.basename(template["template_path"])
                        zip_file.write(template["template_path"], arcname=image_filename)
    
    # Create download link for the ZIP file
    zip_buffer.seek(0)
    zip_b64 = base64.b64encode(zip_buffer.getvalue()).decode()
    zip_href = f'<a href="data:application/zip;base64,{zip_b64}" download="{zip_filename}" class="download-button">Download The Json File and {file_prefix.capitalize()} as ZIP</a>'
    
    return zip_href

def generate_timestamp() -> str:
    """Generate a timestamp string
    
    Returns:
        str: Timestamp string in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")