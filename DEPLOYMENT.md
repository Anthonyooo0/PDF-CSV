# Deploying to Render

This guide explains how to deploy the PDF-CSV backend to Render using Docker to ensure all system dependencies are properly installed.

## Why Docker is Required

The backend requires system-level dependencies that are not available in Render's native Python runtime:
- **tesseract-ocr**: Required for OCR processing of scanned PDFs
- **poppler-utils**: Required for PDF to image conversion

These dependencies can only be installed via Docker, which is why we use Render's Blueprint feature with a Dockerfile.

## Prerequisites

- A Render account (sign up at https://render.com if you don't have one)
- Your GitHub account connected to Render
- OpenAI API key OR Anthropic API key

## Initial Setup

### Step 1: Connect Your Repository as a Blueprint

1. Log in to your [Render Dashboard](https://dashboard.render.com/)

2. Click the **"New +"** button in the top right corner

3. Select **"Blueprint"** from the dropdown menu

4. Click **"Connect account"** if you haven't connected your GitHub account yet
   - Authorize Render to access your GitHub repositories

5. Find and select the **Anthonyooo0/PDF-CSV** repository from the list
   - You can use the search box to find it quickly

6. Configure the Blueprint:
   - **Blueprint Name**: Choose a name (e.g., "PDF-CSV Backend")
   - **Branch**: Select `main` (or the branch you want to deploy)

7. Click **"Connect"** to continue

### Step 2: Review Resources

Render will analyze your `render.yaml` file and show you the resources that will be created:

- **Web Service**: `pdf-csv-backend`
  - Runtime: Docker
  - Build: Uses `backend/Dockerfile`
  - Environment: Docker container with tesseract-ocr and poppler-utils

Review the changes and verify that:
- The service type is "Web Service"
- The runtime is "Docker" (not Python)
- The Dockerfile path is `backend/Dockerfile`

### Step 3: Configure Environment Variables

Before clicking "Apply", you need to set your API keys:

1. In the resources list, click on the **pdf-csv-backend** service

2. Scroll down to **Environment Variables**

3. Add your API key (you need at least one):

   **For OpenAI:**
   ```
   Key: OPENAI_API_KEY
   Value: sk-...your-api-key...
   ```

   **For Anthropic:**
   ```
   Key: ANTHROPIC_API_KEY
   Value: sk-ant-...your-api-key...
   ```

4. Click **"Save"** or continue to the next step

### Step 4: Deploy

1. Click the **"Apply"** button to start provisioning

2. Render will now:
   - Build the Docker image using your Dockerfile
   - Install system dependencies (tesseract-ocr, poppler-utils)
   - Install Python dependencies via Poetry
   - Deploy your backend service

3. Monitor the build logs:
   - You'll see Docker building the image
   - System dependencies being installed
   - Python packages being installed
   - The service starting up

4. Wait for the deployment to complete (usually 3-5 minutes)

### Step 5: Verify Deployment

Once deployed, you should see:

✅ **Build successful** - Docker image built without errors
✅ **Deploy successful** - Service is running
✅ **No dependency errors** - No "Missing system dependencies" messages in logs

Your backend will be available at a URL like:
```
https://pdf-csv-backend.onrender.com
```

Test the deployment by:
1. Opening the `/docs` endpoint to see the API documentation
2. Uploading a test PDF through the API or frontend

## Managing Your Deployment

### Updating Your Service

When you push changes to your repository:

1. Commit and push your changes to the `main` branch (or whichever branch you configured)

2. Render will automatically detect the changes and trigger a new deployment

3. Monitor the build logs in your Render Dashboard

### Viewing Logs

To view your service logs:

1. Go to your Render Dashboard
2. Click on the **pdf-csv-backend** service
3. Click the **"Logs"** tab
4. You'll see real-time logs including:
   - Build logs (Docker build process)
   - Runtime logs (application output)
   - Error messages (if any)

### Manually Triggering a Deploy

To manually redeploy:

1. Go to your service in the Render Dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

## Troubleshooting

### Error: "Missing system dependencies"

If you see this error in the logs:
```
ERROR: Missing system dependencies: tesseract-ocr, poppler-utils
```

**Cause**: Render is not using the Dockerfile (likely using native Python runtime instead)

**Solution**: 
1. Verify your service is using Docker runtime (not Python)
2. In Render Dashboard, go to your service settings
3. Check that "Docker" is selected as the runtime
4. If it shows "Python", you need to delete the service and recreate it via Blueprint (Step 1)

### Error: Docker Build Fails

If the Docker build fails:

1. Check the build logs for specific error messages
2. Common issues:
   - Poetry dependency conflicts: Check `poetry.lock` is up to date
   - Network issues: Retry the build
   - Dockerfile syntax errors: Review the Dockerfile

### Service Exits Immediately After Starting

If the service starts but exits right away:

1. Check the runtime logs for error messages
2. Common issues:
   - Missing environment variables (API keys)
   - Port binding issues (Render uses `$PORT` environment variable)
   - Application startup errors

### Existing Manual Service Conflicts

If you previously created the service manually (not via Blueprint):

1. The manual service will not use the `render.yaml` configuration
2. You need to delete the old manual service first
3. Then create a new service via Blueprint (follow Step 1)

**To delete the old service:**
1. Go to the service in Render Dashboard
2. Click "Settings"
3. Scroll to the bottom and click "Delete Web Service"
4. Confirm the deletion
5. Then follow the Blueprint setup steps above

## Environment Variables Reference

The backend requires at least one of these API keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key for GPT-4o model |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key for Claude model |

*At least one API key is required. The backend will use whichever is provided.

## Architecture

The deployed service uses:
- **Base Image**: `python:3.12-slim`
- **System Dependencies**: tesseract-ocr, poppler-utils
- **Python Dependencies**: Managed via Poetry (see `pyproject.toml`)
- **Runtime**: FastAPI with Uvicorn
- **Port**: Dynamic (provided by Render via `$PORT` environment variable)

## Cost

Render offers:
- **Free Tier**: 750 hours/month (enough for one always-on service)
- **Paid Tier**: Starting at $7/month for more resources and always-on services

Note: The free tier has some limitations:
- Services spin down after 15 minutes of inactivity
- First request after spin-down will be slow (cold start)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Render's [Docker documentation](https://render.com/docs/docker)
3. Check the deployment logs in Render Dashboard
4. Open an issue in the GitHub repository
