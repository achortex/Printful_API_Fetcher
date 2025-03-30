import streamlit as st
import os
import time
import json
import zipfile
import io
import base64

from src.api.printful import PrintfulAPI
from src.utils.image import download_image
from src.utils.file import get_download_link, create_zip_file

def render_template_generator(api: PrintfulAPI):
    """Render the Printing Templates UI
    
    This component fetches existing templates from the Printful API for products in your store.
    It does NOT generate templates from user-uploaded designs.
    
    Args:
        api: PrintfulAPI instance
    """
    st.header("Printing Templates", divider="rainbow")
    
    # Step 1: Select Products
    st.header("Step 1: Select Products from Your Store")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        fetch_button = st.button("Fetch Store Products", key="template_fetch_button")
    with col2:
        force_refresh = st.checkbox("Force Refresh", key="template_force_refresh", 
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
            key="template_product_select"
        )
        
        if selected_product_names:
            selected_products = [product_options[name] for name in selected_product_names]
            st.session_state.selected_products = selected_products
            st.success(f"Selected {len(selected_products)} products")
    
    if selected_products:
        st.header("Step 2: Generate templates for Selected Products")
        
        all_products_templates = []
        
        for product in selected_products:
            st.subheader(f"Product: {product['name']}")
            
            product_id = product['id']
            catalog_product_id = product.get('catalog_product_id')
            
            if not catalog_product_id:
                st.warning(f"No catalog product ID available for {product['name']}")
                continue
            
            with st.spinner(f"Fetching variants for {product['name']}..."):
                variants, main_category_id, category_title = api.get_product_variants(product_id, force_refresh)
            
            if not variants:
                st.warning(f"No variants found for {product['name']}")
                continue
            
            catalog_variant_ids = [variant["catalog_variant_id"] for variant in variants]
            
            with st.spinner(f"Fetching templates for {product['name']}..."):
                template_data = api.get_catalog_variant_templates(catalog_product_id, catalog_variant_ids)
            
            if not template_data or "data" not in template_data or not template_data["data"]:
                st.warning(f"No templates available for {product['name']}")
                continue
            
            available_placements = set()
            for template in template_data["data"]:
                placement = template.get('placement')
                if placement:
                    available_placements.add(placement)
            
            default_placement = 'front' if 'front' in available_placements else next(iter(available_placements), None)
            
            selected_placement = st.selectbox(
                "Select Placement",
                options=sorted(available_placements),
                index=sorted(available_placements).index(default_placement) if default_placement else 0,
                key=f"placement_{product_id}"
            )
            
            filtered_templates = [t for t in template_data["data"] if t.get('placement') == selected_placement]
            
            if not filtered_templates:
                st.warning(f"No templates available for placement: {selected_placement}")
                continue
            
            templates = filtered_templates
            templates_by_size = {}
            techniques_by_template = {}
            templates_by_variant = {}
            
            for template in templates:
                template_variant_ids = template.get('catalog_variant_ids', [])
                technique = template.get('technique', 'Unknown')
                image_url = template.get('image_url', '')
                
                supported_sizes = set()
                for variant in variants:
                    if variant["catalog_variant_id"] in template_variant_ids:
                        supported_sizes.add(variant["size"])
                        
                        variant_key = variant["catalog_variant_id"]
                        if variant_key not in templates_by_variant:
                            templates_by_variant[variant_key] = []
                        templates_by_variant[variant_key].append(template)
                
                size_key = tuple(sorted(supported_sizes))
                if size_key not in templates_by_size:
                    templates_by_size[size_key] = []
                templates_by_size[size_key].append(template)
                
                if image_url not in techniques_by_template:
                    techniques_by_template[image_url] = set()
                techniques_by_template[image_url].add(technique)
            
            templates_vary_by_size = len(templates_by_size) > 1
            
            unique_image_urls = set(template.get('image_url', '') for template in templates)
            templates_have_different_urls = len(unique_image_urls) > 1
            
            if not templates_vary_by_size and len(templates) > 1 and not templates_have_different_urls:
                unique_templates = {}
                for template in templates:
                    image_url = template.get('image_url', '')
                    if image_url not in unique_templates:
                        unique_templates[image_url] = template
                templates = list(unique_templates.values())
            
            template_options = {}
            for i, template in enumerate(templates, 1):
                template_variant_ids = template.get('catalog_variant_ids', [])
                supported_sizes = []
                for variant in variants:
                    if variant["catalog_variant_id"] in template_variant_ids:
                        if variant["size"] not in supported_sizes:
                            supported_sizes.append(variant["size"])
                
                image_url = template.get('image_url', '')
                techniques = list(techniques_by_template.get(image_url, ['Unknown']))
                
                size_info = f" (Sizes: {', '.join(supported_sizes)})" if supported_sizes else ""
                technique_info = f" [Techniques: {', '.join(techniques)}]" if techniques else ""
                template_options[f"Template {i}{size_info}{technique_info}"] = template
            
            if len(template_options) == 1:
                selected_template_key = list(template_options.keys())[0]
                selected_template = template_options[selected_template_key]
                
                template_url = selected_template.get("image_url")
                placement = selected_template.get("placement", "front")
                
                template_info = {
                    "technique": selected_template.get("technique", ""),
                    "template_width": selected_template.get("template_width", 0),
                    "template_height": selected_template.get("template_height", 0),
                    "print_area_width": selected_template.get("print_area_width", 0),
                    "print_area_height": selected_template.get("print_area_height", 0),
                    "print_area_top": selected_template.get("print_area_top", 0),
                    "print_area_left": selected_template.get("print_area_left", 0)
                }
                
                if template_url:
                    template_id = f"template_{templates.index(selected_template) + 1}"
                    template_image, image_url = download_image(
                        template_url,
                        catalog_product_id,
                        placement,
                        template_id
                    )
                    
                    if template_image:
                        st.image(template_image, caption=f"{product['name']} - {selected_template_key}")
                        
                        with st.expander("Template Information"):
                            st.json(template_info)
                        
                        if templates_vary_by_size:
                            st.info("⚠️ This product has different templates for different sizes.")
                        
                        product_template = {
                            "product_id": product_id,
                            "catalog_product_id": catalog_product_id,
                            "name": product['name'],
                            "placement": placement,
                            "template": selected_template_key,
                            "template_url": image_url,
                            "template_image": template_image,
                            "main_category_id": main_category_id,
                            "category_title": category_title,
                            "variants": variants,
                            "templates_vary_by_size": templates_vary_by_size
                        }
                        
                        product_template.update(template_info)
                        
                        all_products_templates.append(product_template)
                    else:
                        st.warning(f"No template URL found for {product['name']} with template {selected_template_key}")
            else:
                if templates_have_different_urls:
                    st.info("⚠️ This product has different templates for different variants. Processing all templates...")
                    
                    for variant in variants:
                        variant_id = variant["catalog_variant_id"]
                        variant_templates = templates_by_variant.get(variant_id, [])
                        
                        if not variant_templates:
                            continue
                        
                        variant_template = variant_templates[0]
                        template_url = variant_template.get("image_url")
                        placement = variant_template.get("placement", "front")
                        
                        template_info = {
                            "technique": variant_template.get("technique", ""),
                            "template_width": variant_template.get("template_width", 0),
                            "template_height": variant_template.get("template_height", 0),
                            "print_area_width": variant_template.get("print_area_width", 0),
                            "print_area_height": variant_template.get("print_area_height", 0),
                            "print_area_top": variant_template.get("print_area_top", 0),
                            "print_area_left": variant_template.get("print_area_left", 0)
                        }
                        
                        if template_url:
                            template_id = f"variant_{variant_id}"
                            template_image, image_url = download_image(
                                template_url,
                                catalog_product_id,
                                placement,
                                template_id
                            )
                            
                            if template_image:
                                if variants.index(variant) < 3:
                                    st.image(template_image, caption=f"{product['name']} - Size: {variant['size']} - Color: {variant['color_code']}")
                                elif variants.index(variant) == 3:
                                    st.info(f"... and {len(variants) - 3} more variants (not displayed)")
                                
                                # Format the size value to replace Unicode characters with standard ASCII
                                size_value = variant["size"]
                                # Replace inch symbol (″) with "in" and multiplication symbol (×) with "x"
                                size_value = size_value.replace('\u2033', 'in').replace('\u00d7', 'x')
                                
                                variant_template_data = {
                                    "product_id": product_id,
                                    "catalog_product_id": catalog_product_id,
                                    "name": product['name'],
                                    "placement": placement,
                                    "variant_id": variant_id,
                                    "variant_size": size_value,
                                    "variant_color": variant["color_code"],
                                    "template_url": image_url,
                                    "template_image": template_image,
                                    "main_category_id": main_category_id,
                                    "category_title": category_title,
                                    "templates_vary_by_size": templates_vary_by_size
                                }
                                
                                variant_template_data.update(template_info)
                                
                                all_products_templates.append(variant_template_data)
                else:
                    selected_template_key = st.selectbox(
                        "Select Template",
                        options=list(template_options.keys()),
                        index=0 if template_options else None,
                        key=f"template_{product_id}"
                    )
                    selected_template = template_options[selected_template_key]
                    
                    template_url = selected_template.get("image_url")
                    placement = selected_template.get("placement", "front")
                    
                    template_info = {
                        "technique": selected_template.get("technique", ""),
                        "template_width": selected_template.get("template_width", 0),
                        "template_height": selected_template.get("template_height", 0),
                        "print_area_width": selected_template.get("print_area_width", 0),
                        "print_area_height": selected_template.get("print_area_height", 0),
                        "print_area_top": selected_template.get("print_area_top", 0),
                        "print_area_left": selected_template.get("print_area_left", 0)
                    }
                    
                    if template_url:
                        template_id = f"template_{templates.index(selected_template) + 1}"
                        template_image, image_url = download_image(
                            template_url,
                            catalog_product_id,
                            placement,
                            template_id
                        )
                        
                        if template_image:
                            st.image(template_image, caption=f"{product['name']} - {selected_template_key}")
                            
                            with st.expander("Template Information"):
                                # Display template info without binary image data
                                display_info = template_info.copy()
                                st.json(display_info)
                            
                            if templates_vary_by_size:
                                st.info("⚠️ This product has different templates for different sizes.")
                            
                            product_template = {
                                "product_id": product_id,
                                "catalog_product_id": catalog_product_id,
                                "name": product['name'],
                                "placement": placement,
                                "template": selected_template_key,
                                "template_url": image_url,
                                "template_image": template_image,
                                "main_category_id": main_category_id,
                                "category_title": category_title,
                                "variants": variants,
                                "templates_vary_by_size": templates_vary_by_size
                            }
                            
                            product_template.update(template_info)
                            
                            all_products_templates.append(product_template)
                        else:
                            st.warning(f"No template URL found for {product['name']} with template {selected_template_key}")
        
        if all_products_templates:
            st.header("Step 3: Save Template Data")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            json_filename = f"templates_{timestamp}.json"

            if st.button("Save All Template Data", key="save_template_data"):
                # Generate timestamp for filenames
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                json_filename = f"templates_{timestamp}.json"
                
                # Create a ZIP file with all template data and images
                zip_href = create_zip_file(all_products_templates, file_prefix="templates")

                st.success(f"All templates data and images prepared for download")
                st.markdown(zip_href, unsafe_allow_html=True)
                
                # Display templates gallery
                st.subheader("Generated Templates Gallery")
                
                # Group templates by product name for display
                templates_by_product = {}
                for template in all_products_templates:
                    product_name = template["name"]
                    if product_name not in templates_by_product:
                        templates_by_product[product_name] = []
                    templates_by_product[product_name].append(template)
                
                # Display grouped templates
                for product_name, templates in templates_by_product.items():
                    with st.expander(f"{product_name} ({len(templates)} templates)"):
                        for i, template in enumerate(templates):
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                # Use template_image for display but not in JSON
                                if "template_image" in template:
                                    st.image(template["template_image"], width=200)
                            with col2:
                                st.write(f"**Placement:** {template.get('placement', 'N/A')}")
                                if "variant_size" in template:
                                    st.write(f"**Size:** {template.get('variant_size', 'N/A')}")
                                    st.write(f"**Color:** {template.get('variant_color', 'N/A')}")
                                st.write(f"**Print Area:** {template.get('print_area_width', 0)}x{template.get('print_area_height', 0)} px")
                                st.write(f"**Technique:** {template.get('technique', 'N/A')}")
                                
                                # Individual template download
                                template_filename = f"template_{template['catalog_product_id']}_{template['placement']}.png"
                                if "template_image" in template:
                                    st.markdown(
                                        get_download_link(template["template_image"], template_filename),
                                        unsafe_allow_html=True
                                    )
                            
                            if i < len(templates) - 1:
                                st.divider()
                
                # Display template usage instructions
                with st.expander("How to use these templates"):
                    st.markdown("""
                    ### Template Usage Instructions
                    
                    1. **Download the ZIP file** containing all templates and JSON data
                    2. **Extract the ZIP file** to access all template images and data
                    3. **Open templates in your design software** (Photoshop, GIMP, etc.)
                    4. **Create your design** within the print area
                    5. **Save as PNG or JPG** with transparency if needed
                    
                    #### Print Area Information
                    The print area is the area where your design will be printed. Make sure your design fits within this area.
                    
                    #### Template Dimensions
                    The template dimensions are the full dimensions of the template image. Your design should be positioned according to the print area coordinates.
                    
                    #### JSON Data
                    The JSON file contains all the template information, including print area dimensions and positions, which can be useful for automated design workflows.
                    """)