# yt-dlp Manager

[Quick Start](#quick-start) • [Features](#features) • [How to Use](#how-to-use) • [Cookies](#cookies) • [Scheduler](#scheduler) • [Docker](#docker)

---

A powerful web-based download manager for YouTube, Vimeo, and thousands of other video sites.

## Features

- **Multi-User Support** - Create accounts for family or team members
- **Organized Downloads** - Organize downloads by folders with custom configurations
- **Scheduled Downloads** - Set up automatic download schedules
- **Real-time Progress** - Watch download progress live in your browser
- **Automatic Retries** - Handles connection issues gracefully
- **Subtitle Support** - Download subtitles in multiple languages
- **Metadata** - Saves video info, thumbnails, and descriptions

## Quick Start

### Docker (Recommended)

```bash
docker-compose up -d
```

Then open **http://localhost:4000**

### Default Login

- Username: `admin`
- Password: `admin123`

---

## How to Use

### 1. Create a Datasource

A datasource combines your download settings with the URLs you want to download.

1. Click **+ New** in the Datasources section
2. Enter a name (e.g., "YouTube Music")

### 2. Add URLs

In the **URLs** tab:
- Add YouTube channels, playlists, or single videos
- Organize into folders

### 3. Configure Options

In the **Config** tab:
- Choose video quality (720p, 1080p, 4K, etc.)
- Set output filename format
- Enable subtitles
- Add cookies for restricted content

### 4. Download

Click the **Download** button and watch progress in real-time!

### 5. Manage Files

Browse, rename, or delete downloaded files in the Files tab.

---

## Cookies

Some videos require YouTube login. To download them:

1. Export cookies from your browser (use a "Get cookies.txt" browser extension)
2. In your datasource, click the **gear icon** → **Upload cookies**
3. Save your config

---

## Scheduler

Schedule downloads to run automatically:

1. Go to the **Scheduler** tab
2. Create a new task
3. Set when to run (e.g., `0 2 * * *` = every day at 2 AM)
4. Choose which datasource to download

---

## Admin

The admin can:

- Create and manage user accounts
- View all downloads across users
- Monitor server status
- Upgrade yt-dlp
- Configure server settings
- Browse server files

---

## Docker

### Pull from Docker Hub

```bash
docker-compose up -d
```

### Build Your Own Image

```bash
docker build -t my-yt-dlp-manager .
docker run -d -p 4000:4000 -v ./data:/app/data my-yt-dlp-manager
```

---

## Support

- Check the **Logs** tab for errors
- Use **Server Manager** (admin only) for advanced settings

---

[README_](./README_.md) - Technical documentation for developers
