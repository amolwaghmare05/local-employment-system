# JobMatrix - Smart Employment Platform

A web-based platform that connects talented professionals with employment opportunities. Built with Flask and MongoDB Atlas, featuring role-based access, intelligent job matching, and efficient data partitioning.

## Features

- **Role-Based Access**
  - Workers: Create profiles, search jobs, and submit applications
  - Employers: Post jobs and manage applications
  - Admins: System oversight and user management

- **Smart Job Matching**
  - Skills-based job matching algorithm
  - Location-aware job search
  - Real-time application tracking

- **Data Optimization**
  - Workers: Hash partitioning (8 partitions) for efficient lookups
  - Jobs: Range partitioning by year
  - Indexed search on skills and job requirements

## Technical Stack

- **Backend**: Python/Flask
- **Database**: MongoDB Atlas (Cloud)
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Authentication**: JWT (JSON Web Tokens)

## Database Collections

- **users** - Central authentication and user management
- **workers** - Worker profiles with skills and location
- **employers** - Employer profiles and company information
- **jobs** - Job postings with skill requirements and location
- **applications** - Job applications with status tracking
- **admins** - Admin profiles and permissions

## Setup

1. **MongoDB Atlas Setup** (Manual):
   - Create a MongoDB Atlas cluster
   - Create database: `local_employment_db`
   - Get connection string and configure IP whitelist
   - Collections will be created automatically

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** in `.env`:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   DATABASE_NAME=local_employment_db
   SECRET_KEY=your_secret_key
   JWT_SECRET_KEY=your_jwt_secret
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Create sample data** (Optional):
   ```bash
   python setup_sample_data.py
   ```

## Default Sample Accounts

After running `setup_sample_data.py`:
- **Admin**: admin@example.com (password: admin123)
- **Employer**: employer1@company.com (password: employer123)  
- **Worker**: worker1@email.com (password: worker123)

## Features by Role

### Workers
- Complete profile with skills and experience
- Browse matched job listings
- Apply to positions
- Track application status
- View application history

### Employers
- Create company profile
- Post job opportunities
- Review applications
- Manage applicant status
- View hiring statistics

### Administrators
- User management
- Job oversight
- Application monitoring
- Activity logging
- System statistics

## Security Features

- Password hashing with bcrypt
- JWT-based authentication
- Role-based access control
- Activity logging for admin actions

## Data Partitioning

- Workers table uses hash partitioning (8 partitions) for even distribution
- Jobs table uses range partitioning by year for efficient historical data management