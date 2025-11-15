import requests
from bs4 import BeautifulSoup
import os
import re
import bleach
from database import get_db_connection
from requests.adapters import HTTPAdapter
from urllib3.util.connection import create_connection
from urllib.parse import urlparse

def sanitize_filename(filename):
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-').lower()

def download_image(img_url, save_path, pinned_ip=None):
    try:
        if pinned_ip:
            session = requests.Session()
            parsed = urlparse(img_url)
            
            original_create_connection = create_connection
            
            def patched_create_connection(address, *args, **kwargs):
                host, port = address
                if host == parsed.hostname:
                    return original_create_connection((pinned_ip, port), *args, **kwargs)
                return original_create_connection(address, *args, **kwargs)
            
            import urllib3.util.connection
            urllib3.util.connection.create_connection = patched_create_connection
            
            try:
                response = session.get(img_url, timeout=10, allow_redirects=False)
            finally:
                urllib3.util.connection.create_connection = original_create_connection
        else:
            response = requests.get(img_url, timeout=10, allow_redirects=False)
        
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error downloading image: {e}")
    return False

def scrape_tutorial(url, pinned_ip=None):
    try:
        if pinned_ip:
            session = requests.Session()
            parsed = urlparse(url)
            
            original_create_connection = create_connection
            
            def patched_create_connection(address, *args, **kwargs):
                host, port = address
                if host == parsed.hostname:
                    return original_create_connection((pinned_ip, port), *args, **kwargs)
                return original_create_connection(address, *args, **kwargs)
            
            import urllib3.util.connection
            urllib3.util.connection.create_connection = patched_create_connection
            
            try:
                response = session.get(url, timeout=15, allow_redirects=False)
            finally:
                urllib3.util.connection.create_connection = original_create_connection
        else:
            response = requests.get(url, timeout=15, allow_redirects=False)
        
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1')
        title_text = title.get_text().strip() if title else 'Untitled Tutorial'
        
        description_meta = soup.find('meta', attrs={'name': 'description'})
        description = description_meta['content'] if description_meta else ''
        
        slug = sanitize_filename(title_text)
        
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        
        if main_content:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                          'ul', 'ol', 'li', 'a', 'img', 'code', 'pre', 'blockquote', 'div', 'span']
            allowed_attrs = {'a': ['href', 'title'], 'img': ['src', 'alt', 'title']}
            
            content_html = bleach.clean(
                str(main_content),
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
        else:
            content_html = '<div><p>Content could not be extracted.</p></div>'
        
        img_tag = soup.find('img')
        image_path = None
        if img_tag and img_tag.get('src'):
            img_url = img_tag['src']
            if not img_url.startswith('http'):
                from urllib.parse import urljoin
                img_url = urljoin(url, img_url)
            
            img_filename = f"{slug}.jpg"
            save_path = os.path.join('static', 'images', 'tutorial_images', img_filename)
            
            if download_image(img_url, save_path, pinned_ip=pinned_ip):
                image_path = f'images/tutorial_images/{img_filename}'
        
        html_filename = f"{slug}.html"
        html_path = os.path.join('templates', 'tutorials', html_filename)
        
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        
        tutorial_template = f"""
{{% extends "base.html" %}}

{{% block content %}}
<div class="container my-5">
    <h1>{{{{ tutorial['title'] }}}}</h1>
    {{% if tutorial['image_path'] %}}
    <img src="{{{{ url_for('static', filename=tutorial['image_path']) }}}}" class="img-fluid mb-4" alt="{{{{ tutorial['title'] }}}}">
    {{% endif %}}
    <div class="tutorial-content">
        {content_html}
    </div>
    <a href="{{{{ url_for('index') }}}}" class="btn btn-secondary mt-4">Back to Tutorials</a>
</div>
{{% endblock %}}
"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(tutorial_template)
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tutorials (title, description, slug, image_path, html_filename) VALUES (?, ?, ?, ?, ?)',
            (title_text, description, slug, image_path, html_filename)
        )
        conn.commit()
        conn.close()
        
        print(f"Successfully scraped: {title_text}")
        return True
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return False

def scrape_multiple_tutorials(urls):
    success_count = 0
    for url in urls:
        print(f"\nScraping: {url}")
        if scrape_tutorial(url):
            success_count += 1
    
    print(f"\nCompleted! Successfully scraped {success_count}/{len(urls)} tutorials")
    return success_count

if __name__ == '__main__':
    sample_urls = [
        'https://www.hackingarticles.in/netcat-tutorials-beginner-to-advance/',
        'https://www.hackingarticles.in/network-penetration-testing/',
    ]
    
    print("Starting tutorial scraper...")
    print("This will scrape tutorials from the provided URLs.")
    print("\nNote: Make sure you have permission to scrape the target website.")
    print("For demonstration, run this script manually with specific URLs.\n")
    
    user_input = input("Enter URLs separated by commas (or press Enter to use sample URLs): ")
    
    if user_input.strip():
        urls = [url.strip() for url in user_input.split(',')]
    else:
        urls = sample_urls
    
    scrape_multiple_tutorials(urls)
