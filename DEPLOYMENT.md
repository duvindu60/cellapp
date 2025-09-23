# CellApp Deployment Guide

## 🚀 Production Deployment

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Local Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd cellapp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp env_example.txt .env
# Edit .env with your configuration

# Run the application
python app.py
```

### Production Deployment

#### Option 1: Using Gunicorn (Recommended)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

#### Option 2: Using Flask Development Server (Not for production)
```bash
# Set production environment
export FLASK_ENV=production
python app.py
```

### Environment Variables
Create a `.env` file with the following variables:
```
SECRET_KEY=your-secret-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
FLASK_ENV=production
```

### Security Considerations
1. **Change SECRET_KEY** in production
2. **Use HTTPS** in production (set SESSION_COOKIE_SECURE=True)
3. **Set strong passwords** for database access
4. **Use environment variables** for sensitive data
5. **Enable CSRF protection** if needed

### Hosting Platforms

#### Heroku
1. Create `Procfile`:
   ```
   web: gunicorn wsgi:application
   ```
2. Deploy to Heroku

#### DigitalOcean App Platform
1. Connect your repository
2. Set environment variables
3. Deploy

#### AWS/GCP/Azure
1. Use containerized deployment
2. Set up load balancer
3. Configure SSL certificates

### Monitoring
- Monitor application logs
- Set up health checks
- Monitor database performance
- Set up error tracking

### Backup Strategy
- Regular database backups
- Code repository backups
- Environment configuration backups
