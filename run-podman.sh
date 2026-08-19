#!/bin/bash

# Podman management script for FAIRweaver
# Usage: ./run-podman.sh <env> <action>
#   env: prod | dev
#   action: start | stop | restart | status | logs

set -e

# Load environment variables
set -a
source .env || true
set +a

ENV=$1
ACTION=$2

if [ -z "$ENV" ] || [ -z "$ACTION" ]; then
    echo "Usage: $0 <prod|dev> <start|stop|restart|status|logs>"
    exit 1
fi

if [ "$ENV" != "prod" ] && [ "$ENV" != "dev" ]; then
    echo "Error: Environment must be 'prod' or 'dev'"
    exit 1
fi

REMOTE_USER="${PODMAN_SERVER_USER:-brizuela}"
REMOTE_HOST="${PODMAN_SERVER_HOST:-dmz-web-140.ipk-gatersleben.de}"
REMOTE_SSH="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_DIR="/tmp/fairweaver-deploy"

BACKEND_CONTAINER="fairweaver-backend-${ENV}"
FRONTEND_CONTAINER="fairweaver-frontend-${ENV}"

case $ACTION in
    start)
        echo "Starting FAIRweaver ${ENV} environment..."
        echo "Deploying to ${REMOTE_HOST}..."

        # Create remote directory and copy project files
        echo "Creating remote directory and copying files..."
        ssh "${REMOTE_SSH}" "mkdir -p ${REMOTE_DIR}"

        # Copy necessary files to remote server
        echo "Copying backend and frontend files..."
        scp -r backend frontend podman-compose.yml "${REMOTE_SSH}:${REMOTE_DIR}/"

        # Copy environment file (strip comments)
        echo "Copying environment variables..."
        grep -v '^#' .env | grep -v '^$' | ssh "${REMOTE_SSH}" "cat > ${REMOTE_DIR}/.env"

        if [ "$ENV" = "prod" ]; then
            ssh "${REMOTE_SSH}" "cd ${REMOTE_DIR} && podman-compose -f podman-compose.yml up -d backend-prod frontend-prod"
            echo "✓ Production environment started"
            echo "  Frontend: http://${REMOTE_HOST}:18080"
            echo "  Backend:  http://${REMOTE_HOST}:18000"
        else
            ssh "${REMOTE_SSH}" "cd ${REMOTE_DIR} && podman-compose -f podman-compose.yml up -d backend-dev frontend-dev"
            echo "✓ Development environment started"
            echo "  Frontend: http://${REMOTE_HOST}:28080"
            echo "  Backend:  http://${REMOTE_HOST}:28000"
        fi
        ;;

    stop)
        echo "Stopping FAIRweaver ${ENV} environment..."

        if [ "$ENV" = "prod" ]; then
            ssh "${REMOTE_SSH}" "cd ${REMOTE_DIR} && podman-compose -f podman-compose.yml down backend-prod frontend-prod"
            echo "✓ Production environment stopped"
        else
            ssh "${REMOTE_SSH}" "cd ${REMOTE_DIR} && podman-compose -f podman-compose.yml down backend-dev frontend-dev"
            echo "✓ Development environment stopped"
        fi
        ;;

    restart)
        echo "Restarting FAIRweaver ${ENV} environment..."
        $0 $ENV stop
        sleep 2
        $0 $ENV start
        ;;

    status)
        echo "FAIRweaver ${ENV} container status:"
        ssh "${REMOTE_SSH}" "podman ps --filter 'name=fairweaver-${ENV}' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
        ;;

    logs)
        if [ -z "$3" ]; then
            echo "Showing logs for both ${ENV} containers..."
            echo "=== Backend Logs ==="
            ssh "${REMOTE_SSH}" "podman logs ${BACKEND_CONTAINER}"
            echo ""
            echo "=== Frontend Logs ==="
            ssh "${REMOTE_SSH}" "podman logs ${FRONTEND_CONTAINER}"
        else
            CONTAINER="fairweaver-${3}-${ENV}"
            echo "Showing logs for $CONTAINER..."
            ssh "${REMOTE_SSH}" "podman logs ${CONTAINER}"
        fi
        ;;

    *)
        echo "Error: Unknown action '$ACTION'"
        echo "Valid actions: start, stop, restart, status, logs"
        exit 1
        ;;
esac