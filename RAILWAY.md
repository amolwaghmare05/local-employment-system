# Railway Deployment Guide

## 🚀 Deploy to Railway (5 minutes)

### Step 1: Create Railway Account
1. Visit: https://railway.app
2. Click **"Login"** or **"Start a New Project"**
3. Sign in with **GitHub** (easiest)
4. Authorize Railway to access your GitHub

### Step 2: Deploy from GitHub

1. **Create New Project**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**

2. **Select Repository**
   - Find and select: **`local-employment-system`**
   - Click on the repository

3. **Add Variables**
   Railway will start deploying automatically, but we need to add environment variables:
   
   - Click on your service/deployment
   - Go to **"Variables"** tab
   - Click **"New Variable"** for each:

   ```
   MONGODB_URI=mongodb+srv://employment_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   (Use your MongoDB Atlas connection string from earlier)
   
   ```
   DATABASE_NAME=local_employment_db
   ```
   
   ```
   SECRET_KEY=your-secret-key-here
   ```
   (Generate a random string or use: https://randomkeygen.com/)
   
   ```
   JWT_SECRET_KEY=your-jwt-secret-key-here
   ```
   (Generate another random string)

4. **Redeploy**
   - After adding variables, click **"Deploy"** or trigger a redeploy
   - Railway will rebuild with the correct environment variables

### Step 3: Get Your URL

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. Your URL will be something like: `https://local-employment-system-production.up.railway.app`

### Step 4: Test Your Website

1. Open your Railway URL
2. Test registration and login
3. Verify all dashboards work

---

## ✅ Advantages of Railway

- **Faster cold starts** than Render (10-15 seconds vs 30-60 seconds)
- **$5 free credit per month** (usually enough for hobby projects)
- **Better performance** on free tier
- **Simple deployment** from GitHub
- **Automatic deploys** on git push

## 💡 Important Notes

- **Free tier**: $5 credit per month (resets monthly)
- Usage is based on compute time, not always-on
- Monitor your usage in Railway dashboard
- If you run out of credit, app will pause until next month

---

## 🔄 Automatic Deploys

Every time you push to GitHub, Railway automatically redeploys! No manual steps needed.

---

Your Railway deployment is complete! 🎉
