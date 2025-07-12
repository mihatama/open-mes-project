FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    sqlite3 \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定（以後の RUN は WORKDIR で実行）
WORKDIR /open_mes

# カレントディレクトリにある資産をコンテナ上の指定のディレクトリにコピーする
COPY ./requirements.txt .

# pipとsetuptoolsをアップグレードし、requirements.txtからパッケージをインストール
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

# 実行用のグループとユーザーを追加
RUN groupadd -g 1000 app_user
RUN useradd -m -s /bin/bash -u 1000 -g 1000 app_user