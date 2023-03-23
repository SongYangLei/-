from websocket import WebSocketApp
import json
import re
import gzip
from urllib.parse import unquote_plus
import requests
import pandas as pd
from douyin_pb2 import PushFrame, Response, MemberMessage


def fetch_live_room_info(url):
    res = requests.get(
        url=url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        },
        cookies={
            "__ac_nonce": "063abcffa00ed8507d599"  # 可以是任意值
        }
    )
    data_string = re.findall(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', res.text)[0]
    data_dict = json.loads(unquote_plus(data_string))

    room_id = data_dict['app']['initialState']['roomStore']['roomInfo']['roomId']
    room_title = data_dict['app']['initialState']['roomStore']['roomInfo']["room"]['title']
    room_user_count = data_dict['app']['initialState']['roomStore']['roomInfo']["room"]['user_count_str']

    # print(room_id)
    wss_url = f'wss://webcast3-ws-web-hl.douyin.com/webcast/im/push/v2/?app_name=douyin_web&version_code=180800&webcast_sdk_version=1.3.0&update_version_code=1.3.0&compress=gzip&internal_ext=internal_src:dim|wss_push_room_id:7208711872101534522|wss_push_did:7206288423342458425|dim_log_id:2023031011394503018C4704AA8A020E99|fetch_time:1678419585802|seq:1|wss_info:0-1678419585802-0-0|wrds_kvs:InputPanelComponentSyncData-1678409093198179842_WebcastRoomRankMessage-1678419365150032503_WebcastRoomStatsMessage-1678419581114014797&cursor=t-1678419585802_r-1_d-1_u-1_h-1&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&debug=false&endpoint=live_pc&support_wrds=1&im_path=/webcast/im/fetch/&user_unique_id=7206288423342458425&device_platform=web&cookie_enabled=true&screen_width=1536&screen_height=864&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/110.0.0.0%20Safari/537.36%20Edg/110.0.1587.63&browser_online=true&tz_name=Asia/Shanghai&identity=audience&room_id=7208711872101534522&heartbeatDuration=0&signature=Wdp6afFS7LraKV69'

    ttwid = res.cookies.get_dict()['ttwid']
    return room_id, room_title, room_user_count, wss_url, ttwid


def on_open(ws):
    print('on_open')


def on_message(ws, content):
    frame = PushFrame()
    frame.ParseFromString(content)


    # 对PushFrame的 payload 内容进行gzip解压
    origin_bytes = gzip.decompress(frame.payload)

    # 根据Response+gzip解压数据，生成数据对象
    response = Response()
    response.ParseFromString(origin_bytes)

    if response.needAck:
        s = PushFrame()
        s.payloadType = "ack"
        s.payload = response.internalExt.encode('utf-8')
        s.logId = frame.logId

        ws.send(s.SerializeToString())

    # 获取数据内容（需根据不同method，使用不同的结构对象对 数据 进行解析）
    #   注意：此处只处理 WebcastChatMessage ，其他处理方式都是类似的。
    for item in response.messagesList:
        if item.method != "WebcastMemberMessage":
            continue

        message = MemberMessage()
        message.ParseFromString(item.payload)
        info = f"【{message.memberCount}】【】 "
        print(info)


def on_error(ws, content):
    print(content)
    print("on_error")


def on_close(*args, **kwargs):
    print(args, kwargs)
    print("on_close")


def run():
    web_url = "https://live.douyin.com/80017709309"


    room_id, room_title, room_user_count, wss_url, ttwid = fetch_live_room_info(web_url)


    print(room_id, room_title, room_user_count, wss_url, ttwid)

    ws = WebSocketApp(
        url=wss_url,
        header={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        },
        cookie=f"ttwid={ttwid}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()



if __name__ == '__main__':
    run()
