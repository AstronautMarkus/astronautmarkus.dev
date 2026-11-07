# astronautmarkus.dev - 2026 Branch

Personal website of Marcos Reyes (AstronautMarkus). This README documents the **2026 Branch**: the version of the site built during 2026 (first commit on 2026-02-19). If the site is rebuilt from scratch in the future, this branch stays as the record of what the 2026 version was and how it worked.

## What this version is

A retro-styled personal website (90s / early 2000s look, pixel icons, 88x31 buttons, CRT effects) backed by a Flask application with its own admin panel. It is bilingual (English and Spanish) and runs on a single Linux server behind a reverse proxy.

## Stack

- Python 3, Flask, Jinja2
- SQLAlchemy + Flask-Migrate (Alembic), MySQL / MariaDB (PyMySQL)
- Flask-Login for admin authentication
- Flask-Mail for contact notifications and autoresponses
- Gunicorn, run as a systemd service
- Cron for hourly external data sync
- Storage driver: local disk or S3-compatible (boto3)
- Static images served from AWS CloudFront
- Cloudflare Turnstile for anti-spam
- Google Gemini for AI suggestions in the admin
- RenderCV / Typst for CV generation, ReportLab for PDF reports
- Plain HTML, CSS and JavaScript on the frontend (no frontend framework)

## Features

Public site:

- Home with welcome card, bio, SDLC stages, metrics card, latest posts and visitor counter
- About page with tech stack, system properties and OS journey
- Blog with categories, tags, slugs, view counts, code copy buttons and RSS feed
- Portfolio with project details, tech stack, status, role, featured projects and Markdown content
- Gallery with lightbox, Setup and Homelab pages
- YouTube videos page, synced from the channel RSS feed
- GitHub stats, synced via the GitHub API
- Guestbook with anti-spam measures
- Contact form with Turnstile, blocked senders and a kill switch
- MySpace-style profile page
- Proyectadas (personal reflections), Beercat project page
- Extras: PDF generator, embeddable SVG widget cards
- Themes: default, Mac OS X, Cyberpunk, Gensokyo and Windows 95, with a theme picker and a weekly theme calendar that rotates automatically
- Localized 404 / 500 pages, SEO meta tags, Open Graph, sitemap and robots.txt

Admin panel:

- Dashboard, visit tracking
- Management for blog posts and categories, portfolio projects, gallery, guestbook, proyectadas and CVs
- Contact inbox with bulk delete
- CV builder that generates RenderCV YAML and renders it to PDF
- AI-generated blog excerpt and tag suggestions (Gemini)
- Database backups: generate, list, download and delete
- Honeypot: decoy routes that log hits and notify the admin

## Project structure

```
website/
  main.py              App entry point (Flask dev server / Gunicorn)
  requirements.txt
  .env.example         All configuration variables
  app/
    config/            Configuration loaded from environment
    models/            SQLAlchemy models
    routes/            Blueprints: main, admin, auth, contact, extras, kanarianlintu (honeypot), utils
    services/          AI, backups, GitHub, YouTube, RenderCV, feeds
    storage/           Local and S3 storage drivers
    middleware/        Visit tracking
    templates/         Jinja2 templates (English and Spanish)
    static/            CSS, themes, JS, images, icons
    scripts/           Database setup, sync, data export, user creation, tests
cron/                  Hourly sync job (YouTube, GitHub)
systemd/               Gunicorn service unit
```

## Running locally

```
cd website
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in the values
python app/scripts/create_db.py
python app/scripts/data/create_user.py
python main.py              # http://127.0.0.1:5001
```

## Deployment

- The app lives in `/var/www/astronautmarkus.dev` and runs with Gunicorn on `127.0.0.1:5016` through [systemd/astronautmarkus_daemon.service](systemd/astronautmarkus_daemon.service).
- External data is synced every hour by [cron/astronautmarkus_sync](cron/astronautmarkus_sync), which runs `app/scripts/sync.py`.
- A reverse proxy sits in front of Gunicorn (ProxyFix is configured for two proxy hops).

### CloudFront assets

Heavy page assets (images for home, about, setup, homelab, theme banners and email banners) are served from an AWS CloudFront distribution instead of the Flask server.

- The CDN mirrors the `static/` folder with the same relative paths, e.g. `static/images/banner.png` lives at `https://dxxxx.cloudfront.net/images/banner.png`.
- Templates use the `cdn_url('images/...')` helper ([app/utils.py](website/app/utils.py)). When `CDN_URL` is set in `.env`, it returns the CloudFront URL; when it is empty, it falls back to the local `/static` path, so development works without the CDN.
- New assets must be uploaded to the CloudFront origin with the same path they have in `static/`, otherwise they will 404 in production.

## License

This project is licensed under the DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE (WTFPL), Version 2. See the [LICENSE](LICENSE) file for details.
