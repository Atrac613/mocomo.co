mocomo.co
=============

Google Buzz にポストされた内容を OAuth を使って Twitter に転送するスクリプトです。

Buzz からは PubSubHubbub 経由でデータが送られてきますのである程度リアルタイムに Twitter へ転送処理が行われます。

Buzz は Google の他のサービスとインテグレートされているので Picasa や YouTube などのアクティビティーの取り込みに便利です。

もともと Twitter から Buzz へ乗り換えて Twitter はサブのマイクロブログサービスとして使おうという試みのプロジェクトでしたが、Buzz がいつまで続くか分からないのでご利用は計画的に。。。

必要なもの
-------

1. Twitter の OAuth 各種キー。
2. Google Shortner API のキー。

使い方
-------

1. config.sample.py を config.py にコピー後必要項目を書き換えます。
2. app.yaml 内のアプリケーション名を適当なものに変更します。
3. GAE へデプロイします。
4. http://YOUR-APPS.appspot.com/home へアクセスします。
5. アプリオーナーアカウントでログインします。（デフォルトではオーナーのみ利用可能。）
6. config ページへ行き、Twitter 連携を行います。
7. Buzz Sync の Enable リンクをクリックします。
8. Buzz へ投稿し、Twitter へ転送されるか確認します。

-------

* デバッグ情報は GAE コンパネのログ画面より確認できます。
* Buzz から PubSubHubbub 経由で送られてくるデータは遅延する場合があります。

連絡先 & リポジトリ
-------

Source Code Repository: [mocomo.co - GitHub][mocomoco]

Twitter: [Atrac613][twitter]

[twitter]: http://twitter.com/Atrac613
[mocomoco]: https://github.com/Atrac613/mocomo.co

