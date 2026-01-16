# GitHub Secrets Configuration

For automated deployment with GitHub Actions, you need to configure the following secrets in your GitHub repository.

## How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret listed below

## Required Secrets

### AZURE_VM_HOST
- **Description**: Your Azure VM's public IP address or domain name
- **Example**: `20.123.45.67` or `myapp.azurewebsites.net`
- **How to get**: From Azure Portal → Virtual Machines → Your VM → Overview → Public IP address

### AZURE_VM_USERNAME
- **Description**: SSH username for accessing the VM
- **Example**: `azureuser` (default) or your custom username
- **How to get**: The username you created when setting up the VM

### AZURE_VM_SSH_KEY
- **Description**: Private SSH key for authentication (entire key content)
- **Example**: 
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
  ... (many lines) ...
  -----END OPENSSH PRIVATE KEY-----
  ```
- **How to get**: 
  1. SSH into your Azure VM
  2. Run: `ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions_key -N ""`
  3. Run: `cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys`
  4. Run: `cat ~/.ssh/github_actions_key`
  5. Copy the **entire output** (including BEGIN and END lines)

### AZURE_VM_PORT
- **Description**: SSH port number
- **Example**: `22` (default SSH port)
- **Default**: If not set, defaults to 22
- **Note**: Only change if you've configured SSH on a custom port

### APP_URL
- **Description**: The full URL where your application will be accessible
- **Example**: `https://myapp.example.com` or `http://20.123.45.67`
- **Purpose**: Used for health checks after deployment

## Security Best Practices

### For SSH Key:
1. **Never commit** the private key to your repository
2. **Generate a dedicated key** for GitHub Actions (don't reuse personal keys)
3. **Restrict permissions**: The key should only have access to the deployment directory
4. **Rotate regularly**: Change the SSH key periodically

### For Secrets:
1. **Minimal access**: Only grant necessary permissions
2. **Use separate environments**: Consider different secrets for staging/production
3. **Audit regularly**: Review who has access to secrets
4. **Never log secrets**: They won't appear in GitHub Actions logs

## Verification Checklist

Before your first deployment, verify:

- [ ] All 5 secrets are configured in GitHub
- [ ] SSH key is correctly formatted (includes BEGIN/END lines)
- [ ] SSH key is added to `authorized_keys` on the VM
- [ ] VM's firewall allows SSH from GitHub Actions IPs
- [ ] Application directory `/var/www/cellapp` exists on VM
- [ ] Setup script has been run successfully
- [ ] `.env` file is configured on the VM

## Testing SSH Connection

To verify your SSH configuration works, test locally:

```bash
# Create a temporary file with the private key
cat > /tmp/test_key <<'EOF'
[paste your AZURE_VM_SSH_KEY content here]
EOF

# Set correct permissions
chmod 600 /tmp/test_key

# Test connection
ssh -i /tmp/test_key -p [AZURE_VM_PORT] [AZURE_VM_USERNAME]@[AZURE_VM_HOST]

# Clean up
rm /tmp/test_key
```

If the test connection works, your GitHub Actions deployment should work too!

## Troubleshooting

### Deployment fails with "Permission denied"
- Verify SSH key is correctly copied (including all lines)
- Check that public key is in `~/.ssh/authorized_keys` on VM
- Verify key permissions: `chmod 600 ~/.ssh/authorized_keys`

### Deployment fails with "Connection refused"
- Check AZURE_VM_HOST is correct
- Verify AZURE_VM_PORT is correct (default: 22)
- Ensure VM's Network Security Group allows SSH (port 22)

### Health check fails
- Verify APP_URL is correct and accessible
- Check if application started: `sudo systemctl status cellapp`
- Review application logs: `sudo journalctl -u cellapp -n 50`

## Environment-Specific Configurations

### Production
Use these exact secret names as listed above.

### Staging (Optional)
If you want a staging environment, create:
- `STAGING_AZURE_VM_HOST`
- `STAGING_AZURE_VM_USERNAME`
- `STAGING_AZURE_VM_SSH_KEY`
- `STAGING_AZURE_VM_PORT`
- `STAGING_APP_URL`

Then modify the workflow file to use different secrets based on the branch.

## Additional Resources

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [SSH Key Generation Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
- [Azure VM SSH Access](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/ssh-from-windows)
