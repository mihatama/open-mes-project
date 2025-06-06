# コードベースの構成と各ディレクトリの役割

本プロジェクトのリポジトリ構成は、Djangoプロジェクトの標準的なレイアウトに従いつつ、Docker運用に必要なファイルを含む形になっています。主要なディレクトリ・ファイルは以下の通りです。

- **`open_mes/`**: プロジェクトのメインディレクトリです。Djangoプロジェクトおよびアプリのコードが収められています。おそらくこの中に`manage.py`（Django管理コマンド起動スクリプト）や`settings.py`等の設定ファイル、`urls.py`（URLルーティング）、`wsgi.py`/`asgi.py`（サーバとのインターフェース）が配置されています。加えて、以下のサブディレクトリが存在します。
    - **`open_mes/base/`**: ベースアプリケーション。共通のモデルやテンプレート、サイト全体設定、ダッシュボード関連処理など、全モジュール横断的なコードを含みます。基本機能常備と説明されている部分に該当し、他の各アプリから参照される土台となります。マイグレーションも含まれ、初期データ投入（例えば基本的な選択肢マスタなど）を行う可能性があります。
    - **`open_mes/master/`**: マスタデータ管理用アプリ。製品マスタ、部品マスタ、工程マスタ、取引先マスタなど、製造プロセス全般に必要な基礎データを管理します。このアプリのモデルは他のアプリ（生産・在庫・品質など）から参照され、例えば製品マスタで定義した品目コードを生産管理や在庫管理で使用する、といった関係になります。
    - **`open_mes/production/`**: 生産管理アプリ。製造指示、作業オーダー、製造実績など生産に直接かかわるデータモデルおよびロジックを実装します。ビューとしては作業指示登録画面、進捗一覧、実績入力画面などが含まれるでしょう。進捗状況のトラッキングや製造オーダーと在庫引当のリンク機能など、本システムの中核的機能を担います。
    - **`open_mes/inventory/`**: 在庫管理アプリ。倉庫やロケーション、在庫品目、入庫（調達品や製造品の受け入れ）、出庫（製造使用や出荷）などのモデル・画面を提供します。在庫数の増減を管理し、在庫評価や欠品アラート等のロジックも将来的に含むかもしれません。生産管理や品質管理と連携し、在庫引当や検査中在庫の区別等も行える設計が考えられます。
    - **`open_mes/quality/`**: 品質管理アプリ。製品や部品の検査結果、不良内容、検査基準など品質に関するデータを扱います。品質検査の記録入力画面、不良分析のレポート、品質傾向チャート等の機能が該当します。品質情報は生産ロットや在庫品と紐づくため、他アプリのデータと関連するモデル設計になっているはずです。
    - **`open_mes/machine/`**: 設備管理アプリ。製造設備・機械に関する情報（設備マスタ、稼働ログ、メンテナンス履歴など）を管理します。例えば、設備ごとの稼働時間や故障履歴、保全スケジュールなどのモデルが含まれるでしょう。生産管理の製造実績と関連して、どのオーダーをどの設備で生産したかを記録したり、品質管理と連動して設備別の不良率を分析するなどの活用も可能です。
    - **`open_mes/users/`**: ユーザー管理アプリ。Djangoの認証システムを拡張またはラップし、システム利用者の管理を行います。カスタムUserモデル（例えばメールアドレスをユニークキーにする等）を定義している場合、この中に`models.py`があり、マイグレーションが行われます
      (github.com)。また、権限グループやアクセス制御に関するモデル（たとえばUserProfileやRoleモデル）を持つ可能性があります。ビューとしてはユーザー一覧・編集画面が管理者向けに提供され、ユーザー自身がパスワード変更等を行う画面も用意されるでしょう。
    - **`open_mes/image/`**: Dockerイメージ関連のファイルを格納したディレクトリです。ここにはアプリケーションコンテナを構築するための `Dockerfile` や `requirements.txt` が置かれています。例えば`requirements.txt`には本プロジェクトで必要となるPythonパッケージ一覧（Django本体、psycopg2など）が記載されています
      (github.com)。`Dockerfile`ではpythonベースイメージの上にこの`requirements.txt`をインストールし、コードを配置して`python manage.py runserver`等をCMDで起動する内容になっていると推測されます。開発者が依存ライブラリを追加した場合、この`requirements.txt`に追記しDockerイメージを再ビルドする必要があります。
    - （`open_mes/static/` や `open_mes/templates/` : 静的ファイルやテンプレートが共通配置されている可能性があります。Djangoでは各アプリ内に`templates`フォルダを持たせることもできますが、共通レイアウトなどをまとめるためプロジェクト直下に設置している場合もあります。）

- **`postgres/`**: PostgreSQL用の設定を収めたディレクトリです。Docker ComposeでPostgresサービスを立ち上げる際に、このディレクトリをマウントして初期設定を行うことがあります。例えば中に`init.sql`のようなファイルがあれば、データベースの初期化（ユーザー作成やデータ投入）を自動化しているかもしれません。環境変数でDBユーザ/パスワードを渡して公式Postgresイメージを利用する場合、本ディレクトリはほとんど空かもしれませんが、バックアップスクリプトや設定ファイル（`postgres.conf`の上書き等）が置かれている可能性もあります。

- **`script/`**: 補助的なスクリプト類を格納するディレクトリです。開発・デプロイの自動化やユーティリティのためにシェルスクリプトやPythonスクリプトが配置されます。例えば、開発環境セットアップ用のスクリプト（venv作成やDB起動チェックを行うもの）や、本番デプロイ時のCI/CDで用いるシェル（Dockerイメージビルド＆プッシュなど）、定期バッチ処理のサンプルコード等が含まれているかもしれません。現時点で具体的な内容は不明ですが、リポジトリ構成上重要ではない補助ファイルをまとめているディレクトリと言えます。

- **`README.md`**: リポジトリのReadme文書です。動作環境やセットアップ手順の概要が記載されており、開発者は最初に目を通すべき情報源となります。基本的なコマンドや`.env`サンプルもここに書かれており、本ドキュメントでも適宜参照しています。

- **`LICENSE`**: 本プロジェクトのライセンス情報です。MIT Licenseの下で公開されており、ソフトウェアを自由に利用・改変・再配布することが認められています
  (github.com)。商用利用も可能ですが、ライセンス条文に従い著作権表示等を残す必要があります。オープンソースとして利用者が安心して使えるよう、緩やかなMITライセンスが選択されています。

- **`.gitignore`**: Gitの不要ファイル除外設定です。`venv`ディレクトリやPyCache、環境設定ファイル（`.env`）などがここで除外指定されており、機密情報や生成物がリポジトリに含まれないようになっています。

以上が主な構成要素です。開発者はまず`open_mes/`以下のソースコードを読み、各アプリケーションのモデル・ビュー・テンプレートの関係を把握するとよいでしょう。特に`open_mes/settings.py`には`INSTALLED_APPS`として上記アプリが登録され、データベース設定や静的ファイル設定、認証設定（カスタムユーザー使用時の`AUTH_USER_MODEL`指定など）も記載されています。`open_mes/urls.py`を見ると、各アプリのURLルートが`include`されているはずなので、URLパターンから画面遷移を追うことも可能です。テンプレートは各app内または共通ディレクトリにあり、ベーステンプレート（レイアウト）やナビゲーションバー、各機能毎の画面（リスト表示、フォーム画面など）が用意されています。