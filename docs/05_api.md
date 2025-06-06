# API構造と言語インタフェース

現時点でopen-mes-projectは主にWeb画面を通じた操作を前提としており、RESTfulな外部公開APIが整備されているかどうかは明確ではありません。しかし、将来的なIoT機器との連携や外部システムとのデータ連携を視野に入れており、リアルタイムのデータ収集や提供を行うAPIインタフェースを備える可能性があります
([prtimes.jp](https://prtimes.jp/main/html/rd/p/000000002.000134589.html))。Djangoは標準でURLルーティングとビューを通じてJSONやXMLの出力も可能なため、必要に応じてDjango REST Framework等を導入し、各機能モジュールに対応するAPIエンドポイントを用意する拡張も考えられます。

例えば、生産指示情報を外部の生産スケジューラから受け取るAPIや、実績データをIoTセンサーから受信するエンドポイント、在庫情報を社内の他システムへ提供するAPI等が想定できます。現状では未実装でも、オープンソースである強みを活かし、ユーザー企業やコミュニティが独自にAPIを追加することも可能です
([prtimes.jp](https://prtimes.jp/main/html/rd/p/000000001.000134589.html))。こうしたAPI拡張を行う場合でも、既存のDjangoプロジェクト構造に沿って、新たなURLルートとビュー（もしくはViewSet）を追加し、シリアライザを定義するといった一般的な手順で対応できます。

内部構造として、Djangoのビューは従来型のHTMLレンダリング用ビューとJSONなどを返すWeb API用ビューの両方を実装可能です。本プロジェクトにおいても、認証や主要データ取得の一部でAjax通信やAPI通信が行われているかもしれません。例えば、ダッシュボード画面でリアルタイムデータを表示する際、バックエンドから最新データを取得するためのJSON APIが用意されている可能性があります。このような部分的なAPIは、エンドユーザー向けUIの一部として実装されているケースも考えられます。