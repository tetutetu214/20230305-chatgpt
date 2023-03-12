import os
import sys
import logging
import openai

from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage)
from linebot.exceptions import (LineBotApiError, InvalidSignatureError)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

#環境変数からLINEBotのチャンネルアクセストークンとシークレットを読込
#環境変数からChatGpt APIの鍵を読込
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
openai.api_key = os.getenv("OPENAI_API_KEY")

#トークンが確認できない場合エラー出力
if channel_secret is None:
    logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

#apiとhandlerの生成（チャンネルアクセストークンとシークレットを渡す）
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

#Lambdaのメインの動作
def lambda_handler(event, context):

#認証用のx-line-signatureヘッダー
    signature = event["headers"]["x-line-signature"]
    body = event["body"]

#リターン値の設定
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}
    error_json = {"isBase64Encoded": False,
                  "statusCode": 500,
                  "headers": {},
                  "body": "Error"}

#LINEからのメッセージを ChatGPTに送信、受信したテキストをLINEで返信
    @handler.add(MessageEvent, message=TextMessage)
    def message(line_event):
        text = line_event.message.text

        completion = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
            {"role": "user", "content": text}
          ]
        )
  #受信したテキストをCloudWatchLogsに出力する
        print(completion.choices[0].message.content)
        text=completion.choices[0].message.content.lstrip()

        line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=text))

#例外処理としての動作
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json

    return ok_json