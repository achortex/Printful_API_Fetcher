import streamlit as st
from dotenv import load_dotenv

from src.api.printful import PrintfulAPI
from src.ui.common import set_page_config, apply_custom_css, render_header, render_sidebar, render_footer, show_api_key_input, load_background_image
from src.ui.template import render_template_generator
from src.ui.mockup import render_mockup_generator
from config import BASE_URL

def main():
    """Main application entry point for the Printful API Fetcher for Products, Variants, Templates and Mockups
    
    This application helps visualize and automate the process of linking products and variants with custom apps
    using the Printful API. It fetches product data and prepares it for custom app integration by generating
    JSON files containing all necessary information and images.
    
    NOTE: This application was created for personal use while working on a separate project to simplify
    the process of implementing Printful's print-on-demand system into a web application. It is not an
    official Printful tool and is currently under construction. Some features may be missing or contain bugs.
    """
    # Load environment variables
    load_dotenv()
    
    # No need for temp directory with Streamlit's built-in caching
    
    # Set page configuration
    set_page_config()
    
    # Apply custom CSS
    apply_custom_css()
    
    # Load background image
    load_background_image()
    
    # Render header
    render_header()
    
    # Check if API key is in session state (from user input)
    api_key = ""
    if 'api_key' in st.session_state:
        api_key = st.session_state.api_key
    
    # Initialize API client with the API key from session state
    api = PrintfulAPI(api_key, BASE_URL)
    
    # If no API key is set, show the API key input form
    if not api_key:
        show_api_key_input()
        render_footer()
        return
    
    # Validate API key
    if not api.validate_api_key():
        st.error("Invalid API key. Please check your API key and try again.")
        show_api_key_input()
        render_footer()
        return
    
    # Render sidebar and get selected page
    page = render_sidebar(api)
    
    # Render selected page
    if page == "Printing Templates":
        render_template_generator(api)
    else:
        render_mockup_generator(api)
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()