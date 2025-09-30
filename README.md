# Hair Color Classification Server - Render Deployment

This package contains the server-only version for Render.com deployment.

## Files Included

- `hair_color_server.py` - Main Flask server
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration file
- `.env` - Environment variables (DO NOT commit to git)
- `.gitignore` - Git ignore file
- `Tones_IBG.xlsx` - Product recommendations Excel file

## Deployment Steps

### 1. Prerequisites
- Render.com account
- Git repository

### 2. Push to GitHub/GitLab

```bash
cd render
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

### 3. Deploy on Render

#### Option A: Using render.yaml (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect `render.yaml`
5. Set environment variables in the dashboard:
   - `PROJECT_ID`: 799143320054
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: (copy from .env file)

#### Option B: Manual Setup
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure:
   - **Name**: hair-color-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn hair_color_server:app`
5. Add environment variables:
   - `PROJECT_ID`: 799143320054
   - `LOCATION`: us-central1
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: (copy entire JSON from .env)

### 4. Environment Variables

Set these in Render dashboard under "Environment":

```
PROJECT_ID=799143320054
LOCATION=us-central1
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

**Important**: Copy the full JSON value from your `.env` file.

## API Endpoints

- `GET /` - Health check
- `POST /classify` - Upload images for classification
  - Accepts multipart/form-data
  - Field names: `image_1`, `image_2`, `image_3`
  - Max 3 images
- `GET /health` - Health status

## Testing

Once deployed, test with:

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Classify image
curl -X POST https://your-app-name.onrender.com/classify \
  -F "image_1=@/path/to/image.jpg"
```

## Features

- Hair color classification using Google Vertex AI
- Product recommendations based on detected colors
- Supports up to 3 images per request
- Excel-based product database
- CORS enabled for web integration

## Notes

- Render's free tier may have cold starts (first request might be slow)
- The Excel file is included in the deployment
- Environment variables are securely stored in Render
- Python 3.11.9 is specified in render.yaml
- Debug mode is disabled for production