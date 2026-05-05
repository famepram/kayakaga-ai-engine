# Finai Agent - Docker Setup

Docker configuration untuk Finai Agent API service.

## 📁 File Structure

```
.
├── Dockerfile                 # Production Docker image
├── docker-compose.yml         # Production orchestration
├── docker-compose.dev.yml     # Development with hot-reload
├── .dockerignore             # Files to exclude from image
└── README.docker.md          # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Valid `.env` file dengan OPENROUTER_API_KEY

### Production Mode

```bash
# Build dan start semua services
docker-compose up -d

# Cek logs
docker-compose logs -f finai-agent

# Cek health
curl http://localhost:8000/health
```

### Development Mode (Hot Reload)

```bash
# Start dengan hot-reload enabled
docker-compose -f docker-compose.dev.yml up -d

# Code changes akan auto-reload
# Cek logs real-time
docker-compose -f docker-compose.dev.yml logs -f finai-agent
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file sebelum menjalankan:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Optional
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL=google/gemma-4-31b-it:free
```

### kayakaga-api Service

Update `docker-compose.yml` line 48-49 untuk kayakaga-api service:

```yaml
kayakaga-api:
  image: your-kayakaga-image:latest  # Ganti dengan image yang sesuai
  # Atau build dari local Dockerfile
  # build:
  #   context: ./kayakaga-api
  #   dockerfile: Dockerfile
```

## 📋 Docker Commands

### Basic Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs specific service
docker-compose logs -f finai-agent
```

### Build & Rebuild

```bash
# Build image
docker-compose build

# Rebuild tanpa cache
docker-compose build --no-cache

# Rebuild specific service
docker-compose build finai-agent
```

### Container Management

```bash
# List running containers
docker-compose ps

# Execute command in container
docker-compose exec finai-agent bash

# Check container health
docker-compose ps
```

### Cleanup

```bash
# Stop dan remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Complete cleanup
docker-compose down -v --rmi all --remove-orphans
```

## 🏥 Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Expected response
# {"status":"ok","service":"finai-agent-api"}

# Check Docker health status
docker-compose ps
```

## 🧪 Testing dengan Docker

```bash
# Test health check
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cek saldo semua akun",
    "conversation_history": [],
    "user_token": "your-jwt-token",
    "user_context": {
      "name": "Andi Pratama",
      "city": "Jakarta",
      "monthly_income": 12000000,
      "risk_profile": "undecided",
      "accounts": [
        {"name": "BCA", "balance": 12100000, "is_primary": true},
        {"name": "Jenius", "balance": 8300000, "is_primary": false},
        {"name": "GoPay", "balance": 3000000, "is_primary": false}
      ]
    }
  }'
```

## 🔍 Troubleshooting

### Container tidak bisa connect ke kayakaga-api

```bash
# Cek network
docker network ls
docker network inspect <network-name>

# Pastikan kedua services di network yang sama
docker-compose ps
```

### Environment variables tidak ter-load

```bash
# Cek environment di container
docker-compose exec finai-agent env | grep OPENROUTER

# Pastikan .env file ada dan format benar
cat .env
```

### Port conflict

```bash
# Cek port usage
netstat -tuln | grep 8000

# Atau gunakan port berbeda
docker-compose config | grep port
```

### Build errors

```bash
# Clear Docker cache
docker system prune -a

# Rebuild dari awal
docker-compose build --no-cache --pull
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Logs last 100 lines
docker-compose logs --tail=100

# Logs specific service
docker-compose logs -f finai-agent
```

### Resource Usage

```bash
# Container stats
docker stats finai-agent-api

# All services
docker-compose stats
```

## 🚀 Production Tips

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
   ```
3. **Use secrets** for sensitive data instead of environment variables
4. **Enable health checks** untuk semua services
5. **Use multi-stage build** untuk lebih kecil image size
6. **Set up logging driver** untuk production logs

## 📝 Notes

- Default port: 8000
- Network name: finai-network
- All services auto-restart unless stopped
- Health checks run setiap 30 detik
- Development mode supports hot-reload untuk code changes
