# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import json
import requests
import threading
import traceback
from flask import Flask, Response, request, render_template

# 导入所有插件
from plugins import base
from plugins import listb
from plugins import dotpy

# 定义文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
M3U_FILE = os.path.join(BASE_DIR, 'tv.m3u')
LOG_FILE = os.path.join(BASE_DIR, 'log.txt')

# Flask 应用
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, '../http'))

# 全局变量
IPTV_LIST =
LAST_UPDATE_TIME = 0
UPDATE_INTERVAL = 6 * 3600  # 6小时更新一次

class Iptv:
    def __init__(self):
        self.lock = threading.Lock()

    def getSource(self):
        global IPTV_LIST
        global LAST_UPDATE_TIME

        with self.lock:
            if time.time() - LAST_UPDATE_TIME < UPDATE_INTERVAL and IPTV_LIST:
                print("IPTV list is up-to-date, skipping update.")
                return

            print("Starting to collect IPTV sources...")
            new_iptv_list =

            # 只保留 listb 插件的调用，假设它处理 iptv807.com 的源。
            # 如果 iptv807.com 实际上是由 base 插件处理的，请取消注释 base.Source() 和 base.getSource()
            # 并注释掉 listb.Source() 和 listb.getSource()。
            try:
                listB = listb.Source()
                new_iptv_list.extend(listB.getSource())
                print(f"Collected {len(listB.getSource())} sources from listb.")
            except Exception as e:
                print(f"Error collecting sources from listb: {e}")
                traceback.print_exc()

            # 注释掉 base 插件的调用
            # try:
            #     Base = base.Source()
            #     new_iptv_list.extend(Base.getSource())
            #     print(f"Collected {len(Base.getSource())} sources from base.")
            # except Exception as e:
            #     print(f"Error collecting sources from base: {e}")
            #     traceback.print_exc()

            # 注释掉 dotpy 插件的调用
            # try:
            #     Dotpy = dotpy.Source()
            #     new_iptv_list.extend(Dotpy.getSource())
            #     print(f"Collected {len(Dotpy.getSource())} sources from dotpy.")
            # except Exception as e:
            #     print(f"Error collecting sources from dotpy: {e}")
            #     traceback.print_exc()

            IPTV_LIST = self.process_iptv_list(new_iptv_list)
            LAST_UPDATE_TIME = time.time()
            self.write_m3u_file()
            print(f"Total {len(IPTV_LIST)} unique IPTV sources collected and processed.")

    def process_iptv_list(self, raw_list):
        processed_list =
        seen_channels = set()

        for item in raw_list:
            if not isinstance(item, dict) or 'name' not in item or 'url' not in item:
                continue

            name = item['name'].strip()
            url = item['url'].strip()

            if not name or not url:
                continue

            # 简单的去重，可以根据需求增加更复杂的去重逻辑
            if (name, url) not in seen_channels:
                processed_list.append(item)
                seen_channels.add((name, url))
        return processed_list

    def write_m3u_file(self):
        with open(M3U_FILE, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for item in IPTV_LIST:
                f.write(f'#EXTINF:-1,{item["name"]}\n')
                f.write(f'{item["url"]}\n')
        print(f"M3U file written to {M3U_FILE}")

    def run_update_thread(self):
        def update_loop():
            while True:
                self.getSource()
                time.sleep(UPDATE_INTERVAL)
        thread = threading.Thread(target=update_loop)
        thread.daemon = True
        thread.start()

# Flask 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/m3u')
def get_m3u():
    if not IPTV_LIST or time.time() - LAST_UPDATE_TIME >= UPDATE_INTERVAL:
        # 如果列表为空或需要更新，则触发更新
        iptv_instance.getSource()
    
    try:
        with open(M3U_FILE, 'r', encoding='utf-8') as f:
            m3u_content = f.read()
        return Response(m3u_content, mimetype='application/x-mpegURL')
    except FileNotFoundError:
        return "M3U file not found. Please wait for the initial collection or check logs.", 404

@app.route('/channels')
def get_channels():
    if not IPTV_LIST or time.time() - LAST_UPDATE_TIME >= UPDATE_INTERVAL:
        iptv_instance.getSource()
    return Response(json.dumps(IPTV_LIST, ensure_ascii=False, indent=4), mimetype='application/json')

@app.route('/update')
def trigger_update():
    iptv_instance.getSource()
    return "Update triggered. Please check logs for progress.", 200

if __name__ == '__main__':
    iptv_instance = Iptv()
    iptv_instance.run_update_thread() # 启动后台更新线程
    app.run(host='0.0.0.0', port=9527)
