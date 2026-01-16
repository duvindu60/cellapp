#!/bin/bash

# CellApp - Manual Deployment Script
# Use this for manual deployments or troubleshooting

set -e  # Exit on any error

APP_NAME="cellapp"
APP_DIR="/var/www/$APP_NAME"

echo "======================================"
echo "CellApp - Deployment Script"
echo "======================================"

# Check if running in the correct directory
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory $APP_DIR not found!"
    echo "Please run setup.sh first."
    exit 1
fi

cd $APP_DIR

echo ""
echo "[1/6] Pulling latest changes from Git..."
git pull origin main

echo ""
echo "[2/6] Activating virtual environment..."
source venv/bin/activate

echo ""
echo "[3/6] Updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "[4/6] Running database migrations (if any)..."
# Add your migration commands here if needed
# Example: flask db upgrade

echo ""
echo "[5/6] Restarting application service..."
sudo systemctl restart cellapp

echo ""
echo "[6/6] Checking service status..."
sleep 3
sudo systemctl status cellapp --no-pager

echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "Useful commands:"
echo "  View logs: sudo journalctl -u cellapp -f"
echo "  Check status: sudo systemctl status cellapp"
echo "  Restart: sudo systemctl restart cellapp"
echo "  Nginx reload: sudo systemctl reload nginx"
