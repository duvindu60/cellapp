# CellApp Deployment Guide - Azure VM with GitHub Actions

This guide covers deploying the CellApp Flask application to an Azure Virtual Machine with automated CI/CD using GitHub Actions.

## Prerequisites

### Azure VM Requirements
- Ubuntu 20.04 LTS or newer
- Minimum 2GB RAM, 1 vCPU
- Public IP address
- SSH access enabled

### Local Requirements
- Git installed
- SSH key pair generated
- Access to your GitHub repository

## Initial Setup on Azure VM

### Step 1: Create Azure VM

1. Create an Ubuntu VM in Azure Portal
2. Configure Network Security Group (NSG) to allow:
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
3. Note down the public IP address

### Step 2: SSH into Your VM

```bash
ssh azureuser@<your-vm-public-ip>
```

### Step 3: Run Initial Setup Script

```bash
# Clone your repository temporarily to get the setup script
git clone <your-repo-url> /tmp/cellapp

# Run the setup script
sudo bash /tmp/cellapp/setup.sh
```

The setup script will:
- Install all required packages (Python, Nginx, Git, etc.)
- Clone your repository to `/var/www/cellapp`
- Set up Python virtual environment
- Install dependencies
- Configure systemd service
- Set up Nginx as reverse proxy
- Configure permissions

### Step 4: Configure Environment Variables

Edit the `.env` file with your actual values:

```bash
sudo nano /var/www/cellapp/.env
```

Required variables:
```env
FLASK_ENV=production
SECRET_KEY=<generate-a-secure-key>
SUPABASE_URL=<your-supabase-url>
SUPABASE_ANON_KEY=<your-supabase-key>
```

To generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Set Up Firewall

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### Step 6: Configure SSL Certificate (Recommended)

Using Let's Encrypt (free):

```bash
sudo certbot --nginx -d your-domain.com
```

Follow the prompts. Certbot will automatically:
- Obtain SSL certificate
- Update Nginx configuration
- Set up auto-renewal

If using IP address instead of domain, you'll need to:
1. Comment out SSL lines in `/etc/nginx/sites-available/cellapp`
2. Remove the HTTP to HTTPS redirect
3. Restart nginx: `sudo systemctl restart nginx`

## GitHub Actions CI/CD Setup

### Step 1: Generate SSH Key for GitHub Actions

On your Azure VM:

```bash
# Generate a new SSH key pair (no passphrase)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions_key -N ""

# Add public key to authorized_keys
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys

# Display private key (copy this for GitHub Secrets)
cat ~/.ssh/github_actions_key
```

### Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `AZURE_VM_HOST` | Your VM's public IP address |
| `AZURE_VM_USERNAME` | SSH username (e.g., `azureuser`) |
| `AZURE_VM_SSH_KEY` | Private key from `~/.ssh/github_actions_key` |
| `AZURE_VM_PORT` | SSH port (default: `22`) |
| `APP_URL` | Your application URL (e.g., `https://your-domain.com`) |

### Step 3: Enable GitHub Actions

The workflow file (`.github/workflows/deploy.yml`) is already in your repository. It will:
- Trigger on pushes to `main` or `master` branch
- SSH into your Azure VM
- Pull latest code
- Update dependencies
- Restart the application
- Run health check

### Step 4: Test Automated Deployment

```bash
# Make a small change and commit
git add .
git commit -m "Test deployment"
git push origin main
```

Check the Actions tab in GitHub to see the deployment progress.

## Managing the Application

### Service Management

```bash
# Start the application
sudo systemctl start cellapp

# Stop the application
sudo systemctl stop cellapp

# Restart the application
sudo systemctl restart cellapp

# Check status
sudo systemctl status cellapp

# Enable auto-start on boot
sudo systemctl enable cellapp
```

### View Logs

```bash
# Application logs (systemd)
sudo journalctl -u cellapp -f

# Application logs (file)
tail -f /var/log/cellapp/error.log
tail -f /var/log/cellapp/access.log

# Nginx logs
tail -f /var/log/nginx/cellapp_error.log
tail -f /var/log/nginx/cellapp_access.log
```

### Manual Deployment

If you need to deploy manually:

```bash
cd /var/www/cellapp
sudo bash deploy.sh
```

### Update Configuration

After changing `.env` or configuration files:

```bash
sudo systemctl restart cellapp
```

After changing Nginx configuration:

```bash
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

## Monitoring and Maintenance

### Check Application Health

```bash
curl http://localhost:5001/login
curl https://your-domain.com/login
```

### Database Backups

If using Supabase, backups are handled automatically. For local databases, set up regular backups:

```bash
# Add to crontab
sudo crontab -e

# Example: Daily backup at 2 AM
0 2 * * * /usr/bin/backup-script.sh
```

### Update SSL Certificate

Certbot auto-renews certificates. To test renewal:

```bash
sudo certbot renew --dry-run
```

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /var/www/cellapp
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart cellapp
```

## Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status cellapp

# Check logs for errors
sudo journalctl -u cellapp -n 50

# Verify .env file exists and has correct permissions
ls -la /var/www/cellapp/.env
```

### 502 Bad Gateway Error

```bash
# Check if Gunicorn is running
sudo systemctl status cellapp

# Check Nginx configuration
sudo nginx -t

# Verify Gunicorn is listening on correct port
sudo netstat -tlnp | grep 5001
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/cellapp

# Fix .env permissions
sudo chmod 600 /var/www/cellapp/.env
```

### GitHub Actions Deployment Fails

1. Verify GitHub Secrets are set correctly
2. Check SSH access: `ssh -i ~/.ssh/github_actions_key azureuser@<vm-ip>`
3. Check GitHub Actions logs in the Actions tab
4. Verify the VM can access GitHub: `git ls-remote <your-repo-url>`

## Security Best Practices

1. **Keep system updated**: Regular security updates
2. **Use strong passwords**: For SSH and application
3. **Limit SSH access**: Use key-based authentication only
4. **Enable firewall**: Only allow necessary ports
5. **Use HTTPS**: Always use SSL certificates
6. **Secure .env file**: Never commit to Git, restrict permissions
7. **Monitor logs**: Regularly check for suspicious activity
8. **Backup regularly**: Both application and database
9. **Rate limiting**: Already configured in the application
10. **Keep dependencies updated**: Regular pip updates

## Performance Optimization

### Gunicorn Workers

Adjust workers in `cellapp.service`:
```
Workers = (2 × CPU cores) + 1
```

For 2 CPU cores: 5 workers

### Nginx Caching

Add to nginx.conf for static content:
```nginx
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Database Connection Pooling

If using heavy database operations, consider implementing connection pooling in your application.

## Scaling Considerations

### Vertical Scaling
- Upgrade VM size in Azure Portal
- Adjust Gunicorn workers accordingly
- No code changes needed

### Horizontal Scaling
- Set up Azure Load Balancer
- Deploy to multiple VMs
- Use shared session storage (Redis)
- Use shared file storage for uploads

## Support

For issues or questions:
1. Check application logs
2. Review this deployment guide
3. Check GitHub Issues
4. Contact development team

## Additional Resources

- [Flask Deployment Documentation](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Azure VM Documentation](https://docs.microsoft.com/en-us/azure/virtual-machines/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
