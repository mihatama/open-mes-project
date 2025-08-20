FROM certbot/certbot

# NginxコンテナをリロードするためにDocker CLIをインストールします
# (証明書更新後のpost-hookで 'docker kill -s HUP ...' を実行するため)
RUN apk add --no-cache docker-cli