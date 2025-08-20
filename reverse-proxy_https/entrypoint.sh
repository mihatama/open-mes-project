#!/bin/sh

# 環境変数が設定されているか確認
if [ -z "$DOMAIN" ]; then
  echo "DOMAIN environment variable is not set."
  exit 1
fi

CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
OPTIONS_SSL_CONF="/etc/letsencrypt/options-ssl-nginx.conf"
SSL_DHPARAMS="/etc/letsencrypt/ssl-dhparams.pem"

# 証明書が存在しない場合、ダミーの自己署名証明書を作成
if [ ! -f "${CERT_DIR}/fullchain.pem" ] || [ ! -f "${CERT_DIR}/privkey.pem" ]; then
  echo "### Creating dummy certificate for ${DOMAIN} ..."
  mkdir -p "${CERT_DIR}"
  openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}"
fi

# options-ssl-nginx.conf が存在しない場合、推奨設定を書き込む
if [ ! -f "${OPTIONS_SSL_CONF}" ]; then
  echo "### Creating dummy options-ssl-nginx.conf ..."
  mkdir -p /etc/letsencrypt
  echo '
ssl_session_cache shared:le_nginx_SSL:10m;
ssl_session_timeout 1440m;
ssl_session_tickets off;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384";
' > "${OPTIONS_SSL_CONF}"
fi

# ssl-dhparams.pem が存在しない場合、生成する (初回起動時に時間がかかる場合があります)
if [ ! -f "${SSL_DHPARAMS}" ]; then
  echo "### Creating ssl-dhparams.pem ..."
  openssl dhparam -out "${SSL_DHPARAMS}" 2048
fi