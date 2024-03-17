# 標準ライブラリ
import os
import json
import hmac
import hashlib
from datetime import datetime
import pytz

# 関連するサードパーティのインポート
from flask import Flask, request, jsonify
from google.cloud import bigquery
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
PROJECT_ID = os.getenv('PROJECT_ID')
BQ_DATASET_NAME = os.getenv('BQ_DATASET_NAME', '')
BQ_TABLE_NAME = os.getenv('BQ_TABLE_NAME', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


app = Flask(__name__)
bq_client = bigquery.Client()


@app.route('/')
def home():
    return jsonify(message='success'), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print('Invalid signature. Please check your channel access token/channel secret.')
        return 'Invalid signature', 401

    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 現在時刻を取得（BigQuery に格納できる形式）
    now = datetime.now(pytz.timezone("Asia/Tokyo")).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    # イベントから情報を取得
    user_id = event.source.user_id
    text = event.message.text
    reply_token = event.reply_token
    response_text = f'{text}と言われましても'
    
    # BigQuery に挿入する行を準備
    row = [{
        'user_id': user_id,
        'user_message': text,
        'bot_response': response_text,
        'received_at': now,
    }]

    # テーブル参照を取得
    table_id = f"{PROJECT_ID}.{BQ_DATASET_NAME}.{BQ_TABLE_NAME}"
    table_ref = bq_client.get_table(table_id)

    # BigQuery にデータを挿入
    try:
        errors = bq_client.insert_rows(table_ref, row) 
        if errors:
            print('[ERROR] Failed to insert message into BigQuery', errors)
    except Exception as e:
        print(f'[ERROR] Failed to insert message into BigQuery: {e}')


    # LINE BOT へ応答メッセージを実行
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=response_text)
        )
    except LineBotApiError as e:
        print(f'[ERROR] Failed to send reply message: {e.status_code} {e.error.message}')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
