# 基本イメージを指定
FROM python:3.9-slim

# ログメッセージの即時表示設定
ENV PYTHONUNBUFFERED True

# ローカルコードをコンテナイメージにコピー
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# 依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# コンテナ起動時のコマンド
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app