# FAIRweaver Podman Deployment - Quick Reference

## Setup Commands

### 1. Install Podman (if not installed)
```bash
sudo apt update
sudo apt install podman podman-compose
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Setup SSH Keys (for passwordless access)
```bash
./setup-ssh.sh
```

### 4. Run Setup Script
```bash
./setup-podman.sh
```

## Deployment Commands

### Start Development Environment
```bash
./run-podman.sh dev start
# Access at: http://dmz-web-140.ipk-gatersleben.de:28080
```

### Start Production Environment
```bash
./run-podman.sh prod start
# Access at: http://dmz-web-140.ipk-gatersleben.de:18080
```

### Stop Environments
```bash
./run-podman.sh dev stop
./run-podman.sh prod stop
```

### Check Status
```bash
./run-podman.sh dev status
./run-podman.sh prod status
```

### View Logs
```bash
./run-podman.sh dev logs          # All containers
./run-podman.sh dev logs backend  # Specific container
./run-podman.sh dev logs frontend
```

## Makefile Targets

```bash
make podman-prod      # Start production (via Makefile)
make podman-dev       # Start development (via Makefile)
make podman-prod-stop # Stop production (via Makefile)
make podman-dev-stop  # Stop development (via Makefile)
```

## Container Management

### Check Remote Podman Status
```bash
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman ps"
```

### Check Remote Container Logs
```bash
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman logs fairweaver-backend-prod"
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman logs fairweaver-frontend-prod"
```

### Restart Specific Container
```bash
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman restart fairweaver-backend-prod"
```

## Troubleshooting

### Connection Issues
```bash
# Test SSH connection
ssh brizuela@dmz-web-140.ipk-gatersleben.de

# Test podman on remote server
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman --version"

# Check network connectivity
ping dmz-web-140.ipk-gatersleben.de
```

### Container Issues
```bash
# Check container logs
./run-podman.sh dev logs

# Restart containers
./run-podman.sh dev restart

# Remove and recreate containers
./run-podman.sh dev stop
podman-compose -f podman-compose.yml down
podman-compose -f podman-compose.yml up -d
```

### Port Conflicts
```bash
# Check what's using ports
ssh brizuela@dmz-web-140.ipk-gatersleben.de "netstat -tulpn | grep -E ':(18000|18080|28000|28080)'"

# Modify ports in podman-compose.yml if needed
```

## File Structure

```
fairweaver/
├── backend/
│   ├── Containerfile           # Podman build file
│   ├── Dockerfile              # Docker build file (kept for compatibility)
│   └── mappings/               # Shared data volume
├── frontend/
│   ├── Containerfile           # Podman build file
│   ├── Dockerfile              # Docker build file (kept for compatibility)
│   └── nginx.conf              # Nginx configuration
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── podman-compose.yml          # Podman compose configuration
├── docker-compose.yml          # Docker compose configuration (original)
├── run-podman.sh               # Podman management script
├── setup-podman.sh             # Initial setup script
├── setup-ssh.sh                # SSH key setup script
├── PODMAN_DEPLOYMENT.md        # Detailed deployment guide
└── QUICK_REFERENCE.md          # This file
```

## Ports Summary

| Environment | Service | Host Port | Container Port | URL |
|-------------|---------|-----------|----------------|-----|
| Production | Frontend | 18080 | 80 | `http://dmz-web-140.ipk-gatersleben.de:18080` |
| Production | Backend | 18000 | 8000 | `http://dmz-web-140.ipk-gatersleben.de:18000` |
| Development | Frontend | 28080 | 80 | `http://dmz-web-140.ipk-gatersleben.de:28080` |
| Development | Backend | 28000 | 8000 | `http://dmz-web-140.ipk-gatersleben.de:28000` |

## Next Steps

1. **First deployment:** Start with development environment
   ```bash
   ./run-podman.sh dev start
   ```

2. **Verify deployment:** Check all containers running
   ```bash
   ./run-podman.sh dev status
   ```

3. **Test application:** Access frontend URL
   ```
   http://dmz-web-140.ipk-gatersleben.de:28080
   ```

4. **Production rollout:** When satisfied, deploy to production
   ```bash
   ./run-podman.sh prod start
   ```

5. **Monitor production:** Check logs and status regularly
   ```bash
   ./run-podman.sh prod status
   ./run-podman.sh prod logs
   ```