# SSH Authentication Troubleshooting Guide

## Error: "ssh: unable to authenticate, attempted methods [none]"

This error means GitHub Actions cannot authenticate with your Azure VM using the SSH key.

## Step-by-Step Fix

### Step 1: Generate a New SSH Key on Azure VM

SSH into your Azure VM:

```bash
ssh your-username@your-vm-ip
```

Generate a new key pair **without a passphrase** (important!):

```bash
# Generate new SSH key (no passphrase - just press Enter when prompted)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions

# When prompted:
# Enter file in which to save the key: (already specified)
# Enter passphrase (empty for no passphrase): [PRESS ENTER]
# Enter same passphrase again: [PRESS ENTER]
```

### Step 2: Add Public Key to Authorized Keys

```bash
# Add the public key to authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Set correct permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/github_actions
chmod 644 ~/.ssh/github_actions.pub

# Verify the key was added
tail -1 ~/.ssh/authorized_keys
```

### Step 3: Copy Private Key for GitHub Secrets

Display the private key:

```bash
cat ~/.ssh/github_actions
```

**IMPORTANT:** Copy the **ENTIRE** output, including:
- `-----BEGIN OPENSSH PRIVATE KEY-----`
- All the encoded text in between
- `-----END OPENSSH PRIVATE KEY-----`

Example of what you should copy:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
NhAAAAAwEAAQAAAYEA1234567890abcdefghijklmnopqrstuvwxyz...
... (many more lines) ...
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
-----END OPENSSH PRIVATE KEY-----
```

### Step 4: Update GitHub Secret

1. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Find `AZURE_VM_SSH_KEY`
3. Click **Update** (pencil icon)
4. **Delete** the old value completely
5. **Paste** the entire private key (from BEGIN to END)
6. Click **Update secret**

### Step 5: Verify Other GitHub Secrets

Check these secrets are correct:

| Secret Name | Value | How to Verify |
|-------------|-------|---------------|
| `AZURE_VM_HOST` | Your VM's public IP | Azure Portal → VM → Overview |
| `AZURE_VM_USER` | SSH username | The user you SSH with (e.g., `azureuser`) |
| `AZURE_VM_SSH_KEY` | Private key | Just updated above |

### Step 6: Test SSH Connection Manually

Before running GitHub Actions, test the key works:

**On your local machine:**

```bash
# Create a temporary test file
nano /tmp/test_key

# Paste the SAME private key you put in GitHub Secrets
# Save and exit (Ctrl+X, Y, Enter)

# Set permissions
chmod 600 /tmp/test_key

# Test connection with verbose output
ssh -i /tmp/test_key -v your-username@your-vm-ip

# If successful, you should be logged in!
# Exit and clean up
exit
rm /tmp/test_key
```

If this test succeeds, GitHub Actions should work too.

### Step 7: Test GitHub Actions

1. Make a small change to your repository
2. Commit and push:
   ```bash
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. Go to GitHub → **Actions** tab
4. Watch the deployment run

## Common Mistakes

### ❌ Key has a passphrase
GitHub Actions cannot use SSH keys with passphrases. Generate without passphrase (`-N ""`).

### ❌ Missing BEGIN/END lines
Make sure you copy the complete key including:
```
-----BEGIN OPENSSH PRIVATE KEY-----
-----END OPENSSH PRIVATE KEY-----
```

### ❌ Extra spaces or line breaks
Copy the key exactly as shown. No extra spaces before/after.

### ❌ Wrong key format
Some keys start with `-----BEGIN RSA PRIVATE KEY-----` instead of `-----BEGIN OPENSSH PRIVATE KEY-----`. 

If you have the old format, convert it:
```bash
ssh-keygen -p -f ~/.ssh/github_actions -m pem
```

### ❌ Public key not in authorized_keys
The public key MUST be in `~/.ssh/authorized_keys` on the VM.

### ❌ Wrong permissions
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## Alternative: Check Azure VM SSH Settings

### Enable SSH password authentication (temporary testing only)

```bash
# On Azure VM
sudo nano /etc/ssh/sshd_config

# Find and set:
PasswordAuthentication yes

# Restart SSH service
sudo systemctl restart sshd
```

Then add a GitHub secret `AZURE_VM_PASSWORD` and modify the workflow to use it temporarily.

**WARNING:** This is less secure. Switch back to key-based auth after testing.

## Debugging Tips

### Enable debug mode in GitHub Actions

Add to workflow:
```yaml
with:
  debug: true
```

### Check VM SSH logs

```bash
# On Azure VM
sudo tail -f /var/log/auth.log
# or
sudo journalctl -u ssh -f
```

Then trigger a deployment and watch for authentication attempts.

### Verify key fingerprint

```bash
# On Azure VM - get fingerprint of your key
ssh-keygen -l -f ~/.ssh/github_actions.pub

# On local machine - verify it matches
ssh-keygen -l -f /tmp/test_key
```

## Still Not Working?

### Check these:

1. **Azure NSG allows SSH**
   - Azure Portal → VM → Networking → Port 22 inbound allowed

2. **Correct username**
   - Common: `azureuser`, `ubuntu`, `admin`
   - Run `whoami` on VM to confirm

3. **VM is accessible**
   - Test: `ping your-vm-ip`
   - Test: `nc -zv your-vm-ip 22`

4. **GitHub Actions runner can reach your VM**
   - Make sure VM has a public IP
   - No firewall blocking GitHub IPs

## Quick Reference Commands

```bash
# Generate new key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions -N ""

# Add to authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Show private key (copy to GitHub)
cat ~/.ssh/github_actions

# Test connection
ssh -i /tmp/test_key your-username@your-vm-ip

# Check VM SSH logs
sudo tail -f /var/log/auth.log
```
