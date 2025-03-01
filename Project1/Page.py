# language: Python
import os
import re
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Directory to store generated markdown files
OUTPUT_DIR = "WWW1"
PAGES_DIR = os.path.join(OUTPUT_DIR, "pages")

# Ensure output directories exist
os.makedirs(PAGES_DIR, exist_ok=True)

# URL to scrape for character info
url = "https://kenjosabers.com/blogs/news/top-15-most-popular-star-wars-characters-icons-from-a-galaxy-far-far-away"
response = requests.get(url)
response.raise_for_status()

# Parse page content to extract all <strong> items matching "\#\d+:" pattern
soup = BeautifulSoup(response.text, "html.parser")
elements = soup.find_all("strong", string=re.compile(r"#\d+:"))
if not elements:
    print("No characters found.")
    exit()

# Prepare list to store character info (each with name, additional info, image URL and image source)
characters = []
for element in elements:
    char_text = element.get_text(strip=True)
    character_name = char_text.replace(":", "").strip()
    # Remove number from character name for search query
    search_name = re.sub(r"^\#\d+\s*", "", character_name).strip()
    additional_info = "No additional info found."
    additional_info_source = ""
    image_url = ""
    image_source = ""
    with DDGS() as ddgs:
        text_results = ddgs.text("fandom information " + search_name, max_results=1)
        image_results = ddgs.images(search_name, max_results=1)
    if text_results and len(text_results) > 0:
        additional_info = ""
        full_text = ""
        for result in text_results:
            full_text += result.get("body", result.get("title")) + "\n\n"
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", full_text)
        if sentences:
            additional_info = sentences[0]
            for i in range(1, len(sentences)):
                if len(additional_info) + len(sentences[i]) < 300:
                    additional_info += " " + sentences[i]
                else:
                    break
        additional_info_source = text_results[0].get("href") if text_results else ""
    if image_results and len(image_results) > 0:
        image_url = image_results[0].get("image", "")
        image_source = image_results[0].get("image") if image_results else ""
    characters.append({
        "name": character_name,
        "info": additional_info,
        "info_src": additional_info_source,
        "img": image_url,
        "img_src": image_source
    })

# Get Star Wars introduction from Wikipedia
wiki_intro = "No introduction found."
try:
    wiki_response = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/Star_Wars")
    wiki_response.raise_for_status()
    wiki_data = wiki_response.json()
    if "extract" in wiki_data:
        wiki_intro = wiki_data["extract"]
except Exception as e:
    print("Error fetching Wikipedia introduction:", e)

# Build the main index markdown file with introduction and list of characters
index_md = "## Star Wars Introduction\n\n"
index_md += f"{wiki_intro}\n\n"
index_md += "## Some of Star Wars characters\n\n"
for char in characters:
    file_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", re.sub(r"^\#\d+\s*", "", char["name"])) + ".md"
    index_md += f"- [{char['name']}](pages/{file_name})\n"

with open(os.path.join(OUTPUT_DIR, "Project1-Web.md"), "w", encoding="utf-8") as f:
    f.write(index_md)

# Create separate markdown subpages for each scraped character with 2 columns layout
for char in characters:
    file_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", re.sub(r"^\#\d+\s*", "", char["name"])) + ".md"
    md_content = f"# {char['name']}\n\n"
    # Create the HTML flex container with two sections:
    # Left side for info and right side for image (if available)
    img_section = ""
    if char["img"]:
        img_section = (
            f'<img src="{char["img"]}" alt="{char["name"]}" '
            f'style="max-height: 275px; max-width: 100%; min-height: 175px;"/>'
            f'<br><br>Source: <a href="{char["img_src"]}" style="word-break: break-all;">{char["img_src"]}</a>'
        )
    md_content += (
        '<div style="display: flex;">\n'
        '  <div style="flex: 1; padding-right: 10px;">\n'
        '    <strong>Short Introduction:</strong>\n'
        f'    <p>{char["info"]}</p>\n'
        f'    Source and additional information about character: <a href="{char["info_src"]}">{char["info_src"]}</a>\n'
        '  </div>\n'
        '  <div style="flex: 1; text-align: right;">\n'
        f'    {img_section}\n'
        '  </div>\n'
        '</div>\n'
    )
    with open(os.path.join(PAGES_DIR, file_name), "w", encoding="utf-8") as f:
        f.write(md_content)

print("Static Markdown site generated in the 'site' directory.")