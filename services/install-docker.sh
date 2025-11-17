#!/bin/bash
set -euo pipefail

detect_os() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
      ubuntu) OS_TYPE="ubuntu" ;;
      debian) OS_TYPE="debian" ;;
      centos|rhel) OS_TYPE="centos" ;;
      *)
        echo "Unsupported OS: $ID"
        exit 1
        ;;
    esac
  else
    echo "Cannot detect OS (missing /etc/os-release)"
    exit 1
  fi
}

install_docker_ubuntu() {
  local mirror="${DOCKER_MIRROR:-https://mirrors.pku.edu.cn/docker-ce/linux/ubuntu}"
  apt-get update
  apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
  mkdir -p /etc/apt/keyrings
  curl -fsSL "${mirror}/gpg" | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] ${mirror} $(lsb_release -cs) stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io
  systemctl enable docker
  systemctl start docker
  if id ubuntu >/dev/null 2>&1; then
    usermod -aG docker ubuntu || true
  fi
  docker --version > /root/docker-version.txt 2>&1 || true
}

install_docker_debian() {
  local mirror="${DOCKER_MIRROR:-https://mirrors.pku.edu.cn/docker-ce/linux/debian}"
  apt-get update
  apt-get remove -y docker docker-engine docker.io containerd runc || true
  apt-get install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
  mkdir -p /etc/apt/keyrings
  curl -fsSL "${mirror}/gpg" | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] ${mirror} $(lsb_release -cs) stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce
  systemctl enable docker
  systemctl start docker
  if id debian >/dev/null 2>&1; then
    usermod -aG docker debian || true
  fi
  docker --version > /root/docker-version.txt 2>&1 || true
}

install_docker_centos() {
  local repo_url="${DOCKER_CENTOS_REPO:-http://mirrors.pku.edu.cn/repoconfig/docker-ce/docker-ce.repo}"
  yum install -y yum-utils device-mapper-persistent-data lvm2
  curl -fsSL "${repo_url}" -o /etc/yum.repos.d/docker-ce.repo
  yum makecache
  yum install -y docker-ce docker-ce-cli containerd.io
  systemctl enable docker
  systemctl start docker
  if id centos >/dev/null 2>&1; then
    usermod -aG docker centos || true
  fi
  docker --version > /root/docker-version.txt 2>&1 || true
}

main() {
  detect_os
  case "$OS_TYPE" in
    ubuntu)
      install_docker_ubuntu
      ;;
    debian)
      install_docker_debian
      ;;
    centos)
      install_docker_centos
      ;;
    *)
      echo "Unsupported OS_TYPE: $OS_TYPE"
      exit 1
      ;;
  esac
}

main "$@"

