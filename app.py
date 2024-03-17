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


app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
bq_dataset_id = 'your_dataset_id'
BQ_DATASET_ID = os.getenv('BQ_DATASET_ID', '')
BQ_TABLE_ID = os.getenv('BQ_TABLE_ID', '')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    # イベントから情報を取得
    user_id = event.message.user_id
    text = event.message.text
    reply_token = event.reply_token
    timestamp = event.timestamp
    response_text = f'{text}と言われましても'
    
    # BigQueryに挿入する行を準備
    row = [{
        'user_id': user_id,
        'message': text,
        'received_at': datetime.utcfromtimestamp(timestamp/1000).replace(tzinfo=pytz.utc),
    }]

    # データセットとテーブルの参照を作成
    table_ref = bq_client.dataset(BQ_DATASET_ID).table(BQ_TABLE_ID)

    # BigQueryにデータを挿入
    try:
        errors = bq_client.insert_rows_json(table_ref, [row])  # リスト内の単一の辞書を挿入
        if errors != []:
            print('Insert errors:', errors)
    except Exception as e:
        print(f'[ERROR] Failed to insert message into BigQuery: {e}')
        print(e)

    # 応答メッセージを実行
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=response_text)
        )
    except LineBotApiError as e:
        print(f'[ERROR] Failed to send reply message: {e.status_code} {e.error.message}')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
