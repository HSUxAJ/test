import os
import sys
from argparse import ArgumentParser
from dotenv import load_dotenv

import asyncio
import aiohttp
from aiohttp import web

import logging

from aiohttp.web_runner import TCPSite

from linebot import (
    AsyncLineBotApi, WebhookParser
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, SourceGroup

import json

import random
import string
import re

load_dotenv()
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

class Handler:
    def __init__(self, line_bot_api, parser, line):
        self.line_bot_api = line_bot_api
        self.line = line
        self.parser = parser
        
    async def callback(self, request):
        signature = request.headers['X-Line-Signature']
        body = await request.text()

        try:
            events = self.parser.parse(body, signature)
        except InvalidSignatureError:
            return web.Response(status=400, text='Invalid signature')
        
        for event in events:
            logging.info("Handling event: %s", event)
            if isinstance(event, FollowEvent):
                await self.handle_follow(event)
            elif isinstance(event, MessageEvent):
                await self.handle_message(event)
        
        return web.Response(text="OK\n")

    async def handle_follow(self, event):
        pass

    async def handle_message(self, event):
        user_id = event.source.user_id
        self.line.push_message(user_id, TextMessage(text='123'))

async def main(port=8080):
    session = aiohttp.ClientSession()
    async_http_client = AiohttpAsyncHttpClient(session)
    line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
    parser = WebhookParser(channel_secret)
    line = LineBotApi(channel_access_token)

    handler = Handler(line_bot_api, parser, line)

    app = web.Application()
    app.add_routes([web.post('/callback', handler.callback)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = TCPSite(runner=runner, port=port)
    await site.start()

    while True:
        await asyncio.sleep(3600)  # sleep forever

if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8080, help='port')
    options = arg_parser.parse_args()

    asyncio.run(main(options.port))