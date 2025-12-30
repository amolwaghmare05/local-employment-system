import os
from dotenv import load_dotenv
load_dotenv()

# ---- Flask / JWT ----
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_this_jwt_secret")

# ---- MongoDB ----
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://sandeshshinde2026_db_user:ZsqSNgjJwzPMZiqT@localemployment.ptzwmby.mongodb.net/?retryWrites=true&w=majority&appName=localEmployment")
DATABASE_NAME = os.getenv("DATABASE_NAME", "local_employment_db")