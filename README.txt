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
　　git commit -m "イベントにコメント追加"
　　git push

5.画像保存策
　　import cloudinary
import cloudinary.uploader

# Cloudinary設定
cloudinary.config(
    cloud_name="purofu",
    api_key="321378518641743",
    api_secret="wbr-PE9sGDB_KLurSKM3N9TafVQ"
)

#自動デプロイ
git add render.yaml
git commit -m "add render.yaml for migration"
git push