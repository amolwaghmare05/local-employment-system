# Local Employment System - Deployment Guide

## 🚀 Deploy to Render (Free Hosting)

### Prerequisites
1. GitHub account (✅ Already done)
2. MongoDB Atlas account (Free)
3. Render account (Free)

### Step 1: Set up MongoDB Atlas (5 minutes)

1. **Create MongoDB Atlas Account**
   - Visit: https://www.mongodb.com/cloud/atlas/register
   - Sign up with Google or email

2. **Create Free Cluster**
   - Click "Build a Database"
   - Select "M0 FREE" tier
   - Choose cloud provider (AWS recommended)
   - Select region closest to you
   - Click "Create Cluster"

3. **Configure Database Access**
   - Go to "Database Access" in left menu
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `employment_admin`
   - Password: Click "Autogenerate Secure Password" (SAVE THIS!)
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access**
   - Go to "Network Access" in left menu
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (for Render deployment)
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" (Deployment)
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Driver: Python, Version: 3.12 or later
   - Copy the connection string (looks like):
     ```
     mongodb+srv://employment_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - **Replace `<password>` with your actual password!**

### Step 2: Deploy to Render (10 minutes)

1. **Create Render Account**
   - Visit: https://render.com
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect to your GitHub repository: `local-employment-system`
   - Click "Connect"

3. **Configure Service**
   - **Name**: local-employment-system
   - **Region**: Choose closest to you
   - **Branch**: main
   - **Root Directory**: (leave blank)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

4. **Add Environment Variables**
   Click "Add Environment Variable" for each:
   
   - **MONGODB_URI**: `your_mongodb_atlas_connection_string`
     (Paste the full connection string from Step 1.5)
   
   - **DATABASE_NAME**: `local_employment_db`
   
   - **SECRET_KEY**: Click "Generate" (Render will create secure key)
   
   - **JWT_SECRET_KEY**: Click "Generate" (Render will create secure key)

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first deployment
   - Render will show build logs
   - When complete, you'll see "Live" status

6. **Access Your Website**
   - Your site will be at: `https://local-employment-system.onrender.com`
   - Or the URL shown in Render dashboard

### Step 3: Test Your Live Website

1. Open your Render URL
2. Click "Register" and create a new account
3. Login and test all features
4. All three dashboards should work (worker, employer, admin)

### Important Notes

⚠️ **Free Tier Limitations**:
- Render free tier: Service sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- MongoDB Atlas M0: 512MB storage limit
- Recommended for development/portfolio projects

💡 **Your Data**:
- Local MongoDB data won't transfer automatically
- You'll need to recreate accounts on the live site
- Or export/import data manually

🔒 **Security**:
- Never commit `.env` file (already in .gitignore ✅)
- Use strong passwords for MongoDB Atlas
- Environment variables are secure on Render

### Troubleshooting

**If deployment fails:**
1. Check Render build logs for errors
2. Verify MongoDB connection string is correct
3. Ensure all environment variables are set
4. Check that `requirements.txt` has all dependencies

**If site is slow:**
- Free tier sleeps when inactive
- First load takes 30-60 seconds
- Consider upgrading to paid tier ($7/month) for always-on service

### Alternative: Railway (Another Free Option)

If you prefer Railway:
1. Visit: https://railway.app
2. Sign up with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add same environment variables
6. Railway will auto-deploy

---

## 📝 Next Steps After Deployment

1. Share your live website URL
2. Add URL to GitHub repository description
3. Update resume/portfolio with live link
4. Create admin account on live site
5. Post sample jobs for demonstration

Your website is now live and accessible worldwide! 🎉
