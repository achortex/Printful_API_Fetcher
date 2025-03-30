import streamlit as st
from typing import Dict, List, Any
import base64
from src.api.printful import PrintfulAPI

def set_page_config():
    """Set the page configuration for the Streamlit app"""
    st.set_page_config(
        page_title="Printful API Fetcher for Products, Variants, Templates and Mockups",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_css():
    """Apply custom CSS to the Streamlit app"""
    # Initialize theme in session state if not already set
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Define CSS variables based on theme
    bg_color = "#f5f5f5" if st.session_state.theme == 'light' else "#1e1e1e"
    text_color = "#333333" if st.session_state.theme == 'light' else "#e0e0e0"
    heading_color = "#2E7D32" if st.session_state.theme == 'light' else "#4CAF50"
    button_bg = "#4CAF50" if st.session_state.theme == 'light' else "#2E7D32"
    button_hover_bg = "#2E7D32" if st.session_state.theme == 'light' else "#1b5e20"
    card_bg = "white" if st.session_state.theme == 'light' else "#2d2d2d"
    card_border = "#e0e0e0" if st.session_state.theme == 'light' else "#444444"
    sidebar_bg = "#f0f0f0" if st.session_state.theme == 'light' else "#252525"
    footer_color = "#666" if st.session_state.theme == 'light' else "#999"
    expander_border = "#e0e0e0" if st.session_state.theme == 'light' else "#444444"
    
    # Dark mode specific CSS
    dark_mode_css = ""
    if st.session_state.theme == 'dark':
        dark_mode_css = """
        .stTextInput>div>div>input {  
            background-color: #333;
            color: #e0e0e0;
        }
        .stSelectbox>div>div>div {  
            background-color: #333;
            color: #e0e0e0;
        }
        .stMultiSelect>div>div>div {  
            background-color: #333;
            color: #e0e0e0;
        }
        """
    
    # Apply CSS
    st.markdown(f"""
    <style>
    /* CSS Variables for theming */
    :root {{
        --background-color: {bg_color};
        --text-color: {text_color};
        --heading-color: {heading_color};
        --button-bg: {button_bg};
        --button-hover-bg: {button_hover_bg};
        --card-bg: {card_bg};
        --card-border: {card_border};
        --sidebar-bg: {sidebar_bg};
        --footer-color: {footer_color};
        --expander-border: {expander_border};
    }}
    
    /* Apply variables to elements */
    .main {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    .stApp {{
        max-width: 1200px;
        margin: 0 auto;
        color: var(--text-color);
    }}
    h1, h2, h3 {{
        color: var(--heading-color);
    }}
    p {{
        color: var(--text-color);
    }}
    .stButton>button {{
        background-color: var(--button-bg);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: var(--button-hover-bg);
    }}
    .download-button {{
        display: inline-block;
        background-color: var(--button-bg);
        color: white;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        border-radius: 4px;
        margin: 4px 2px;
        cursor: pointer;
    }}
    .download-button:hover {{
        background-color: var(--button-hover-bg);
    }}
    .stExpander {{
        border-radius: 8px;
        border: 1px solid var(--expander-border);
    }}
    .stAlert {{
        border-radius: 8px;
    }}
    .stProgress .st-bo {{
        background-color: var(--button-bg);
    }}
    .stSidebar .sidebar-content {{
        background-color: var(--sidebar-bg);
    }}
    .product-card {{
        border: 1px solid var(--card-border);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        background-color: var(--card-bg);
        color: var(--text-color);
    }}
    .product-card:hover {{
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    .footer {{
        text-align: center;
        margin-top: 40px;
        padding: 20px;
        border-top: 1px solid var(--card-border);
        color: var(--footer-color);
    }}
    /* Dark mode adjustments for Streamlit components */
    {dark_mode_css}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the app header"""
    st.markdown("<h1 style='text-align: center;'>Printful API Fetcher for Products, Variants, Templates and Mockups</h1>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    Visualize and automate the process of linking products and variants with custom apps using the Printful API.
    This tool helps you fetch product data and prepare it for custom app integration by generating JSON files
    containing all necessary information and images.
    
    ⚠️ **Note:** This application is currently under construction. Some features may be missing or contain bugs.
    """)
    st.divider()

def render_sidebar(api: PrintfulAPI):
    """Render the sidebar
    
    Args:
        api: PrintfulAPI instance
    """
    with st.sidebar:
        st.header("🔧 Tools")
        
        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Select Data Type",
            ["Printing Templates", "Mockups"],
            key="navigation"
        )
        
        st.divider()
        
        # Theme Toggle
        st.subheader("Appearance")
        theme_options = {"Light": "light", "Dark": "dark"}
        selected_theme = st.radio(
            "Theme",
            options=list(theme_options.keys()),
            index=0 if st.session_state.theme == "light" else 1,
            key="theme_selector"
        )
        
        # Update theme in session state if changed
        if theme_options[selected_theme] != st.session_state.theme:
            st.session_state.theme = theme_options[selected_theme]
            st.rerun()
        
        st.divider()
        
        # Cache Controls
        st.subheader("Cache Controls")
        if st.button("Clear API Cache"):
            api.clear_cache()
            st.session_state.downloaded_images = {}
            st.success("Cache cleared successfully!")
        
        # Cache Info
        st.info(f"API Cache: {len(st.session_state.api_cache)} items")
        if 'downloaded_images' in st.session_state:
            st.info(f"Downloaded Images: {len(st.session_state.downloaded_images)} items")
        
        # API Status
        st.divider()
        st.subheader("API Status")
        api_valid = api.validate_api_key()
        if api_valid:
            st.success("✅ API connection successful")
        else:
            st.error("❌ API connection failed")
        
        # About
        st.divider()
        st.subheader("About")
        st.markdown("""
        **Printful API Fetcher for Products, Variants, Templates and Mockups**
        
        Version 0.9.0 (Beta)
        
        [GitHub Repository](https://github.com/achortex/Printful_API_Fetcher)
        
        Made by Abdelhamid Chihabi (Achortex)
        """)
    
    return page

def render_footer():
    """Render the app footer"""
    st.markdown("""
    <div class="footer">
    <p>© 2025 Printful API Fetcher for Products, Variants, Templates and Mockups | 
    <a href="https://github.com/achortex/Printful_API_Fetcher" target="_blank">GitHub</a>
    </p>
    </div>
    """, unsafe_allow_html=True)

def render_product_selection(api: PrintfulAPI) -> List[Dict[str, Any]]:
    """Render the product selection UI
    
    Args:
        api: PrintfulAPI instance
        
    Returns:
        List[Dict[str, Any]]: List of selected products
    """
    st.header("Step 1: Select Products from Your Store", divider="rainbow")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fetch_button = st.button("Fetch Store Products", key="fetch_button")
    with col2:
        force_refresh = st.checkbox("Force Refresh", key="force_refresh", 
                                  help="Force refresh data from API instead of using cache")
    
    if fetch_button:
        with st.spinner("Fetching products from your store..."):
            store_products = api.fetch_store_products(force_refresh)
        
        if store_products:
            st.success(f"Found {len(store_products)} products in your store")
        else:
            st.error("No products found in your store")
    
    selected_products = []
    
    if 'store_products' in st.session_state:
        product_options = {f"{p['name']} (ID: {p['id']}, Catalog ID: {p.get('catalog_product_id', 'N/A')})" : p 
                          for p in st.session_state.store_products}
        
        selected_product_names = st.multiselect(
            "Select Products",
            options=list(product_options.keys()),
            key="product_select"
        )
        
        if selected_product_names:
            selected_products = [product_options[name] for name in selected_product_names]
            st.success(f"Selected {len(selected_products)} products")
            
            # Display selected products in a grid
            cols = st.columns(3)
            for idx, product in enumerate(selected_products):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="product-card">
                    <h4>{product['name']}</h4>
                    <p>ID: {product['id']}</p>
                    <p>Catalog ID: {product.get('catalog_product_id', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    return selected_products

def load_background_image():
    """Load a background image for the app based on the current theme"""
    # Different background images for light and dark modes
    light_bg = "https://static.vecteezy.com/system/resources/previews/002/099/443/original/abstract-white-background-with-light-gray-waves-free-vector.jpg"
    dark_bg = "https://static.vecteezy.com/system/resources/previews/007/295/846/original/dark-blue-technology-background-with-digital-data-visualization-network-connection-concept-free-vector.jpg"
    
    # Select background based on theme
    bg_url = light_bg if st.session_state.get('theme', 'light') == 'light' else dark_bg
    
    background_image = f"""
    <style>
    .stApp {{
        background-image: url("{bg_url}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(background_image, unsafe_allow_html=True)

def display_progress_bar(progress_text: str, total_items: int, current_item: int):
    """Display a progress bar
    
    Args:
        progress_text: Text to display above the progress bar
        total_items: Total number of items
        current_item: Current item number
    """
    progress = st.progress(0)
    status_text = st.empty()
    
    if total_items > 0:
        percent_complete = current_item / total_items
        progress.progress(percent_complete)
        status_text.text(f"{progress_text} ({current_item}/{total_items})")
    else:
        progress.progress(0)
        status_text.text(f"{progress_text} (0/0)")

def show_api_key_input():
    """Show API key input field and save to session state"""
    st.header("Printful API Key Setup")
    
    api_key = st.text_input(
        "Enter your Printful API Key",
        type="password",
        help="You can find your API key in your Printful account settings",
        key="api_key_input",
        autocomplete="off",
        label_visibility="visible",
        placeholder="Enter API key here...",
        kwargs={"style": "border: 2px solid #4CAF50; border-radius: 5px; padding: 8px;"}
    )
    
    if st.button("Save API Key"):
        if api_key:
            # Clear any existing cache when changing API key
            if 'api_cache' in st.session_state:
                st.session_state.api_cache = {}
            if 'store_products' in st.session_state:
                st.session_state.store_products = []
            if 'product_variants_cache' in st.session_state:
                st.session_state.product_variants_cache = {}
            if 'template_data_cache' in st.session_state:
                st.session_state.template_data_cache = {}
            if 'mockup_styles_cache' in st.session_state:
                st.session_state.mockup_styles_cache = {}
            if 'mockup_images_cache' in st.session_state:
                st.session_state.mockup_images_cache = {}
                
            # Save API key to session state
            st.session_state.api_key = api_key
            st.success("API key saved successfully!")
            st.rerun()
        else:
            st.error("Please enter a valid API key")
    
    st.markdown("""
    ### How to use this tool:
    1. Create a store in [Printful](https://www.printful.com/dashboard)
    2. Add products to your store
    3. Get your API key from settings
    4. Paste your API key above to start generating mockups
    
    Note: The mockups generated will be blank templates. The colors and sizes for each product variant are available in the JSON response after generation is complete.
    """)

def display_image_gallery(images: List[Dict[str, str]], columns: int = 3):
    """Display a gallery of images
    
    Args:
        images: List of dictionaries with 'path', 'caption', and 'download_name' keys
        columns: Number of columns in the gallery
    """
    if not images:
        st.info("No images to display")
        return
    
    cols = st.columns(columns)
    
    for i, image_data in enumerate(images):
        col_idx = i % columns
        with cols[col_idx]:
            st.image(image_data['path'], caption=image_data.get('caption', ''))
            if 'download_name' in image_data:
                st.markdown(
                    get_download_link(
                        image_data['path'], 
                        image_data['download_name']
                    ), 
                    unsafe_allow_html=True
                )

def get_download_link(file_path: str, filename: str, file_type: str = "file/png") -> str:
    """Generate a download link for a file
    
    Args:
        file_path: Path to the file
        filename: Filename to use for download
        file_type: MIME type of the file
        
    Returns:
        str: HTML download link
    """
    with open(file_path, "rb") as file:
        file_bytes = file.read()
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:{file_type};base64,{b64}" download="{filename}" class="download-button">Download {filename}</a>'
    return href

def show_json_preview(data: Dict[str, Any], max_height: str = "300px"):
    """Show a preview of JSON data with a max height
    
    Args:
        data: JSON data to display
        max_height: Maximum height of the preview
    """
    st.json(data)
    
def show_help_section():
    """Show a help section with instructions"""
    with st.expander("ℹ️ Help & Instructions"):
        st.markdown("""
        ## How to use this tool
        
        ### Printing Templates
        1. **Select Products**: Choose the products from your store for which you want to generate templates
        2. **Generate Templates**: For each product, select the placement and template style
        3. **Save Templates**: Save the generated templates to your computer
        
        ### Mockups
        1. **Select Products**: Choose the products from your store for which you want to generate mockups
        2. **Upload Designs**: Upload your design files for each product
        3. **Generate Mockups**: Generate mockups with your designs
        4. **Save Mockups**: Save the generated mockups to your computer
        
        ### Tips
        - Use the "Force Refresh" option if you've recently added new products to your store
        - Clear the cache if you encounter any issues
        - For best results, upload designs that match the template dimensions
        """)