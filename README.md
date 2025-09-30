# Hair Color Classification Server - Heroku Deployment

This package contains the server-only version for Heroku deployment.

## Files Included

- `hair_color_server.py` - Main Flask server
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku process configuration
- `runtime.txt` - Python version specification
- `.env.example` - Environment variables template

## Deployment Steps

### 1. Prerequisites
- Heroku account and CLI installed
- Git repository initialized

### 2. Set Environment Variables

Set these config vars in Heroku dashboard or via CLI:

```bash
heroku config:set PROJECT_ID=your-gcp-project-id
heroku config:set LOCATION=us-central1
heroku config:set GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

### 3. Deploy to Heroku

```bash
# Login to Heroku
heroku login

# Create new app
heroku create your-app-name

# Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main

# Check logs
heroku logs --tail
```

### 4. Optional: Add Excel File

If you have the products Excel file (`Tones_IBG.xlsx`), you can:
- Upload it to cloud storage and set the URL
- Or include it in the deployment (add to git)

## API Endpoints

- `GET /` - Health check
- `POST /classify` - Upload images for classification
- `GET /health` - Health status

## Testing

```bash
curl https://your-app-name.herokuapp.com/health
```

## Environment Variables

- `PROJECT_ID` - Google Cloud Project ID (required)
- `LOCATION` - GCP region (default: us-central1)
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Service account credentials JSON (required)
- `EXCEL_PATH` - Path to products Excel file (optional)
- `PORT` - Server port (automatically set by Heroku)

## Notes

- The server runs on the port specified by Heroku's `PORT` environment variable
- Debug mode is disabled for production
- Products Excel file is optional - server will work without it