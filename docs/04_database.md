# データベース構成

PostgreSQLが本システムのリレーショナルデータベースとして使用されています
([github.com](https://github.com/mihatama/open-mes-project))。DjangoのORM（Object-Relational Mapping）を通じてモデルとテーブルのマッピングが行われ、各機能モジュールに対応するテーブル群が自動生成・管理されます。データベース名や接続情報は環境変数で設定され、デフォルトでは下記のような構成となっています
([github.com](https://github.com/mihatama/open-mes-project/blob/main/README.md?plain=1#L103-L112))：

- エンジン: `django.db.backends.postgresql` (PostgreSQLデータベースエンジン)
  (github.com)
- データベース名: `open_mes`
  (github.com)
- ユーザー名: `django`
  (github.com)
- パスワード: `django`
  (github.com)
- ホスト: `postgres` (Dockerコンテナ名。通常はDocker Compose設定によりPostgreSQLコンテナをpostgresという名前で起動)
  (github.com)
- ポート: `5432`（PostgreSQLのデフォルトポート）
  (github.com)

初回セットアップ時には、データベースにテーブルを作成するため マイグレーション を実行する必要があります
(github.com)。各アプリケーション（base, inventory, machine, master, production, quality, users）のモデル定義に基づきテーブルやインデックスが生成されます。例えば生産管理モジュールでは「製造オーダーテーブル」「製造履歴テーブル」等、在庫管理では「在庫マスタ」「入出庫履歴テーブル」等、品質管理では「検査結果テーブル」等といった具合に、機能に沿ったエンティティがデータベース上に構築されます。それらは外部キーで相互参照され、前述のようにモジュール間のデータ連携を実現します。

データベースの初期スキーマ構築後、管理者ユーザーを作成することで基本的なデータが投入されます（管理者の作成自体はユーザーテーブルへのレコード挿入です）
(github.com)。その後は、ユーザーがシステム上から入力する各種情報（生産指示、在庫登録、検査結果入力など）がリアルタイムにデータベースへ保存され、必要に応じて参照・更新されます。なお、PostgreSQLを使用していることで大量データの扱いやトランザクション管理、ストアドプロシージャ等の高度な機能も利用可能です。将来的にデータ量が膨大になった場合でも、PostgreSQLのチューニングやスケーリングによって性能確保が図れる設計になっています。

## 環境設定 (.env)
データベース接続情報やDjangoのセキュリティキー、デバッグ設定などは環境変数として管理します。プロジェクトルートに配置する `.env` ファイルに以下のような内容を記述して設定します
(github.com)
(github.com)。

```env
SECRET_KEY= # (Djangoの秘密鍵をここに記載)      # セキュリティキー。初回生成したランダムな値
DEBUG=True                                # 開発環境ではTrue、本番ではFalse推奨
ALLOWED_HOSTS=*                           # 許可するホスト名。開発用途ではワイルドカード指定
# CSRFを許可するオリジン。フロントエンドのURLをスキーマ(http/https)から指定します。
CSRF_TRUSTED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"

DB_ENGINE=django.db.backends.postgresql   # 使用DBエンジン（PostgreSQL）
DB_NAME=open_mes                         # データベース名
DB_USER=django                           # DBユーザー名
DB_PASSWORD=django                       # DBパスワード
DB_HOST=postgres                         # DBホスト（Dockerコンテナ名）
DB_PORT=5432                             # DBポート
```

`SECRET_KEY`（Djangoの`SECRET_KEY`）は、プロジェクト初回セットアップ時に自動生成することが可能です。開発者は以下のコマンドでランダムな`SECRET_KEY`文字列を取得し、`.env`にコピーできます
(github.com)。

```bash
docker compose exec -it open_mes python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
上記コマンドはDockerコンテナ内でDjangoのユーティリティを用いて安全なキーを生成するものです
(github.com)。