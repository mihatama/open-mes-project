# open-mes-project

## 詳細ドキュメント

Open MES Project (みんなのMES) の詳細な技術ドキュメントやガイドラインは、[こちら (`docs/README.md`)](./docs/README.md) を参照してください。
これらのドキュメントは `docs` ディレクトリに格納されています。

### 目次

#### 1. プロジェクト概要とアーキテクチャ
- プロジェクト紹介
- システムアーキテクチャ

#### 2. 機能と技術スタック
- 主要機能とモジュール
- 使用言語・フレームワーク・ライブラリ
- データベース構成
- API構造と言語インタフェース

#### 3. 導入ガイド
- 開発・実行環境の前提条件
- セットアップ手順
- トラブルシューティング

#### 4. 開発者向けドキュメント
- コードベースの構成
- 開発フローとブランチ戦略
- テスト方法
- CI/CD パイプライン
- 機能拡張の指針
- クラス構造

---

## 動作推奨環境

**推奨OS:** Ubuntu

**推奨環境:**

1.  **Ubuntu Server 24.04 LTS (最新版):** 本番環境での運用に最適です。安定性とセキュリティに優れており、サーバー用途に特化した機能が充実しています。
2.  **Ubuntu Desktop 24.04 LTS (最新版):** 開発環境やテスト環境として利用できます。デスクトップ環境が必要な場合に適しています。

**必須ソフトウェア:**

*   **Docker:** コンテナ化された環境でアプリケーションを実行するために必要です。
*   **Docker Compose:** 複数のDockerコンテナを定義し、管理するためのツールです。
*   **PostgreSQL:** データベースとして使用します。

**備考:** 上記以外のOSでも動作する可能性がありますが、検証は行っておりません。

## テスト実行環境の構築(windows)
`start.bat` は、Windows上で開発・テスト環境を簡単にセットアップし、アプリケーションを起動するためのバッチスクリプトです。

**前提条件:**
*   Windows OS。
*   Python 3.11 がインストールされ、システムのPATHに追加されていること (Pipも同様に利用可能であること)。
*   プロジェクトファイルがローカルに展開されていること (例: Gitクローン)。

**実行方法:**
1.  コマンドプロンプトまたはPowerShellを開きます。
2.  プロジェクトのルートディレクトリ (<code>start.bat</code> ファイルがあるディレクトリ) に移動します。
3.  以下のコマンドを実行します:
    ```bat
    start.bat
    ```

**初回実行時の主な動作:**
スクリプトは対話形式で進行し、以下の処理を自動または確認を求めながら行います。
*   PythonおよびPipのバージョンを確認します。
*   プロジェクトルートに `venv` という名前でPython仮想環境を作成し、有効化します。
*   <code>image/requirements.txt</code> に基づいて必要なライブラリをインストールします。
    *   これにはPostgreSQL用の `psycopg2` も含まれます。もし `psycopg2` のインストールでエラーが発生した場合、PostgreSQLクライアントライブラリのインストールや、Microsoft Visual C++ Build Toolsが必要になることがあります。スクリプト内の指示や、<code>requirements.txt</code> を編集して `psycopg2-binary` を使用することも検討してください。
*   <code>scr</code> ディレクトリに <code>.env</code> ファイルが存在しない場合、SQLiteをデフォルトのデータベースとして設定し、一意の `SECRET_KEY` を自動生成してファイルを作成します。
*   作成された <code>.env</code> ファイルの内容 (特に `SECRET_KEY` やデータベース設定) を確認し、必要に応じて修正するよう促されます (スクリプトが一時停止します)。
*   Djangoのデータベースマイグレーションを実行します (デフォルトのSQLiteの場合、<code>scr</code> ディレクトリ近辺に `db.sqlite3` ファイルが生成されることがあります)。
*   Django管理サイトにアクセスするためのスーパーユーザーを作成するかどうかを尋ねられます。
*   セットアップが完了したことを示すフラグファイル (<code>venv\.setup_complete</code>) を作成し、次回以降の起動時に初期セットアップ手順をスキップします。

**2回目以降の実行時の主な動作:**
*   仮想環境を有効化します。
*   Djangoのデータベースマイグレーションを実行します。
*   Django開発サーバーを起動します (通常、ブラウザで <code>http://127.0.0.1:8000</code> からアクセスできます)。

**重要な注意点:**
*   スクリプトの指示に従って操作してください。特に <code>.env</code> ファイルの設定確認は重要です。
*   デフォルトはSQLiteですが、PostgreSQLを使用したい場合は、<code>start.bat</code> が <code>.env</code> ファイルを作成した後 (またはスクリプトの一時停止中に)、<code>scr/.env</code> ファイル内のデータベース関連の設定 (<code>DB_ENGINE</code>, <code>DB_NAME</code>, <code>DB_USER</code>, <code>DB_PASSWORD</code>, <code>DB_HOST</code>, <code>DB_PORT</code>) を適切に変更してください。PostgreSQLサーバーが稼働していることも確認が必要です。
*   開発サーバーを停止するには、<code>start.bat</code> を実行しているコンソールウィンドウで `Ctrl+C` を押してください。
*   このスクリプトは、プロジェクトのルートディレクトリから実行されることを想定しています。

---

## 開発環境の構築
venvで使用するライブラリを入れることをおすすめします。
使用するコマンド
```

sudo apt update
sudo apt install libpq-dev


# venvが入っていない場合
sudo apt install python3-venv

# 仮想環境に入る
source venv/bin/activate

# ライブラリインストール
pip install -r ./open_mes/image/requirements.txt

```
## buildコマンド
```
docker compose run --rm frontend npm run build
docker compose -f compose.yml run --rm frontend npm run build
```

## 初回は下記コマンドを実行
```
docker compose run -it --rm backend python3 manage.py migrate
docker compose -f compose.yml run -it --rm backend python3 manage.py migrate
```
## 管理者を登録
```
docker compose exec -it backend python3 manage.py createsuperuser
docker compose run -it --rm backend python3 manage.py createsuperuser
docker compose -f compose.yml run -it --rm backend python3 manage.py createsuperuser
```

## .envファイルのサンプル

下記コマンドでセキュリティキーを再発行する
```
docker compose exec -it backend python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
.env
```
SECRET_KEY=(生成したセキュリティキーをここに記載する)

DEBUG=True

ALLOWED_HOSTS=*
# フロントエンドやリバースプロキシが動作するオリジン(スキーマ+ホスト+ポート)をカンマ区切りで指定します。
# 例: "http://localhost:3000,http://127.0.0.1:8000,https://your-domain.com"
CSRF_TRUSTED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"

DATABASE_URL=postgres://django:django@db:5432/open_mes

```