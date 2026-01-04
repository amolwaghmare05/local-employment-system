# Local Employment System

A Flask-based web application that connects job seekers with employers in their local area. Features intelligent job matching, role-based dashboards, and real-time application tracking.

## 🌐 Live Demo

**Try it here**: [https://local-employment-system-production.up.railway.app](https://local-employment-system-production.up.railway.app/)

## Features

- **For Job Seekers**: Create profile, search jobs by skills/location, apply and track applications
- **For Employers**: Post jobs, review applications, manage candidates
- **For Admins**: User management, job oversight, system monitoring
- **Smart Matching**: Skill-based job recommendations
- **Secure Auth**: JWT tokens with bcrypt password hashing

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB Atlas
- **Frontend**: HTML5, Bootstrap 5, Vanilla JS
- **Auth**: JWT (Flask-JWT-Extended)

## Quick Start

1. Clone the repository
   ```bash
   git clone https://github.com/amolwaghmare05/local-employment-system.git
   cd local-employment-system
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up MongoDB Atlas
   - Create a free cluster at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Get your connection string
   - Whitelist your IP address

4. Configure environment variables (create `.env` file)
   ```bash
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   DATABASE_NAME=local_employment_db
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   ```

5. Run the application
   ```bash
   python app.py
   ```

6. Access at `http://localhost:5000`

## Project Structure

```
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── models/             # Database models
│   ├── mongodb.py
│   ├── user_model_mongo.py
│   ├── job_model_mongo.py
│   └── application_model_mongo.py
├── routes/             # Route blueprints
│   ├── worker_routes.py
│   ├── employer_routes.py
│   └── admin_routes.py
└── templates/          # HTML templates
```

## Deployment

The app is deployed on Railway. For deploying your own instance:

1. Fork this repository
2. Sign up at [railway.app](https://railway.app)
3. Create new project from GitHub repo
4. Add environment variables (same as .env)
5. Deploy automatically!

## Screenshots

*Coming soon*

## License

MIT License - feel free to use for your projects

## Author

Developed by Amol Waghmare

---

**Note**: This project was created as a learning exercise to understand Flask, MongoDB, and full-stack development.
- Activity logging for admin actions

## Data Partitioning

- Workers table uses hash partitioning (8 partitions) for even distribution
- Jobs table uses range partitioning by year for efficient historical data management