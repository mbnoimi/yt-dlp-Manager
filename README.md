# yt-dlp Manager

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/0/00/Flag_of_Palestine.svg" alt="Palestine Flag" width="60" height="40">
  <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/Flag_of_Syria_%281930%E2%80%931958%2C_1961%E2%80%931963%29.svg" alt="Syria Flag" width="70" height="40">
  <img src="https://upload.wikimedia.org/wikipedia/commons/4/49/Flag_of_Ukraine.svg" alt="Ukraine Flag" width="60" height="40">
</p>

<p align="center">
  <b>🕊️ Freedom for Palestine, Ukraine, Syria, and all nations fighting against tyrants 🕊️</b>
</p>

<p align="center">
  <sub>Free Palestine • Free Syria • Peace for Ukraine</sub>
</p>

<br>

<p align="center">
  <img src="assets/icons/logo.svg" alt="yt-dlp Manager Logo" width="120" height="120">
</p>

<p align="center">
  A powerful web-based download manager for YouTube, Vimeo, and thousands of other video sites
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-how-to-use">How to Use</a> •
  <a href="#-docker">Docker</a> •
  <a href="#-configuration">Configuration</a>
</p>

---

## ✨ Features

- **👥 Multi-User Support** - Create accounts for family or team members with isolated data folders
- **📁 Organized Downloads** - Organize downloads by folders with custom configurations
- **📅 Scheduled Downloads** - Set up automatic download schedules using cron expressions
- **🔴 Real-time Progress** - Watch download progress live in your browser via SSE streaming
- **🔄 Automatic Retries** - Handles connection issues gracefully
- **📝 Subtitle Support** - Download subtitles in multiple languages
- **📸 Metadata** - Saves video info, thumbnails, and descriptions
- **🍪 Cookie Support** - Upload cookies for restricted content
- **🔗 Deduplication** - Global storage with symlinks to avoid re-downloading
- **⚙️ Server Manager** - Admin panel for system status, user management, and logs

---

## 📦 Installation

### Docker (Recommended)

#### Docker Compose

```yml
services:
  yt-dlp-manager:
    image: mbnoimi/yt-dlp-manager:latest
    container_name: yt-dlp-manager
    ports:
      - "4000:4000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/backend/logs
    environment:
      - BACKEND_SECRET_KEY=your-secret-key-change-in-production
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=pass
    restart: unless-stopped
```

Then

```bash
docker-compose up -d
```

#### Direct Command

```bash
docker run -d \
  --name yt-dlp-manager \
  -p 4000:4000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/backend/logs \
  -e BACKEND_SECRET_KEY=your-secret-key-change-in-production \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=pass \
  --restart unless-stopped \
  mbnoimi/yt-dlp-manager:latest
```


The image is automatically pulled from [Docker Hub](https://hub.docker.com/r/mbnoimi/yt-dlp-manager).

---

## 🚀 Quick Start

1. Open **http://localhost:4000**
2. Login with default credentials:
   - Username: `admin`
   - Password: `pass`
3. Create a datasource and start downloading!

---

## 📖 How to Use

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

## 🍪 Cookies

Some videos require YouTube login. To download them:

1. Export cookies from your browser (use a "Get cookies.txt" browser extension)
2. In your datasource, click the **gear icon** → **Upload cookies**
3. Save your config

---

## 📅 Scheduler

Schedule downloads to run automatically:

1. Go to the **Scheduler** tab
2. Create a new task
3. Set when to run (e.g., `0 2 * * *` = every day at 2 AM)
4. Choose which datasource to download

### Cron Examples

| Expression | Description |
|------------|-------------|
| `0 2 * * *` | Every day at 2 AM |
| `0 9 * * 0` | Every Sunday at 9 AM |
| `0 */6 * * *` | Every 6 hours |

---

## 🖥️ Admin

The admin can:

- Create and manage user accounts
- View all downloads across users
- Monitor server status (CPU, memory, disk)
- Upgrade yt-dlp to latest version
- Configure server settings
- Browse server files
- View backend logs

---

## 🐳 Docker

### Quick Start

```bash
# Pull and run from Docker Hub
docker-compose up -d
```

The application is available at **http://localhost:4000**

### Image

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_SECRET_KEY` | - | JWT signing key |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `pass` | Default admin password |
| `BACKEND_MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads |
| `BACKEND_DEDUPLICATION_ENABLED` | `true` | Enable deduplication |
| `ALLOW_NEW_USERS` | `false` | Allow user registration |

---

## 🛠️ Technology Stack

### Backend

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- **Database**: [SQLite](https://www.sqlite.org/) with SQLAlchemy ORM
- **Download Engine**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- **Auth**: JWT-based multi-user authentication
- **Server**: [Uvicorn](https://www.uvicorn.org/) ASGI server

### Frontend

- **Framework**: [Svelte 5](https://svelte.dev/) - Cybernetically enhanced web apps
- **Build Tool**: [Vite](https://vitejs.dev/) - Next generation frontend tooling
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com/) - Utility-first CSS
- **UI Components**: [Skeleton UI](https://www.skeleton.dev/) - Svelte component library

---

## 📂 Project Structure

```
yt-dlp Manager/
├── src/
│   ├── backend/              # FastAPI application
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, security, deps
│   │   ├── db/              # Database models & sync
│   │   ├── services/        # Downloader, scheduler
│   │   └── main.py          # Entry point
│   │
│   ├── frontend/             # Svelte SPA
│   │   ├── src/
│   │   │   ├── lib/         # Components, pages, stores
│   │   │   ├── App.svelte   # Root component
│   │   │   └── main.ts      # Entry point
│   │   └── package.json
│   │
│   └── data/                # User data
│       └── <username>/
│           ├── downloads/   # Downloaded files
│           ├── configs/     # Config JSON files
│           └── urls/       # URL JSON files
│
├── docker-compose.yml        # Docker deployment
└── .env                    # Configuration
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests
5. Commit your changes
6. Push to the branch
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The amazing download engine
- [FastAPI](https://fastapi.tiangolo.com/) - The powerful Python framework
- [Svelte](https://svelte.dev/) - The wonderful UI framework
- [Skeleton UI](https://www.skeleton.dev/) - Beautiful Svelte components
- All contributors who help improve this project

---

<p align="center">
  Made with ❤️ by a Syrian developer who believes in freedom for Palestine, Ukraine, Syria, and any nation standing against tyrants
</p>

<p align="center">
  ⭐ Star this repo if you find it useful!
</p>
