import requests
import time
import streamlit as st
import base64
import io
from typing import Dict, List, Any, Optional, Tuple

class PrintfulAPI:
    """Printful API client for interacting with the Printful API"""
    
    def __init__(self, api_key: str, base_url: str):
        """Initialize the Printful API client
        
        Args:
            api_key: Printful API key
            base_url: Printful API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        } if api_key else {"Content-Type": "application/json"}
        
        # Initialize cache if not already in session state
        if 'api_cache' not in st.session_state:
            st.session_state.api_cache = {}
        if 'store_products' not in st.session_state:
            st.session_state.store_products = []
        if 'product_variants_cache' not in st.session_state:
            st.session_state.product_variants_cache = {}
        if 'template_data_cache' not in st.session_state:
            st.session_state.template_data_cache = {}
        if 'mockup_styles_cache' not in st.session_state:
            st.session_state.mockup_styles_cache = {}
        if 'mockup_images_cache' not in st.session_state:
            st.session_state.mockup_images_cache = {}
    
    def validate_api_key(self) -> bool:
        """Validate the API key by making a test request
        
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        if not self.api_key:
            return False
            
        test_url = f"{self.base_url}/store/products"
        try:
            response = requests.get(test_url, headers=self.headers)
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                st.error("Invalid API key. Please check your API key and try again.")
                return False
            else:
                st.warning(f"API connection issue: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            st.error(f"Connection error: {e}")
            return False
    
    def make_request(self, endpoint: str, params: Optional[Dict] = None, force_refresh: bool = False) -> Optional[Dict]:
        """Make a request to the Printful API with caching and rate limiting
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            force_refresh: Force refresh data from API instead of using cache
            
        Returns:
            Optional[Dict]: API response or None if the request failed
        """
        url = f"{self.base_url}{endpoint}"
        cache_key = f"{endpoint}_{str(params)}"
        
        # Return cached result if available and not forcing refresh
        if not force_refresh and cache_key in st.session_state.api_cache:
            return st.session_state.api_cache[cache_key]
        
        try:
            with st.spinner(f"Making request to {endpoint}..."):
                response = requests.get(url, headers=self.headers, params=params)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
                if response.status_code == 200:
                    result = response.json()
                    # Cache the result
                    st.session_state.api_cache[cache_key] = result
                    return result
                elif response.status_code == 429:
                    st.warning("Rate limit exceeded. Waiting 5 seconds before retrying...")
                    time.sleep(5)
                    return self.make_request(endpoint, params)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            st.error(f"Request error: {e}")
            return None
    
    def fetch_store_products(self, force_refresh: bool = False) -> List[Dict]:
        """Fetch all products from the store and their catalog product IDs with caching
        
        Args:
            force_refresh: Force refresh data from API instead of using cache
            
        Returns:
            List[Dict]: List of products
        """
        if not force_refresh and st.session_state.store_products:
            return st.session_state.store_products
        
        products_data = self.make_request("/store/products")
        if not products_data or "result" not in products_data:
            st.error("Failed to fetch products from your store")
            return []
        
        products = []
        for product in products_data["result"]:
            product_id = product["id"]
            
            product_details = self.make_request(f"/store/products/{product_id}")
            
            if product_details and "result" in product_details and "sync_variants" in product_details["result"]:
                if product_details["result"]["sync_variants"]:
                    catalog_product_id = product_details["result"]["sync_variants"][0]["product"]["product_id"]
                    
                    products.append({
                        "id": product_id,
                        "name": product["name"],
                        "catalog_product_id": catalog_product_id
                    })
                else:
                    products.append({
                        "id": product_id,
                        "name": product["name"]
                    })
            else:
                products.append({
                    "id": product_id,
                    "name": product["name"]
                })
        
        st.session_state.store_products = products
        
        return products
    
    def get_product_variants(self, product_id: str, force_refresh: bool = False) -> Tuple[List[Dict], str, str]:
        """Fetch all variants for a specific product from the store with caching
        
        Args:
            product_id: Product ID
            force_refresh: Force refresh data from API instead of using cache
            
        Returns:
            Tuple[List[Dict], str, str]: Tuple of (variants, main_category_id, category_title)
        """
        if not force_refresh and product_id in st.session_state.product_variants_cache:
            return st.session_state.product_variants_cache[product_id]
        
        product_details = self.make_request(f"/store/products/{product_id}")
        
        variants = []
        main_category_id = ""
        category_title = ""
        
        if product_details and "result" in product_details and "sync_variants" in product_details["result"]:
            for variant in product_details["result"]["sync_variants"]:
                variant_id = variant["id"]
                catalog_variant_id = variant["product"]["variant_id"]
                
                variant_details = self.make_request(f"/products/variant/{catalog_variant_id}")
                
                size = ""
                color_code = ""
                in_stock = False
                
                if variant_details and "result" in variant_details:
                    size = variant_details["result"]["variant"].get("size", "")
                    color_code = variant_details["result"]["variant"].get("color_code", "")
                    in_stock = variant_details["result"]["variant"].get("in_stock", False)
                    
                    if not main_category_id:
                        main_category_id = variant_details["result"]["product"].get("main_category_id", "")
                        category_title = variant_details["result"]["product"].get("type", "")
                
                variants.append({
                    "catalog_variant_id": catalog_variant_id,
                    "size": size,
                    "color_code": color_code,
                    "in_stock": in_stock
                })
        
        result = (variants, main_category_id, category_title)
        st.session_state.product_variants_cache[product_id] = result
        
        return result
    
    def get_catalog_variant_templates(self, catalog_product_id: str, catalog_variant_ids: List[str]) -> Dict:
        """Get templates for specific catalog variants with caching
        
        Args:
            catalog_product_id: Catalog product ID
            catalog_variant_ids: List of catalog variant IDs
            
        Returns:
            Dict: Template data
        """
        cache_key = f"{catalog_product_id}_{catalog_variant_ids}"
        
        if cache_key in st.session_state.template_data_cache:
            return st.session_state.template_data_cache[cache_key]
        
        if not isinstance(catalog_variant_ids, list):
            catalog_variant_ids = catalog_variant_ids.split(",")
            catalog_variant_ids = [int(id.strip()) for id in catalog_variant_ids]
        
        result = {"data": []}
        template_dict = {}
        
        offset = 0
        limit = 100
        has_more = True
        
        while has_more:
            endpoint = f"/v2/catalog-products/{catalog_product_id}/mockup-templates?limit={limit}&offset={offset}"
            page_result = self.make_request(endpoint)
            
            if not page_result or "data" not in page_result:
                break
            
            for template in page_result["data"]:
                template_variant_ids = template.get('catalog_variant_ids', [])
                image_url = template.get('image_url', '')
                
                if any(variant_id in template_variant_ids for variant_id in catalog_variant_ids):
                    if image_url not in template_dict:
                        template_dict[image_url] = template
                        result["data"].append(template)
            
            if len(page_result["data"]) < limit:
                has_more = False
            else:
                offset += limit
        
        if result:
            st.session_state.template_data_cache[cache_key] = result
        
        return result
    
    def get_mockup_styles(self, catalog_product_id: str, force_refresh: bool = False) -> Tuple[Dict, Optional[int], Optional[int], Optional[int], Optional[str], Optional[str]]:
        """Get mockup styles for a catalog product with caching
        
        Args:
            catalog_product_id: Catalog product ID
            force_refresh: Force refresh data from API instead of using cache
            
        Returns:
            Tuple[Dict, Optional[int], Optional[int], Optional[int], Optional[str], Optional[str]]: 
            Tuple of (mockup_styles, print_area_width, print_area_height, dpi, print_area_type, technique)
        """
        cache_key = f"mockup_styles_{catalog_product_id}"
        
        if not force_refresh and cache_key in st.session_state.mockup_styles_cache:
            return st.session_state.mockup_styles_cache[cache_key]
        
        result = {"data": []}
        
        print_area_width = None
        print_area_height = None
        dpi = None
        print_area_type = None
        technique = None
        
        offset = 0
        limit = 100
        has_more = True
        
        while has_more:
            endpoint = f"/v2/catalog-products/{catalog_product_id}/mockup-styles?limit={limit}&offset={offset}"
            page_result = self.make_request(endpoint)
            
            if not page_result or "data" not in page_result:
                break
            
            result["data"].extend(page_result["data"])
            extracted = False
            
            if page_result["data"] and extracted == False:
                first_style = page_result["data"][0]
                print_area_width = first_style.get('print_area_width')
                print_area_height = first_style.get('print_area_height')
                dpi = first_style.get('dpi')
                print_area_type = first_style.get('print_area_type')
                technique = first_style.get('technique')
                extracted = True
            
            if len(page_result["data"]) < limit:
                has_more = False
            else:
                offset += limit
        
        if result and result["data"]:
            st.session_state.mockup_styles_cache[cache_key] = result, print_area_width, print_area_height, dpi, print_area_type, technique
        
        return result, print_area_width, print_area_height, dpi, print_area_type, technique
    
    def get_mockup_images(self, catalog_product_id: str, mockup_style_id: str, force_refresh: bool = False) -> Dict:
        """Get mockup images for a specific mockup style with caching
        
        Args:
            catalog_product_id: Catalog product ID
            mockup_style_id: Mockup style ID
            force_refresh: Force refresh data from API instead of using cache
            
        Returns:
            Dict: Mockup images data
        """
        cache_key = f"mockup_images_{catalog_product_id}_{mockup_style_id}"
        
        if not force_refresh and cache_key in st.session_state.mockup_images_cache:
            return st.session_state.mockup_images_cache[cache_key]
        
        result = {"data": []}
        
        offset = 0
        limit = 20
        has_more = True
        
        while has_more:
            endpoint = f"/v2/catalog-products/{catalog_product_id}/images?mockup_style_ids={mockup_style_id}&limit={limit}&offset={offset}"
            page_result = self.make_request(endpoint)
            
            if not page_result or "data" not in page_result:
                break
            
            result["data"].extend(page_result["data"])
            
            if len(page_result["data"]) < limit:
                has_more = False
            else:
                offset += limit
        
        if result and result["data"]:
            st.session_state.mockup_images_cache[cache_key] = result
        
        return result
    
    def make_post_request(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make a POST request to the Printful API
        
        Args:
            endpoint: API endpoint
            data: POST data
            
        Returns:
            Optional[Dict]: API response or None if the request failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with st.spinner(f"Making POST request to {endpoint}..."):
                headers = self.headers.copy()
                headers["Content-Type"] = "application/json"
                
                response = requests.post(url, headers=headers, json=data)
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 429:
                    st.warning("Rate limit exceeded. Waiting 5 seconds before retrying...")
                    time.sleep(5)
                    return self.make_post_request(endpoint, data)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            st.error(f"Request error: {e}")
            return None
    
    def upload_file(self, file_data: bytes) -> Optional[Dict]:
        """Upload a file to the Printful API
        
        Args:
            file_data: File data as bytes
            
        Returns:
            Optional[Dict]: API response with file ID or None if the upload failed
        """
        endpoint = "/files"
        url = f"{self.base_url}{endpoint}"
        
        try:
            with st.spinner("Uploading file to Printful..."):
                # Encode file data as base64
                file_content_b64 = base64.b64encode(file_data).decode('utf-8')
                
                # Prepare data for file upload
                data = {
                    "file": file_content_b64
                }
                
                headers = self.headers.copy()
                headers["Content-Type"] = "application/json"
                
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return result
                elif response.status_code == 429:
                    st.warning("Rate limit exceeded. Waiting 5 seconds before retrying...")
                    time.sleep(5)
                    return self.upload_file(file_data)
                else:
                    st.error(f"Error uploading file: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            st.error(f"File upload error: {e}")
            return None
    
    def generate_mockup(self, product_id: str, variant_id: str, placement: str, uploaded_file_id: str) -> Optional[Dict]:
        """Generate a mockup using an uploaded file
        
        Args:
            product_id: Product ID
            variant_id: Variant ID
            placement: Placement (e.g., 'front', 'back')
            uploaded_file_id: ID of the uploaded file
            
        Returns:
            Optional[Dict]: Mockup generation result or None if generation failed
        """
        # Initialize generated_mockups_cache if not already in session state
        if 'generated_mockups_cache' not in st.session_state:
            st.session_state.generated_mockups_cache = {}
            
        cache_key = f"mockup_{product_id}_{variant_id}_{placement}_{uploaded_file_id}"
        
        # Check if mockup is already in cache
        if cache_key in st.session_state.generated_mockups_cache:
            return st.session_state.generated_mockups_cache[cache_key]
        
        endpoint = "/mockup-generator/create-task"
        
        # Prepare data for mockup generation
        data = {
            "variant_ids": [int(variant_id)],
            "format": "png",
            "files": [
                {
                    "placement": placement,
                    "image_url": f"https://api.printful.com/files/{uploaded_file_id}"
                }
            ]
        }
        
        # Create mockup generation task
        task_result = self.make_post_request(endpoint, data)
        
        if not task_result or "result" not in task_result:
            return None
        
        task_key = task_result["result"]["task_key"]
        
        # Poll for task completion
        max_attempts = 30
        attempts = 0
        
        with st.spinner("Generating mockup... This may take a moment."):
            while attempts < max_attempts:
                status_endpoint = f"/mockup-generator/task?task_key={task_key}"
                status_result = self.make_request(status_endpoint)
                
                if not status_result or "result" not in status_result:
                    attempts += 1
                    time.sleep(2)
                    continue
                
                status = status_result["result"]["status"]
                
                if status == "completed":
                    # Cache the result
                    st.session_state.generated_mockups_cache[cache_key] = status_result
                    return status_result
                elif status == "failed":
                    st.error("Mockup generation failed")
                    return None
                
                attempts += 1
                time.sleep(2)
            
            st.error("Mockup generation timed out")
            return None
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        st.session_state.api_cache = {}
        st.session_state.product_variants_cache = {}
        st.session_state.template_data_cache = {}
        st.session_state.mockup_styles_cache = {}
        st.session_state.mockup_images_cache = {}
        if 'generated_mockups_cache' in st.session_state:
            st.session_state.generated_mockups_cache = {}
        st.success("Cache cleared successfully!")