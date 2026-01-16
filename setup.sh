#!/bin/bash

# CellApp - Initial Setup Script for Azure VM
# This script sets up the application for the first time on a fresh Azure VM

set -e  # Exit on any error

echo "======================================"
echo "CellApp - Initial Setup Script"
echo "======================================"

# Variables
APP_NAME="cellapp"
APP_DIR="/var/www/$APP_NAME"
APP_USER="www-data"
PYTHON_VERSION="python3"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo ""
echo "[1/10] Updating system packages..."
apt update && apt upgrade -y

echo ""
echo "[2/10] Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx git ufw fail2ban certbot python3-certbot-nginx

echo ""
echo "[3/10] Creating application directory..."
mkdir -p $APP_DIR
mkdir -p /var/log/$APP_NAME

echo ""
echo "[4/10] Cloning repository..."
read -p "Enter your GitHub repository URL: " REPO_URL
git clone $REPO_URL $APP_DIR

echo ""
echo "[5/10] Creating Python virtual environment..."
cd $APP_DIR
$PYTHON_VERSION -m venv venv
source venv/bin/activate

echo ""
echo "[6/10] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "[7/10] Setting up environment variables..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp $APP_DIR/env.example $APP_DIR/.env
    echo "IMPORTANT: Edit $APP_DIR/.env with your actual environment variables!"
    echo "Press Enter to continue after editing .env file..."
    read
fi

echo ""
echo "[8/10] Setting permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chown -R $APP_USER:$APP_USER /var/log/$APP_NAME
chmod 600 $APP_DIR/.env

echo ""
echo "[9/10] Setting up systemd service..."
cp $APP_DIR/cellapp.service /etc/systemd/system/cellapp.service
systemctl daemon-reload
systemctl enable cellapp
systemctl start cellapp

echo ""
echo "[10/10] Setting up Nginx..."
# Backup default nginx config
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Copy and configure nginx
cp $APP_DIR/nginx.conf /etc/nginx/sites-available/$APP_NAME

echo "Enter your domain name (or Azure VM IP address):"
read DOMAIN_NAME
sed -i "s/your-domain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/$APP_NAME

# Enable site
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next Steps:"
echo "1. Configure firewall:"
echo "   sudo ufw allow 22"
echo "   sudo ufw allow 80"
echo "   sudo ufw allow 443"
echo "   sudo ufw enable"
echo ""
echo "2. Set up SSL certificate (recommended):"
echo "   sudo certbot --nginx -d $DOMAIN_NAME"
echo ""
echo "3. Configure GitHub Secrets for CI/CD:"
echo "   - AZURE_VM_HOST: Your VM's public IP"
echo "   - AZURE_VM_USERNAME: Your SSH username"
echo "   - AZURE_VM_SSH_KEY: Your private SSH key"
echo "   - AZURE_VM_PORT: SSH port (default: 22)"
echo "   - APP_URL: https://$DOMAIN_NAME"
echo ""
echo "4. Check application status:"
echo "   sudo systemctl status cellapp"
echo "   sudo systemctl status nginx"
echo ""
echo "5. View logs:"
echo "   sudo journalctl -u cellapp -f"
echo "   tail -f /var/log/cellapp/error.log"
echo ""
echo "Your application should now be running!"
