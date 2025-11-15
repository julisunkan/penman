from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
