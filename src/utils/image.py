import requests
from urllib.parse import urlparse, unquote
import streamlit as st
import base64
from io import BytesIO

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def download_image(url, product_id, placement, style_id, temp_dir=None):
    """Download image and cache it using Streamlit's cache_data decorator
    
    Args:
        url: URL of the image to download
        product_id: Product ID
        placement: Placement (e.g., 'front', 'back')
        style_id: Style ID or identifier
        temp_dir: Deprecated parameter, kept for backward compatibility
        
    Returns:
        Tuple[bytes, str]: Image data as bytes and the original URL
    """
    try:
        # Create a unique key for this image
        image_key = f"{product_id}_{placement}_{style_id}"
        
        # Download the image
        with st.spinner(f"Downloading image..."):
            response = requests.get(url)
            if response.status_code == 200:
                # Return the image data directly
                return response.content, url
            else:
                st.error(f"Failed to download image: {response.status_code}")
                return None, url
    except Exception as e:
        st.error(f"Error downloading image: {e}")
        return None, url

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_image_as_base64(image_data):
    """Convert image data to base64 encoding
    
    Args:
        image_data: Image data as bytes
        
    Returns:
        str: Base64 encoded image data
    """
    if image_data is None:
        return None
    return base64.b64encode(image_data).decode()

def get_download_link(image_data, filename, file_type="image/png"):
    """Generate a download link for image data
    
    Args:
        image_data: Image data as bytes
        filename: Filename to use for download
        file_type: MIME type of the file
        
    Returns:
        str: HTML download link
    """
    if image_data is None:
        return ""
    
    b64 = get_image_as_base64(image_data)
    href = f'<a href="data:{file_type};base64,{b64}" download="{filename}" class="download-button">Download {filename}</a>'
    return href