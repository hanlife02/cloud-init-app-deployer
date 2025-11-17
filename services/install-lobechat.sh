#!/bin/bash
set -euo pipefail

INSTALL_DIR="${LOBECHAT_INSTALL_DIR:-/opt/lobechat}"
IMAGE="${LOBECHAT_IMAGE:-lobehub/lobe-chat:latest}"

mkdir -p "${INSTALL_DIR}"
cd "${INSTALL_DIR}"

cat > docker-compose.yml <<EOF
version: "3.8"
services:
  lobe-chat:
    image: "${IMAGE}"
    container_name: "lobe-chat"
    restart: "always"
    ports:
      - "0.0.0.0:3210:3210"
    environment:
      OPENAI_API_KEY: "${OPENAI_API_KEY:-}"
      OPENAI_PROXY_URL: "${OPENAI_PROXY_URL:-}"
      ACCESS_CODE: "${ACCESS_CODE:-}"
EOF

cat > auto-update-lobe-chat.sh <<'EOF'
#!/bin/bash
set -euo pipefail

INSTALL_DIR="${LOBECHAT_INSTALL_DIR:-/opt/lobechat}"
IMAGE="${LOBECHAT_IMAGE:-lobehub/lobe-chat:latest}"

cd "${INSTALL_DIR}"

output=$(docker pull "${IMAGE}" 2>&1 || true)

if echo "$output" | grep -q "Image is up to date"; then
  exit 0
fi

echo "Detected Lobe-Chat update"

docker rm -f lobe-chat >/dev/null 2>&1 || true

docker-compose up -d

echo "Update time: $(date)"
docker inspect "${IMAGE}" 2>/dev/null | grep 'org.opencontainers.image.version' || true

docker images | grep 'lobehub/lobe-chat' | grep -v 'latest' | awk '{print $3}' | xargs -r docker rmi >/dev/null 2>&1 || true
EOF

chmod +x auto-update-lobe-chat.sh

(crontab -l 2>/dev/null; echo '0 2 * * * LOBECHAT_INSTALL_DIR='"${INSTALL_DIR}"' /bin/bash '"${INSTALL_DIR}"'/auto-update-lobe-chat.sh >> /var/log/lobe-chat-update.log 2>&1') | crontab -

docker-compose up -d

