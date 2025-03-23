@echo off
cd /d %~dp0

:: 仮想環境を有効化（PowerShellじゃなく .bat を使うのがポイント！）
call venv\Scripts\activate.bat

:: アプリ起動
python app.py

pause
