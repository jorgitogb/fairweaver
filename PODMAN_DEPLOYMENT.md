# FAIRweaver Podman Deployment Guide

This guide covers deploying FAIRweaver using Podman on your production and development servers.

## Prerequisites

- Podman installed on your local machine and remote server
- SSH access to `dmz-web-140.ipk-gatersleben.de`
- OpenAI API key configured in `.env`

## Quick Setup

1. **Install dependencies:**
   ```bash
   sudo apt install podman podman-compose podman-docker
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run setup script:**
   ```bash
   ./setup-podman.sh
   ```

4. **Deploy environments:**
   ```bash
   # Development
   ./run-podman.sh dev start
   
   # Production  
   ./run-podman.sh prod start
   ```

## Available Scripts

### `./run-podman.sh <env> <action>`

**Environments:** `prod` | `dev`

**Actions:**
- `start` - Start all containers
- `stop` - Stop all containers  
- `restart` - Restart all containers
- `status` - Show container status
- `logs` - Show container logs

**Examples:**
```bash
./run-podman.sh dev start       # Start development
./run-podman.sh prod status     # Check production status
./run-podman.sh dev logs        # View dev logs
./run-podman.sh prod restart    # Restart production
```

### `./setup-podman.sh`

Initial setup script that:
- Checks podman installation
- Validates environment configuration
- Tests connection to remote podman server
- Provides deployment commands

## Environment Configuration

### Port Mapping

| Environment | Host Port | Container Port | URL |
|-------------|-----------|----------------|-----|
| Production  | 18080     | 80             | `http://dmz-web-140.ipk-gatersleben.de:18080` |
| Production  | 18000     | 8000           | `http://dmz-web-140.ipk-gatersleben.de:18000` |
| Development | 28080     | 80             | `http://dmz-web-140.ipk-gatersleben.de:28080` |
| Development | 28000     | 8000           | `http://dmz-web-140.ipk-gatersleben.de:28000` |

### Container Names

**Production:**
- `fairweaver-backend-prod` - Backend API server
- `fairweaver-frontend-prod` - Frontend web interface

**Development:**
- `fairweaver-backend-dev` - Backend API server  
- `fairweaver-frontend-dev` - Frontend web interface

## SSH Key Setup (Recommended)

For passwordless SSH access to remote podman server:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "fairweaver@local"

# Copy public key to remote server
ssh-copy-id brizuela@dmz-web-140.ipk-gatersleben.de

# Test connection
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman --version"
```

## Troubleshooting

### Cannot connect to remote podman server

1. **Test SSH connection:**
   ```bash
   ssh brizuela@dmz-web-140.ipk-gatersleben.de
   ```

2. **Check podman on remote server:**
   ```bash
   ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman ps"
   ```

3. **Verify network connectivity:**
   ```bash
   ping dmz-web-140.ipk-gatersleben.de
   ```

### Containers won't start

1. **Check logs:**
   ```bash
   ./run-podman.sh dev logs backend
   ./run-podman.sh dev logs frontend
   ```

2. **Check environment variables:**
   ```bash
   cat .env | grep -v "^#" | grep -v "^$"
   ```

3. **Verify podman-compose file:**
   ```bash
   podman-compose -f podman-compose.yml config
   ```

### Port conflicts

If you encounter port conflicts, modify ports in `podman-compose.yml`:
- Production: Change `18080` and `18000` to available ports
- Development: Change `28080` and `28000` to available ports

## Monitoring

### Check container status:
```bash
./run-podman.sh prod status
./run-podman.sh dev status
```

### View logs:
```bash
# All containers
./run-podman.sh prod logs

# Specific container
./run-podman.sh dev logs backend
./run-podman.sh dev logs frontend
```

### Monitor resources:
```bash
# On remote server
ssh brizuela@dmz-web-140.ipk-gatersleben.de "podman stats"
```

## Backup and Restore

### Backup data:
```bash
# Copy mappings directory
scp brizuela@dmz-web-140.ipk-gatersleben.de:/var/lib/containers/storage/volumes/fairweaver-mappings ./backup/
```

### Restore data:
```bash
# Restore mappings directory  
scp -r ./backup/* brizuela@dmz-web-140.ipk-gatersleben.de:/var/lib/containers/storage/volumes/fairweaver-mappings/
```

## Security Notes

⚠️ **Important:**
- The `.env` file contains sensitive credentials and should never be committed to git
- SSH keys provide more secure authentication than passwords
- Ensure firewall rules allow traffic on the specified ports
- Use HTTPS in production environments
- Regular update container images with `podman pull`

## Next Steps

1. Test the development environment first: `./run-podman.sh dev start`
2. Verify all services are running: `./run-podman.sh dev status`
3. Access the UI at `http://dmz-web-140.ipk-gatersleben.de:28080`
4. When satisfied, deploy to production: `./run-podman.sh prod start`

## Support

For issues or questions:
1. Check container logs: `./run-podman.sh <env> logs`
2. Review this deployment guide
3. Check main project README for architecture details