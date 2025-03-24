# 開発手順メモ

1. 仮想環境を有効化
   .\venv\Scripts\Activate.ps1

2. 必要なライブラリをインストール（初回だけ）
   pip install -r requirements.txt
   pip install flask-migrate

3. アプリ実行
   python app.py

4.アップデート用そのあと手動デプロイ
　　git add .
　　git commit -m "背番号検索修正"
　　git push