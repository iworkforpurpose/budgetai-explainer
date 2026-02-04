# Budget 2026 AI - Deployment Guide

## 🚀 Deploy to Render (Free Tier)

### Prerequisites
- [x] GitHub repo: `https://github.com/iworkforpurpose/budgetai-explainer`
- [x] Supabase project with 1,461 chunks uploaded
- [x] Groq API key

### Step 1: Create Render Web Service

1. Go to https://render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select repository: `iworkforpurpose/budgetai-explainer`
5. Click **"Connect"**

### Step 2: Configure Service

**Basic Settings:**
- **Name**: `budgetai-backend` (or your choice)
- **Region**: Oregon (US West) - lowest latency for free tier
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **Free** (512 MB RAM, sleeps after inactivity)

### Step 3: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these **REQUIRED** variables:

```
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-anon-key>
GROQ_API_KEY=<your-groq-api-key>
```

**Optional** (already have defaults):
```
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
HOST=0.0.0.0
PORT=10000
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait ~5-10 minutes for:
   - Install dependencies (~3 min)
   - Download sentence-transformers model (~2 min)
   - Start server (~1 min)

### Step 5: Verify Deployment

Once deployed, your app will be at:
```
https://budgetai-backend.onrender.com
```

**Test endpoints:**
```bash
# Health check
curl https://budgetai-backend.onrender.com/api/v1/health

# Chat
curl -X POST https://budgetai-backend.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the tax benefits for salaried employees?"}'

# Tax calculator
curl -X POST https://budgetai-backend.onrender.com/api/v1/calculate/calculate-tax \
  -H "Content-Type: application/json" \
  -d '{"income": 1000000, "regime": "new"}'
```

---

## 📊 Expected Performance

**Cold Start** (after sleep):
- ~30 seconds (loading sentence-transformers model)

**Warm Response**:
- Health: ~50ms
- Search: ~200ms
- Chat (RAG): ~800ms
- Calculator: ~50ms

**Memory Usage**:
- Idle: ~400 MB
- Peak: ~480 MB
- Limit: 512 MB (Free tier)

---

## 🔧 Troubleshooting

### Deployment fails
- Check build logs for missing dependencies
- Verify Python version (3.11+)
- Check root directory is set to `backend`

### Out of memory
- Sentence-transformers model loads into RAM (~300MB)
- If OOM, upgrade to Starter plan ($7/mo, 2GB RAM)

### Cold starts too slow
- Free tier sleeps after 15 min inactivity
- Use cron-job.org to ping `/api/v1/health` every 14 min
- Or upgrade to Starter plan (no sleep)

### Connection to Supabase fails
- Verify SUPABASE_URL and SUPABASE_KEY
- Check Supabase project is active
- Test from local: `python scripts/test_connections.py`

---

## 💰 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Supabase | Free (500MB) | $0 |
| Groq | Free (30 RPM) | $0 |
| Render | Free (512MB) | $0 |
| **Total** | | **$0/month** |

**Upgrade costs** (if needed):
- Render Starter: $7/mo (no sleep, 2GB RAM)
- Supabase Pro: $25/mo (8GB storage, better perf)
- Groq: Free tier should be enough (30 RPM = ~3 users/min)

---

## 🎉 Next Steps

After deployment:
1. ✅ Test all endpoints
2. Update CORS in `app/main.py` to your frontend domain
3. Build frontend (Phase 6)
4. Connect frontend to backend API
5. Deploy frontend to Vercel/Netlify (free)

---

## 📝 Maintenance

**Auto-deploys:**
- Every `git push` to `main` triggers new deployment
- Takes ~5-8 minutes

**Monitoring:**
- Render dashboard shows logs, metrics, deploys
- Set up alerts for errors

**Updates:**
- Update dependencies: `pip list --outdated`
- Update Render build: Push to GitHub
