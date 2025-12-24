# Data Persistence

## Overview

The Skill Tracker application automatically persists all your data (skills and counters) to disk. Data is preserved across server restarts and deployments.

## How It Works

- **Automatic Saving**: Data is automatically saved to JSON files whenever you create, update, or delete skills/counters
- **Storage Location**: Data files are stored in the `data/` directory:
  - `data/skills.json` - All skill tree data
  - `data/counters.json` - All counter data
- **Auto-Loading**: Data is automatically loaded when the server starts

## Data Files

The `data/` directory is:
- ✅ Created automatically on first use
- ✅ Excluded from git (in `.gitignore`)
- ✅ Preserved during deployments on Render.com

## Clearing All Data

### Via Web Interface

Click the "🗑️ Clear All Data" button in the top-right corner of the application:
- Permanently deletes all skills and counters
- Requires confirmation before executing
- Cannot be undone

### Via API

```bash
curl -X DELETE http://localhost:8000/api/data
```

### Manually

Delete the files directly:
```bash
rm -rf data/
```

## Production Deployment

On Render.com, the `data/` directory persists between deployments using Render's [Persistent Disks](https://render.com/docs/disks) feature (if configured).

**Note**: Without a persistent disk, data will be lost on each deployment. To enable persistence:

1. Go to your Render.com dashboard
2. Add a Persistent Disk to your service
3. Mount it to the `/data` path
4. Redeploy

## Backup

To backup your data:

```bash
# Copy data files
cp -r data/ data_backup_$(date +%Y%m%d)/
```

To restore:

```bash
# Stop the server first
cp -r data_backup_YYYYMMDD/* data/
# Restart the server
```

## Migration to Database

This file-based persistence is temporary. In Milestone-3, we'll migrate to a proper database (PostgreSQL) which will provide:
- Better performance for large datasets
- ACID transactions
- Concurrent access support
- Built-in backup/restore tools
