from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from database import init_db, get_db_connection
from scraper import scrape_tutorial

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

ALLOWED_DOMAINS = [
    'hackingarticles.in',
    'www.hackingarticles.in',
    'cybersecuritynews.com',
    'www.cybersecuritynews.com',
    'hackthebox.com',
    'www.hackthebox.com',
    'tryhackme.com',
    'www.tryhackme.com',
]

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    tutorials = conn.execute('SELECT * FROM tutorials ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', tutorials=tutorials)

@app.route('/tutorial/<slug>')
def tutorial(slug):
    conn = get_db_connection()
    tutorial = conn.execute('SELECT * FROM tutorials WHERE slug = ?', (slug,)).fetchone()
    conn.close()
    
    if tutorial is None:
        flash('Tutorial not found', 'error')
        return redirect(url_for('index'))
    
    tutorial_html_path = os.path.join('templates', 'tutorials', tutorial['html_filename'])
    
    if not os.path.exists(tutorial_html_path):
        flash('Tutorial content not found', 'error')
        return redirect(url_for('index'))
    
    return render_template(f'tutorials/{tutorial["html_filename"]}', tutorial=tutorial)

@app.route('/secret-admin-panel')
def admin():
    conn = get_db_connection()
    tutorials = conn.execute('SELECT * FROM tutorials ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin.html', tutorials=tutorials)

@app.route('/edit/<int:tutorial_id>', methods=['GET', 'POST'])
def edit(tutorial_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        conn.execute('UPDATE tutorials SET title = ?, description = ? WHERE id = ?',
                    (title, description, tutorial_id))
        conn.commit()
        conn.close()
        
        flash('Tutorial updated successfully!', 'success')
        return redirect(url_for('admin'))
    
    tutorial = conn.execute('SELECT * FROM tutorials WHERE id = ?', (tutorial_id,)).fetchone()
    conn.close()
    
    if tutorial is None:
        flash('Tutorial not found', 'error')
        return redirect(url_for('admin'))
    
    return render_template('edit.html', tutorial=tutorial)

@app.route('/delete/<int:tutorial_id>', methods=['POST'])
def delete(tutorial_id):
    conn = get_db_connection()
    tutorial = conn.execute('SELECT * FROM tutorials WHERE id = ?', (tutorial_id,)).fetchone()
    
    if tutorial:
        html_file_path = os.path.join('templates', 'tutorials', tutorial['html_filename'])
        if os.path.exists(html_file_path):
            os.remove(html_file_path)
        
        if tutorial['image_path']:
            full_image_path = os.path.join('static', tutorial['image_path'])
            if os.path.exists(full_image_path):
                os.remove(full_image_path)
        
        conn.execute('DELETE FROM tutorials WHERE id = ?', (tutorial_id,))
        conn.commit()
        flash('Tutorial deleted successfully!', 'success')
    else:
        flash('Tutorial not found', 'error')
    
    conn.close()
    return redirect(url_for('admin'))

@app.route('/scrape', methods=['POST'])
def scrape_url():
    url = request.form.get('url')
    
    if not url:
        flash('Please provide a URL', 'error')
        return redirect(url_for('admin'))
    
    from urllib.parse import urlparse
    import socket
    import ipaddress
    
    try:
        parsed_url = urlparse(url)
        
        if parsed_url.scheme not in ['http', 'https']:
            flash('Invalid URL scheme. Only HTTP and HTTPS URLs are allowed.', 'error')
            return redirect(url_for('admin'))
        
        hostname = parsed_url.hostname
        if not hostname:
            flash('Invalid URL format.', 'error')
            return redirect(url_for('admin'))
        
        if hostname.lower() not in ALLOWED_DOMAINS:
            flash(f'Domain not allowed. Allowed domains: {", ".join(ALLOWED_DOMAINS)}', 'error')
            return redirect(url_for('admin'))
        
        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            flash('Could not resolve hostname. Please check the URL.', 'error')
            return redirect(url_for('admin'))
        
        validated_ip = None
        for addr in addr_info:
            ip_str = addr[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                    flash('Cannot scrape from private, loopback, or reserved IP addresses.', 'error')
                    return redirect(url_for('admin'))
                if validated_ip is None and ip.version == 4:
                    validated_ip = ip_str
            except ValueError:
                flash('Invalid IP address resolved from hostname.', 'error')
                return redirect(url_for('admin'))
        
        if not validated_ip:
            flash('No valid IPv4 address found for hostname.', 'error')
            return redirect(url_for('admin'))
        
        success = scrape_tutorial(url, pinned_ip=validated_ip)
        if success:
            flash(f'Tutorial scraped successfully from {url}!', 'success')
        else:
            flash(f'Failed to scrape tutorial from {url}. It may already exist or the content could not be extracted. Check the console for details.', 'error')
    except Exception as e:
        flash(f'Error scraping tutorial: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

@app.route('/add-manual', methods=['POST'])
def add_manual():
    import re
    from werkzeug.utils import secure_filename
    
    title = request.form.get('title')
    description = request.form.get('description')
    content = request.form.get('content')
    
    if not title or not description or not content:
        flash('All fields except image are required', 'error')
        return redirect(url_for('admin'))
    
    try:
        # Generate slug from title
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Check if slug already exists
        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM tutorials WHERE slug = ?', (slug,)).fetchone()
        if existing:
            conn.close()
            flash(f'A tutorial with similar title already exists', 'error')
            return redirect(url_for('admin'))
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(f"{slug}.{file.filename.rsplit('.', 1)[1].lower()}")
                save_path = os.path.join('static', 'images', 'tutorial_images', filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
                image_path = f'images/tutorial_images/{filename}'
        
        # Create HTML file
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
        {content}
    </div>
    <a href="{{{{ url_for('index') }}}}" class="btn btn-secondary mt-4">Back to Tutorials</a>
</div>
{{% endblock %}}
"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(tutorial_template)
        
        # Insert into database
        conn.execute(
            'INSERT INTO tutorials (title, description, slug, image_path, html_filename) VALUES (?, ?, ?, ?, ?)',
            (title, description, slug, image_path, html_filename)
        )
        conn.commit()
        conn.close()
        
        flash(f'Tutorial "{title}" added successfully!', 'success')
        
    except Exception as e:
        flash(f'Error adding tutorial: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
