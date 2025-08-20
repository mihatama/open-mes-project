FROM nginx:latest

# opensslをインストール
RUN apt-get update && apt-get install -y openssl curl && rm -rf /var/lib/apt/lists/*

# 起動スクリプトをコピー
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Nginx設定テンプレートをコピー
COPY ./default.conf.template /etc/nginx/templates/default.conf.template
