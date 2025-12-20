import json
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Configuration
MANIFEST_PATH = Path("public/monkey_manifest.json")
OUTPUT_FILE = Path("public/sitemap.xml")
BASE_URL = "https://monkeyhub.icu"


def encode_url_path(path: str) -> str:
    """
    URL-encode a path for use in sitemap, encoding non-ASCII characters
    while preserving path structure (slashes).
    
    Example: /imgs_monkey/000032_为猴着迷.webp 
          -> /imgs_monkey/000032_%E4%B8%BA%E7%8C%B4%E7%9D%80%E8%BF%B7.webp
    """
    # Split path into segments, encode each segment, then rejoin
    segments = path.split('/')
    encoded_segments = [quote(segment, safe='') for segment in segments]
    return '/'.join(encoded_segments)

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    # Ensure encoding is specified in the declaration
    return reparsed.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")

def generate_sitemap():
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest file {MANIFEST_PATH} does not exist.")
        return

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            images = json.load(f)
    except Exception as e:
        print(f"Error reading manifest: {e}")
        return

    # XML Namespaces
    urlset = ET.Element('urlset')
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    urlset.set("xmlns:image", "http://www.google.com/schemas/sitemap-image/1.1")

    # Single URL entry for the main page
    url_element = ET.SubElement(urlset, "url")
    
    # Location
    loc = ET.SubElement(url_element, "loc")
    loc.text = f"{BASE_URL}/"
    
    # Last Modified (now)
    lastmod = ET.SubElement(url_element, "lastmod")
    lastmod.text = datetime.now().strftime("%Y-%m-%d")

    # Change Frequency
    changefreq = ET.SubElement(url_element, "changefreq")
    changefreq.text = "daily"

    # Priority
    priority = ET.SubElement(url_element, "priority")
    priority.text = "1.0"

    print(f"Found {len(images)} images to index.")

    # Add images to the url entry
    # Note: Google Sitemap limit is 1000 images per URL. 
    # If we exceed this, we'd need to paginate URLs.
    count = 0
    for img in images:
        if count >= 1000:
            print("Warning: Reached 1000 image limit per URL. Truncating.")
            break
            
        image_element = ET.SubElement(url_element, "image:image")
        
        image_loc = ET.SubElement(image_element, "image:loc")
        # Ensure the URL is absolute and properly URL-encoded
        encoded_path = encode_url_path(img['monkey_url'])
        image_loc.text = f"{BASE_URL}{encoded_path}"
        
        # Optional: Title (using original name or id)
        if 'original_name' in img:
            image_title = ET.SubElement(image_element, "image:title")
            image_title.text = Path(img['original_name']).stem

        count += 1

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(prettify(urlset))

    print(f"Sitemap generated successfully at {OUTPUT_FILE}")
    print(f"Total images included: {count}")

if __name__ == "__main__":
    generate_sitemap()
