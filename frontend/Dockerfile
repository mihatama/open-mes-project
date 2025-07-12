# 公式のNode.jsランタイムを親イメージとして使用します
FROM node:22-alpine

# コンテナ内の作業ディレクトリを設定します
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピーします
# これを別のステップにすることで、Dockerのレイヤーキャッシュを活用できます
# これらのファイルが変更されない限り、npm installは再実行されません
COPY package*.json ./

# プロジェクトの依存関係をインストールします
RUN npm install

# アプリケーションのソースコードの残りをコピーします
COPY . .

# アプリケーションを起動するコマンド（Viteのデフォルト）
# --hostフラグを追加して、コンテナ外からアクセスできるようにします
CMD ["npm", "run", "dev", "--", "--host"]