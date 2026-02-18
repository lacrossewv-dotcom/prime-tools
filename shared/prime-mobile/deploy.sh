#!/bin/bash
# Deploy PRIME Mobile to Cloud Run
# Copy this file to deploy.local.sh and fill in your secrets
cd "C:/Users/lacro/.google_workspace_mcp"

GCLOUD="/c/Users/lacro/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd"

echo "y" | "$GCLOUD" run deploy prime-mobile \
  --source . \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=production,GOOGLE_CLIENT_ID=YOUR_CLIENT_ID,GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET,GOOGLE_WEB_CLIENT_ID=YOUR_WEB_CLIENT_ID,GOOGLE_WEB_CLIENT_SECRET=YOUR_WEB_CLIENT_SECRET,GOOGLE_REFRESH_TOKEN=YOUR_REFRESH_TOKEN,GEMINI_API_KEY=YOUR_GEMINI_KEY,JWT_SECRET=YOUR_JWT_SECRET,ALLOWED_EMAIL=YOUR_EMAIL,CLAUDE_API_KEY=YOUR_CLAUDE_KEY" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=60
