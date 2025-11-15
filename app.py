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
            flash(f'Failed to scrape tutorial from {url}. Please check the URL and try again.', 'error')
    except Exception as e:
        flash(f'Error scraping tutorial: {str(e)}', 'error')
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
