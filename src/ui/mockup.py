import streamlit as st
import os

from src.api.printful import PrintfulAPI
from src.utils.image import download_image
from src.utils.file import get_download_link, create_zip_file

def render_mockup_generator(api: PrintfulAPI):
    """Render the Mockups fetcher UI
    
    This component fetches product data and mockup images from the Printful API for products in your store.
    It prepares the data for custom app integration by generating JSON files containing all necessary information.
    
    Args:
        api: PrintfulAPI instance
    """
    st.header("Product Mockup Data", divider="rainbow")
    
    # Initialize session state variables if they don't exist
    if 'selected_mockup_products' not in st.session_state:
        st.session_state.selected_mockup_products = []
    
    if 'mockup_current_step' not in st.session_state:
        st.session_state.mockup_current_step = 1
    
    # Step 1: Select Products
    st.subheader("Step 1: Select Products from Your Store")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fetch_button = st.button("Fetch Store Products", key="mockup_fetch_button")
    with col2:
        force_refresh = st.checkbox("Force Refresh", key="mockup_force_refresh", 
                                  help="Force refresh data from API instead of using cache")
    
    if fetch_button:
        with st.spinner("Fetching products from your store..."):
            store_products = api.fetch_store_products(force_refresh)
        
        if store_products:
            st.success(f"Found {len(store_products)} products in your store")
        else:
            st.error("No products found in your store")
    
    if 'store_products' in st.session_state:
        product_options = {f"{p['name']} (ID: {p['id']}, Catalog ID: {p.get('catalog_product_id', 'N/A')})" : p 
                          for p in st.session_state.store_products}
        
        selected_product_names = st.multiselect(
            "Select Products",
            options=list(product_options.keys()),
            key="mockup_product_select"
        )
        
        if selected_product_names:
            selected_products = [product_options[name] for name in selected_product_names]
            st.session_state.selected_mockup_products = selected_products
            st.success(f"Selected {len(selected_products)} products")
            
            for idx, product in enumerate(selected_products):
                st.write(f"{idx+1}. {product['name']} (ID: {product['id']})")
        
        if st.session_state.selected_mockup_products and st.button("Confirm Selection and Proceed to Step 2", key="mockup_proceed_button"):
            st.session_state.mockup_current_step = 2
            st.rerun()
        
        if st.session_state.mockup_current_step == 2 and st.session_state.selected_mockup_products:
            st.header("Step 2: Generate Mockups")
            
            all_mockup_data = []
            
            for product_index, product in enumerate(st.session_state.selected_mockup_products):
                st.subheader(f"Processing Product {product_index+1}/{len(st.session_state.selected_mockup_products)}: {product['name']}")
                
                product_id = product['id']
                catalog_product_id = product.get('catalog_product_id')
                
                if not catalog_product_id:
                    st.warning(f"No catalog product ID available for {product['name']}. Skipping.")
                    continue
                
                with st.spinner(f"Fetching mockup styles for {product['name']}..."):
                    mockup_styles_result = api.get_mockup_styles(catalog_product_id, force_refresh)
                    mockup_styles_data = mockup_styles_result[0]
                    print_area_width = mockup_styles_result[1]
                    print_area_height = mockup_styles_result[2]
                    dpi = mockup_styles_result[3]
                    print_area_type = mockup_styles_result[4]
                    technique = mockup_styles_result[5]
                
                if not mockup_styles_data or "data" not in mockup_styles_data or not mockup_styles_data["data"]:
                    st.warning(f"No mockup styles available for {product['name']}. Skipping.")
                    continue
                
                mockup_style_options = {}
                
                for style in mockup_styles_data["data"]:
                    mockup_styles = style.get('mockup_styles', [])
                    
                    for mockup_style in mockup_styles:
                        style_id = mockup_style.get('id')
                        category_name = mockup_style.get('category_name', 'Unknown')
                        view_name = mockup_style.get('view_name', 'Unknown')
                        restricted_variants = mockup_style.get('restricted_to_variants')
                        
                        restriction_info = " (Restricted)" if restricted_variants else ""
                        mockup_style_options[f"{category_name} - {view_name} (ID: {style_id}){restriction_info}"] = {
                            "style_id": style_id,
                            "category_name": category_name,
                            "view_name": view_name,
                            "restricted_to_variants": restricted_variants
                        }
                
                selected_style_key = st.selectbox(
                    f"Select Mockup Style for {product['name']}",
                    options=list(mockup_style_options.keys()),
                    key=f"style_{product_id}"
                )
                
                if selected_style_key:
                    selected_style = mockup_style_options[selected_style_key]
                    mockup_style_id = selected_style["style_id"]
                    
                    with st.spinner(f"Fetching mockup images for style {mockup_style_id}..."):
                        mockup_images_data = api.get_mockup_images(catalog_product_id, mockup_style_id, force_refresh)
                    
                    if not mockup_images_data or "data" not in mockup_images_data or not mockup_images_data["data"]:
                        st.warning(f"No mockup images available for style {mockup_style_id}. Skipping.")
                        continue
                    
                    main_category_id = ""
                    category_title = ""
                    variants_data = []
                    product_details = api.make_request(f"/store/products/{product_id}")

                    if product_details and "result" in product_details and "sync_variants" in product_details["result"]:
                        for variant in product_details["result"]["sync_variants"]:
                            variant_id = variant["product"]["variant_id"]
                            
                            variant_details = api.make_request(f"/products/variant/{variant_id}")

                            size = ""
                            color_code = ""
                            in_stock = False
                            
                            if variant_details and "result" in variant_details:
                                variant_result = variant_details["result"]["variant"]
                                size = variant_result.get("size").replace('\u2033', 'in').replace('\u00d7', 'x')
                                color_code = variant_result.get("color_code")
                                in_stock = variant_result.get("in_stock")
                                if not main_category_id:
                                    main_category_id = variant_details["result"]["product"].get("main_category_id", "")
                                    category_title = variant_details["result"]["product"].get("type", "")
                            
                            variants_data.append({
                                "catalog_variant_id": variant_id,
                                "size": size,
                                "color_code": color_code,
                                "in_stock": in_stock
                            })
                    
                    mockup_image = None
                    mockup_url = None
                    selected_placement = None
                    
                    for variant_data in mockup_images_data["data"]:
                        for image_data in variant_data.get('images', []):
                            image_placement = image_data.get('placement')
                            mockup_url = image_data.get('image_url')
                            
                            if mockup_url:
                                mockup_image = {
                                    "variant_id": variant_data.get('catalog_variant_id'),
                                    "color": variant_data.get('color', 'Unknown'),
                                    "image_url": mockup_url
                                }
                                selected_placement = image_placement
                                break
                        if mockup_image:
                            break
                            
                    if not selected_placement:
                        selected_placement = 'front'
                    
                    if mockup_image and mockup_url:
                        st.subheader(f"Mockup Image for {product['name']}")
                        
                        mockup_image, image_url = download_image(
                            mockup_url,
                            catalog_product_id,
                            selected_placement,
                            mockup_style_id
                        )
                        
                        if mockup_image:
                            st.image(mockup_image, caption=f"{product['name']} - {selected_placement}")
                            
                            filename = f"mockup_{catalog_product_id}_{selected_placement}_{mockup_style_id}.png"
                            st.markdown(get_download_link(mockup_image, filename), unsafe_allow_html=True)
                            
                            mockup_data = {
                                "product_id": product_id,
                                "catalog_product_id": catalog_product_id,
                                "name": product['name'],
                                "placement": selected_placement,
                                "main_category_id": main_category_id,
                                "category_title": category_title,
                                "technique": technique,
                                "dpi": dpi,
                                "print_area_width": print_area_width,
                                "print_area_height": print_area_height,
                                "print_area_type": print_area_type,
                                "mockup_name": f"{selected_style['category_name']} - {selected_style['view_name']} (ID: {mockup_style_id}){' (Restricted)' if selected_style['restricted_to_variants'] else ''}",
                                "mockup_url": image_url,
                                "mockup_image": mockup_image,
                                "variants": variants_data,
                                "variant_ids_restricted": selected_style['restricted_to_variants'] or [],
                            }
                            
                            all_mockup_data.append(mockup_data)
                            
                            with st.expander(f"Mockup Information for {product['name']}"):
                                # Create a copy without the binary image data for display
                                display_data = mockup_data.copy()
                                if "mockup_image" in display_data:
                                    del display_data["mockup_image"]
                                st.json(display_data)
                        else:
                            st.warning(f"Failed to download mockup image for {product['name']}")
                    else:
                        st.warning(f"No mockup images found for the selected placement and style for {product['name']}")
            
            if all_mockup_data:
                if st.button("Export All Mockup Data", key="save_mockup_data"):
                    # Create a ZIP file with all mockup data and images
                    zip_href = create_zip_file(all_mockup_data, file_prefix="mockups")
                    
                    st.success(f"All mockups data and images prepared for download")
                    st.markdown(zip_href, unsafe_allow_html=True)
                    
                    # Display mockup usage instructions
                    with st.expander("How to use these mockups"):
                        st.markdown("""
                        ### Mockup Usage Instructions
                        
                        1. **Download the ZIP file** containing all mockups and JSON data
                        2. **Extract the ZIP file** to access all mockup images and data
                        3. **Use in your online store** to showcase your products
                        4. **Share on social media** to promote your products
                        5. **Include in marketing materials** for a professional look
                        
                        #### Image Quality
                        The mockups are high-quality images suitable for web and print use.
                        
                        #### JSON Data
                        The JSON file contains all the mockup information, which can be useful for automated workflows.
                        """)