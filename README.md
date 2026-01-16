# CellApp - Flask Web Application

A modern Flask web application with mobile number + OTP authentication, built with a professional dark theme and responsive design.

## 🚀 Features

- **Mobile-First Design**: Responsive UI that works on all devices
- **OTP Authentication**: Secure login using mobile number and OTP
- **Modern UI**: Professional dark theme with Bootstrap 5
- **Session Management**: Secure session handling
- **Modular Architecture**: Clean code structure with blueprints
- **Production Ready**: Optimized for hosting and deployment

## 📱 Authentication Flow

1. **Enter Mobile Number**: 10-digit mobile number validation
2. **Send OTP**: System sends OTP (currently fixed as `123456` for testing)
3. **Verify OTP**: Enter the OTP to complete login
4. **Access Dashboard**: Redirected to main application

## 🛠️ Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd cellapp
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Test the app**
   - Go to `http://localhost:5000/login`
   - Enter mobile number: `1234567890`
   - Enter OTP: `123456`
   - You're logged in! 🎉

## 🚀 Production Deployment

<<<<<<< HEAD
### Azure VM with GitHub Actions (Recommended)

This application is configured for automated deployment to Azure VM using GitHub Actions.

**Quick Deployment:**
1. Run the setup script on your Azure VM:
   ```bash
   sudo bash setup.sh
   ```

2. Configure GitHub Secrets:
   - `AZURE_VM_HOST` - Your VM's public IP
   - `AZURE_VM_USERNAME` - SSH username
   - `AZURE_VM_SSH_KEY` - Private SSH key
   - `AZURE_VM_PORT` - SSH port (default: 22)
   - `APP_URL` - Your application URL

3. Push to main branch - deployment happens automatically!

**For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

### Manual Deployment with Gunicorn

=======
### Using Gunicorn (Recommended)
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
```bash
# Install gunicorn
pip install gunicorn

# Run production server
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

### Environment Variables
<<<<<<< HEAD
Create a `.env` file (copy from `env.example`):
=======
Create a `.env` file:
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
```env
SECRET_KEY=your-secret-key-here
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
FLASK_ENV=production
```

## 📁 Project Structure

```
cellapp/
<<<<<<< HEAD
├── app.py                      # Main Flask application
├── wsgi.py                    # WSGI entry point for production
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── env.example                # Environment variables template
├── README.md                  # This file
├── DEPLOYMENT.md              # Detailed deployment guide
├── setup.sh                   # Initial setup script for Azure VM
├── deploy.sh                  # Manual deployment script
├── nginx.conf                 # Nginx reverse proxy configuration
├── cellapp.service            # Systemd service configuration
├── .github/
│   └── workflows/
│       └── deploy.yml         # GitHub Actions CI/CD workflow
├── routes/                    # Application routes (blueprints)
│   ├── __init__.py
│   ├── auth.py               # Authentication routes
│   ├── main.py               # Main application routes
│   └── api.py                # API routes
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   ├── auth/                 # Authentication templates
│   └── main/                 # Main app templates
├── static/                    # Static assets
│   ├── css/
│   ├── js/
│   └── manifest.json
├── utils/                     # Utility modules
│   ├── activity_logger.py
│   └── device_detector.py
└── database/                  # Database migrations
    └── migrations/
=======
├── app.py                 # Main Flask application
├── wsgi.py               # WSGI entry point for production
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── DEPLOYMENT.md         # Production deployment guide
├── routes/               # Application routes (blueprints)
│   ├── auth.py          # Authentication routes
│   ├── main.py          # Main application routes
│   └── api.py           # API routes
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   └── auth/            # Authentication templates
│       └── login.html   # Login page
└── static/              # Static assets
    ├── css/
    ├── js/
    └── manifest.json
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397
```

## 🎨 UI Features

- **Responsive Design**: Mobile-first approach
- **Dark Theme**: Professional black/white color scheme
- **Modern Icons**: Font Awesome integration
- **Bootstrap 5**: Latest UI components

## 🔐 Security

- **Session Management**: Secure session handling
- **Input Validation**: Mobile number format validation
- **Secure Cookies**: HTTPOnly and SameSite settings
- **Production Ready**: Optimized security settings

## 📚 Documentation

- **Setup Guide**: This README
<<<<<<< HEAD
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md) - Complete Azure VM deployment instructions
- **Environment Variables**: [env.example](env.example) - Template for environment configuration
- **Architecture**: [ARCHITECTURE_DOCUMENTATION.md](ARCHITECTURE_DOCUMENTATION.md)

## 🔧 Deployment Files

| File | Purpose |
|------|---------|
| `setup.sh` | Initial setup script for fresh Azure VM |
| `deploy.sh` | Manual deployment/update script |
| `nginx.conf` | Nginx reverse proxy configuration |
| `cellapp.service` | Systemd service configuration |
| `.github/workflows/deploy.yml` | GitHub Actions CI/CD workflow |
| `env.example` | Environment variables template |
=======
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Environment Variables**: See `env_example.txt`
>>>>>>> 20dac40646ecb456f1bdc39aa36c2952699ee397

## 🆘 Support

For issues or questions:
1. Check terminal for error messages
2. Verify environment variables
3. Ensure all dependencies are installed
4. Check browser console for errors

## 📄 License

MIT License - see LICENSE file for details.