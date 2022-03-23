#!/usr/bin/python3

import websocket
import time, json
from datetime import datetime, timezone, timedelta
import dateutil, calendar
from telethon import TelegramClient
import requests
import blocksmith, hashlib
import binascii
import pandas as pd
import string


botToken = 'YOUR_BOT_TOKEN'
gchatId = 'YOUR_CHANNEL_ID'

# default configuration
PBClientID = "YOUR_DEVICE_ID"
authBearer = "AUTH_BEARER"
myuid = "YOUR_ID_IN_PIXIE"
userAgent = "PxBee/1.0.7 (iOS; 15.3.1; en_US; iPhone14,4; network=WIFI; screen=375x812)"
set_timezone = "Asia/Jakarta"
min_power = 50

try:
    import thread
except ImportError:
    import _thread as thread

f = open("webSocketTester.log", "a")

msg = ""
old_msg = ""
old_post = ""
counter = 0

df = pd.DataFrame(columns=['date','postId','author','permlink'])

def on_message(ws, message):
    global df, counter

    try:    
        msg = json.loads(message)    
        #print(msg)
    except:
        ws = websocket.WebSocketApp("wss://ws.blockchain.info/inv",
                                  on_message = on_message,
                                  on_error = on_error,
                                  on_close = on_close,
                                  on_ping=on_ping,
                                  on_pong=on_pong
                                  )
        ws.on_open = on_open

    process_om(msg)
    counter = counter + 1

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        mes = {"op": "unconfirmed_sub"}
        ws.send(json.dumps(mes))        
    thread.start_new_thread(run, ())

def on_ping(ws, message):
    today = str(datetime.now())
    print("{} ### Got a Ping! ###".format(today))
    print(message)

def on_pong(ws, message):
    print("{} ### Send a Pong! ###".format(str(datetime.now())))
    print(message)

def process_om(data):        
    global df
    getFollower()
    getNewPost()

def postLike(author, permlink):
    uxt = getUnixTime()
    rand_str = string_generator()

    header = {
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "PBClientID": "{}".format(PBClientID),
        "api-version": "2",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en", 
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)
    }

    postData = {
        "appVersion": "1.0.7",
        "author": "{}".format(author),
        "country": "id",
        "deviceName": "iPhone14",
        "language": "en",
        "osVersion": "15.3.1",
        "permlink": "{}".format(permlink),
        "platform": "2",
        "timestamp": "{}".format(uxt),
        "timezone": "{}".format(set_timezone),
        "version": "2",
        "voter": "{}".format(myuid)
    }

    print("postData -> ",postData)

    url = "https://api.pixie.xyz/api/likes"
    postLike = requests.post(url, data=postData, headers=header)
    print("respon like -> ", postLike)
    #response = json.loads(postLike)
    #print("Post Like response -> ",response)
    return postLike

def getNewPost():
    global df, old_post
    rand_str = string_generator()
    curtime = getUnixTime()

    header = {
        "Connection": "keep-alive",
        "PBClientID": "{}".format(PBClientID),
        "api-version": "3", 
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(curtime),
        "Authorization": "bearer {}".format(authBearer)
    }

    url = "https://api.pixie.xyz/api/posts/new?appVersion=1.0.7&country=us&deviceName=iPhone14%2C4&language=en&limit=50&osVersion=15.3.1&platform=2&start_author=&start_permlink=&timestamp={}&timezone={}&version=2".format(curtime, set_timezone)
    
    #print(url)

    now_utc = datetime.utcnow()
    cur_date = now_utc.strftime('%Y-%m-%d')
    df_utc = now_utc.strftime('%Y%m%d')
    reset_time = now_utc.strftime('%H:%M')
    cur_time = now_utc.strftime('%H')
    start_time = now_utc.strftime('%H')
    end_time = now_utc.strftime('%H')

    dsave = datetime.strptime(df_utc, "%Y%m%d") - timedelta(days=1)           
    
    print("Jam (UTC) -> ",int(cur_time))
    print("Hibernate dari jam 03:00 UTC (10 WIB) mulai lagi nanti jam 00:00 UTC...")

    if 1 <= int(cur_time) <= 2:
        ret = requests.get(url,headers=header).content
        dt = json.loads(ret)

        if dt['status'] == True:
            ld = dt['data']['list']
            #print("data -> ", dt['data'])
            #print("list data -> ", ld)

            for post in ld:

                #print("post -> ", post)

                postId = post['postId']
                author = post['author']
                permlink = post['permlink']
                
                dict1 = {
                    "date": "{}".format(cur_date),
                    "postId": "{}".format(postId),
                    "author": "{}".format(author),
                    "permlink": "{}".format(permlink)
                }

                print("dict1 -> ", dict1)

                # reset data
                fn = 'pixie-'+str(df_utc)+'.csv'
                last_date = dsave.strftime('%Y%m%d')
                fn2 = 'pixie-'+str(last_date)+'.csv'
                if str(reset_time) == '02:50':
                    df.to_csv(fn)
                    df = pd.DataFrame(columns=['date','postId','author','permlink'])
                # end reset data
                
                #print("df -> ", df)
                
                energy = checkEnergy()
                power = energy['power']
                max_power = energy['max_power']
                print("power -> ", power)

                if min_power <= power <= max_power:
                    if old_post != postId:
                        djs = pd.DataFrame(dict1,columns=['date','postId','author','permlink'],index=[0]).rename_axis(columns='No')
                        if df.empty:
                            df = pd.concat([djs], ignore_index=True)
                        else:
                            isPostid = searchDataFrame(postId)
                            if isPostid.size <= 0:
                                df = pd.concat([df,djs], ignore_index=True)
                                print("start comment and like post...")
                                res_comment = likeAndComment(author, permlink)
                                print("Comment response -> ",res_comment)
                                time.sleep(5)
                                res_like = postLike(author, permlink)
                                print("Like post response -> ",res_like)
                                getFollower()
                        old_post = postId

                df.drop_duplicates()


def myAccount():
    uxt = getUnixTime()
    rand_str = string_generator()

    header = {
        "Connection": "keep-alive",
        "PBClientID": "{}".format(PBClientID), 
        "api-version": "2",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)
    }

    url = "https://api.pixie.xyz/api/account/user/{}?appVersion=1.0.7&country=us&deviceName=iPhone14%2C4&language=en&osVersion=15.3.1&platform=2&timestamp={}&timezone={}".format(myuid, uxt, set_timezone)

    ret = requests.get(url,headers=header).content
    dt = json.loads(ret)
    if dt['status'] == True:
        return dt['data']

def checkBalance():
    uxt = getUnixTime()
    rand_str = string_generator()

    header = {
        "Connection": "keep-alive",
        "PBClientID": "{}".format(PBClientID), 
        "api-version": "0",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)
    }

    url = "https://api.pixie.xyz/api/userinfo/money?account={}&appVersion=1.0.7&country=id&deviceName=iPhone14%2C4&language=en&osVersion=15.3.1&platform=2&timestamp={}&timezone={}".format(myuid, uxt, set_timezone)
    ret = requests.get(url,headers=header).content
    dt = json.loads(ret)
    if dt['status'] == True:
        return dt['data']
    

def getFollower():
    uxt = getUnixTime()
    rand_str = string_generator()

    header = {
        "Connection": "keep-alive",
        "PBClientID": "{}".format(PBClientID), 
        "api-version": "0",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)
    }

    url = "https://api.pixie.xyz/api/fans?appVersion=1.0.7&country=us&deviceName=iPhone14%2C4&following={}&language=en&limit=20&osVersion=15.3.1&platform=2&timestamp={}&timezone={}&version=1".format(myuid, uxt, set_timezone)
    ret = requests.get(url,headers=header).content
    dt = json.loads(ret)
    if dt['status'] == True:
        ld = dt['data']['list']
        for follower in ld:
            idFollower = follower['follower']
            if follower['isFollow'] == False:
                followUser(idFollower)


def followUser(uid):
    uxt = getUnixTime()
    rand_str = string_generator()

    header = {
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "PBClientID": "{}".format(PBClientID), 
        "api-version": "0",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)
    }

    postData = {
        "appVersion": "1.0.7",
        "country": "us",
        "deviceName": "iPhone14,4",
        "following": "{}".format(uid),
        "language": "en",
        "osVersion": "15.3.1",
        "platform": "2",
        "timestamp": "{}".format(uxt),
        "timezone": "{}".format(set_timezone)
    }

    url = "https://api.pixie.xyz/api/follow"
    postFollow = requests.post(url, data=postData, headers=header)
    print("Respon Follow -> ", postFollow)

def likeAndComment(author, permlink):
    uxt = getUnixTime()
    rand_str = string_generator()
    comment = "👋 Like 👍 my post and follow me and I’ll follow you 🔙, thanks 😏"
    comment_permlink= "{}-{}-{}".format("pxbee-comment", myuid, uxt)

    header = {
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "PBClientID": "{}".format(PBClientID),
        "api-version": "0",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)     
    }
    
    postData = {
        "appVersion": "1.0.7",
        "body": "{}".format(comment),
        "country": "id",
        "deviceName": "iPhone14,4",
        "language": "en",
        "osVersion": "15.3.1",
        "parent_author": "{}".format(author),
        "parent_permlink": "{}".format(permlink),
        "permlink": "{}".format(comment_permlink),
        "platform": "2",
        "timestamp": "{}".format(uxt),
        "timezone": "Asia/Jakarta"
    }

    url = "https://api.pixie.xyz/api/posts/comment"
    postComment = requests.post(url, data=postData, headers=header)
    print("Respon comment -> ", postComment)

def checkEnergy():
    uxt = getUnixTime()
    rand_str = string_generator()
    print(rand_str)
    header = {
        "Connection": "keep-alive",
        "PBClientID": "{}".format(PBClientID),
        "api-version": "0",
        "signature": "{}".format(rand_str),
        "Host": "api.pixie.xyz",
        "language": "en",
        "PBTaskID": "1",
        "User-Agent": "{}".format(userAgent),
        "timestamp": "{}".format(uxt),
        "Authorization": "bearer {}".format(authBearer)
    }
    url = "https://api.pixie.xyz/api/userinfo/power?appVersion=1.0.7&country=id&deviceName=iPhone14%2C4&language=en&osVersion=15.3.1&platform=2&timestamp={}&timezone={}".format(uxt, set_timezone)
    ret = requests.get(url,headers=header).content
    dt = json.loads(ret)
    if dt['status'] == True:
        return dt['data']

def string_generator(size=32):
    kg = blocksmith.KeyGenerator()
    kg.seed_input('{}'.format(getUnixTime()))
    key = kg.generate_key()    
    return key[0:size]

def getUnixTime():
    timezone_offset = +7.0 
    tzinfo = timezone(timedelta(hours=timezone_offset))
    dtt = datetime.now(tzinfo)
    uxtime = dtt.strftime('%Y-%m-%d %H:%M:%S')
    unixtime = time.mktime(dtt.timetuple()) * 1000    
    return round(unixtime)

def searchDataFrame(term):
    global df
    result = df.loc[df['postId'] == "{}".format(term)]
    print("searchDataFrame -> ", result)
    if result.size > 0:
        print("Found in DataFrame -> ", df)
        return df
    else: return result

def telegram_bot_sendtext(bot_message):    
    bot_token = botToken
    bot_chatID = gchatId
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()    

if __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://ws.blockchain.info/inv",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              on_ping=on_ping,
                              on_pong=on_pong
                              )
    ws.on_open = on_open
    
    keep_on = True
    while keep_on:
      try:
        ping_data = {"op": "ping"}
        keep_on = ws.run_forever(ping_interval=15, ping_payload=json.dumps(ping_data))
      except:
        print("[Websocket Error]")

    #ws.run_forever()
