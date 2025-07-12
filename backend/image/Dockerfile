FROM python:3.11-buster

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python \
    sqlite3 \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの作成
RUN mkdir /open_mes

# カレントディレクトリにある資産をコンテナ上の指定のディレクトリにコピーする
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

# 実行用のグループとユーザーを追加
RUN groupadd -g 1000 app_user
RUN useradd -m -s /bin/bash -u 1000 -g 1000 app_user

# 作業ディレクトリの設定（以後の RUN は WORKDIR で実行）
WORKDIR /open_mes