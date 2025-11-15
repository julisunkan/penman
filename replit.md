# Network Penetration Guides & Tools

## Overview
A Progressive Web App (PWA) built with Flask for browsing network penetration testing tutorials. The app features offline support, a responsive design, and an admin panel for content management.

## Recent Changes (November 15, 2025)
- Initial project setup with complete Flask PWA implementation
- Created SQLite database schema for tutorial storage
- Implemented web scraper for extracting tutorial content from external sources
- Built responsive UI with Bootstrap and custom CSS
- Added PWA functionality with service worker and manifest
- Configured Flask workflow on port 5000

## Project Architecture

### Backend (Flask)
- **app.py**: Main Flask application with routes for:
  - `/` - Home page displaying tutorial cards
  - `/tutorial/<slug>` - Individual tutorial pages
  - `/secret-admin-panel` - Hidden admin panel for management
  - `/edit/<id>` - Edit tutorial metadata
  - `/delete/<id>` - Delete tutorials
- **database.py**: SQLite database initialization and connection management
- **scraper.py**: Web scraping functionality using BeautifulSoup

### Database Schema
SQLite database (`data/tutorials.db`) with tutorials table:
- id (PRIMARY KEY)
- title (TEXT)
- description (TEXT)
- slug (TEXT UNIQUE)
- image_path (TEXT)
- html_filename (TEXT)
- created_at (TIMESTAMP)

### Frontend Structure
- **Templates**: Jinja2 templates in `templates/` directory
  - base.html - Base template with navbar and footer
  - index.html - Tutorial listing page
  - admin.html - Admin management interface
  - edit.html - Tutorial editing form
  - tutorials/ - Individual tutorial HTML files
- **Static Assets**:
  - CSS: Custom styling in `static/css/style.css`
  - JS: Service worker in `static/js/service-worker.js`
  - Images: Icons and tutorial images in `static/images/`
  - PWA: manifest.json for app installation

### PWA Features
- Service worker for offline caching
- Web app manifest for mobile installation
- Responsive design for all devices
- Cache-first strategy for static assets

## How to Use

### Running the App
The Flask app runs automatically on port 5000. Access it through the web view.

### Adding Tutorials
1. Run the scraper: `python scraper.py`
2. Enter tutorial URLs when prompted
3. The scraper will download content, images, and save to database

### Admin Panel
- Access at `/secret-admin-panel`
- Edit tutorial titles and descriptions
- Delete tutorials (removes HTML files and images)

## Dependencies
- Flask >= 3.0.0
- requests >= 2.28.1
- beautifulsoup4 >= 4.11.1
- trafilatura

## User Preferences
None specified yet.

## Security Notes
- Admin panel uses a hidden route (no authentication by design)
- Session secret stored in environment variable SESSION_SECRET
- All user inputs sanitized for database queries

## Future Enhancements
- Add user authentication for admin panel
- Implement search and filtering
- Add tutorial categories and tags
- Create tutorial bookmark functionality
- Automated scraper scheduling
