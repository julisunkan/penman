# Network Penetration Guides & Tools

A Progressive Web App (PWA) for browsing network penetration testing tutorials with offline support.

## Features

- **Tutorial Browsing**: View network penetration testing tutorials in a clean, card-based interface
- **Web Scraper**: Automatically extract tutorials from external sources
- **Admin Panel**: Manage tutorials without login (edit titles/descriptions, delete content)
- **Progressive Web App**: Install on mobile devices and browse offline
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Offline Support**: Service worker caches content for offline access

## Getting Started

### Running the App

The Flask app runs automatically on port 5000. Click the webview to access the application.

### Adding Tutorials

To add tutorials from external sources:

```bash
python scraper.py
```

The scraper will prompt you to enter URLs. You can:
- Press Enter to use sample URLs
- Enter your own URLs separated by commas

The scraper will:
- Extract tutorial content and metadata
- Download and save images
- Sanitize HTML to prevent security issues
- Save everything to the database

### Admin Panel

Access the admin panel at: `/secret-admin-panel`

Features:
- View all tutorials in a table
- Edit tutorial titles and descriptions
- Delete tutorials (removes HTML files and images)

**Note**: The admin panel has no authentication by design, as specified in the project requirements.

## Project Structure

```
├── app.py                 # Main Flask application
├── database.py            # Database initialization and connection
├── scraper.py             # Web scraping functionality
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template with navbar
│   ├── index.html        # Tutorial listing page
│   ├── admin.html        # Admin panel
│   ├── edit.html         # Edit form
│   └── tutorials/        # Individual tutorial HTML files
├── static/
│   ├── css/
│   │   └── style.css     # Custom styling
│   ├── js/
│   │   └── service-worker.js  # PWA service worker
│   ├── images/
│   │   ├── icons/        # PWA icons
│   │   └── tutorial_images/   # Tutorial images
│   └── manifest.json     # PWA manifest
└── data/
    └── tutorials.db      # SQLite database
```

## Technology Stack

- **Backend**: Flask 3.x
- **Database**: SQLite3
- **Scraping**: BeautifulSoup4, Requests
- **Security**: Bleach (HTML sanitization)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **PWA**: Service Worker, Web App Manifest

## Security

- Admin panel uses hidden route (no authentication by design)
- Session secret stored in environment variable `SESSION_SECRET`
- HTML content sanitized using Bleach to prevent XSS attacks
- Database queries use parameterized statements to prevent SQL injection

## Future Enhancements

- Add user authentication for admin panel
- Implement search and filtering
- Add tutorial categories and tags
- Create bookmark functionality
- Automated scraper scheduling
- Add unit and integration tests

## License

Educational purposes only.
