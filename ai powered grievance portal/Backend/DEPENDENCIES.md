# AI Powered Grievance Portal - Backend Dependencies Analysis

## 📋 **Complete Dependencies List**

### **Core Framework & Server**

1. **FastAPI (0.104.1)** - Modern web framework for building APIs
2. **Uvicorn (0.24.0)** - ASGI server for running FastAPI applications
3. **Pydantic (2.5.0)** - Data validation and serialization

### **Form & File Handling**

4. **python-multipart (0.0.6)** - Required for handling form data and file uploads

### **Security & Authentication**

5. **bcrypt (4.1.2)** - Password hashing and verification

### **Database Connectivity**

6. **PyMongo (4.6.0)** - MongoDB driver for Python
7. **mysql-connector-python (8.2.0)** - MySQL database connector (currently imported but not actively used)

### **Configuration & Environment**

8. **python-dotenv (1.0.0)** - Load environment variables from .env files

### **External API Calls**

9. **requests (2.31.0)** - HTTP library for making API calls (used for Groq AI classification)

### **Background Tasks & Scheduling**

10. **APScheduler (3.10.4)** - Advanced Python Scheduler for automated reminders
11. **pytz (2023.3)** - Timezone handling for scheduler

### **🆕 AI & Machine Learning (New Features)**

12. **scikit-learn (1.3.2)** - Machine learning library for TF-IDF similarity detection
13. **numpy (1.24.4)** - Numerical computing library (required by scikit-learn)

### **Built-in Python Modules (No Installation Required)**

- `datetime` & `timedelta` - Date and time operations
- `difflib` - String similarity matching
- `os` - Operating system interface
- `random` & `string` - Random data generation
- `logging` - Application logging

## 🔧 **Installation Instructions**

### **Method 1: Install from requirements.txt**

```bash
cd Backend
pip install -r requirements.txt
```

### **Method 2: Manual Installation**

```bash
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 bcrypt==4.1.2 pymongo==4.6.0 mysql-connector-python==8.2.0 python-dotenv==1.0.0 requests==2.31.0 APScheduler==3.10.4 pytz==2023.3
```

## ⚠️ **Missing Dependencies Found**

The original requirements.txt was missing:

- **APScheduler** - Critical for automated reminder system
- **pytz** - Required for timezone handling in scheduler

## 🌍 **Environment Variables Required**

Create a `.env` file in the Backend directory with:

```env
MONGODB_URI=mongodb://localhost:27017/petition_db
GROQ_API_KEY=your_groq_api_key_here
```

## 📊 **Database Requirements**

### **MongoDB Collections Used:**

- `users` - User authentication data
- `reminders` - Automated reminder tracking
- Department-specific collections (e.g., `petitions_pwd`, `petitions_finance`, etc.)

### **MySQL (Optional)**

- Currently imported but not actively used
- Can be removed if not needed for future features

## 🚀 **Key Features Supported**

1. **Web API Framework** - FastAPI with CORS support
2. **User Authentication** - bcrypt password hashing
3. **Department Classification** - Groq AI integration
4. **File Upload Support** - Multipart form handling
5. **Automated Reminders** - Background scheduling system
6. **Database Operations** - MongoDB integration
7. **Grievance Tracking** - Unique ID generation and tracking

## 🛡️ **Security Considerations**

- Passwords are hashed using bcrypt
- CORS middleware configured for cross-origin requests
- Environment variables used for sensitive configuration
- Input validation through Pydantic models

## 📱 **API Endpoints Available**

- `/` - Health check
- `/register` - User registration
- `/login` - User/admin authentication
- `/classify` - AI-powered department classification
- `/submit_to_department` - Submit grievances
- `/admin/petitions` - Admin petition management
- `/track_grievance` - Grievance tracking
- `/admin/send_reminders` - Manual reminder triggers
- `/admin/reminders` - Reminder history
- `/admin/reminder_stats` - Reminder statistics

## 🔄 **Background Services**

- **Daily Reminder Check** - Runs at 9:00 AM IST
- **Frequent Reminder Check** - Runs every 6 hours
- **Automated Status Monitoring** - Tracks inactive grievances

## ✅ **Verification Steps**

1. Install all dependencies
2. Set up environment variables
3. Start MongoDB service
4. Run: `uvicorn main:app --reload`
5. Test API at: `http://localhost:8000`

Your backend is now ready with all necessary dependencies for the automated reminders system!
