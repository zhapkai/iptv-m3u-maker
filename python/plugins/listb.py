#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tools
import time
import re
import db
import threading
import os

class Source(object):
    def __init__(self):
        self.T = tools.Tools()
        self.now = int(time.time() * 1000)
        self.siteUrl = str('http://m.iptv807.com/')

    def getSource(self):
        self.T.logger(f"Starting getSource for {self.siteUrl}", new=True)
        urlList = []

        url = self.siteUrl
        req = [
            'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Mobile Safari/537.36',
        ]
        res = self.T.getPage(url, req)
        self.T.logger(f"Got response for {url}, code: {res['code']}")

        if res['code'] == 200:
            pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">.*?</a></li>", re.I|re.S)
            postList = pattern.findall(res['body'])
            self.T.logger(f"Found {len(postList)} post links")

            for post in postList:
                url = self.siteUrl + post
                req = [
                    'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                ]
                res = self.T.getPage(url, req)
                self.T.logger(f"Got response for {url}, code: {res['code']}")

                if res['code'] == 200:
                    pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">(.*?)<\/a><\/li>", re.I|re.S)
                    channelList = pattern.findall(res['body'])
                    self.T.logger(f"Found {len(channelList)} channels in {url}")
                    threads = []

                    for channel in channelList:
                        channelUrl = self.siteUrl + channel[0]
                        thread = threading.Thread(target=self.detectData, args=(channel[1], channelUrl,), daemon=True)
                        thread.start()
                        threads.append(thread)

                    for t in threads:
                        t.join()
                else:
                    self.T.logger(f"Failed to access {url}, code: {res['code']}")
        else:
            self.T.logger(f"Failed to access {self.siteUrl}, code: {res['code']}")

    def detectData(self, title, url):
        self.T.logger(f"Starting detectData for {title}, {url}")
        req = [
            'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        ]

        try:
            info = self.T.fmtTitle(title)
            self.T.logger(f"Formatted title: {info}")

            playInfo = self.T.getPage(url, req)
            if playInfo['code'] != 200:
                self.T.logger(f"Failed to access {url}, code: {playInfo['code']}")
                return

            pattern = re.compile(r"<option value=\"(.*?)\">.*?</option>", re.I|re.S)
            playUrlList = pattern.findall(playInfo['body'])
            self.T.logger(f"Found {len(playUrlList)} play URLs in {url}")

            if len(playUrlList) > 0:
                # 使用相对路径，基于 working-directory: python
                file_path = 'encrypted_urls.txt'
                self.T.logger(f"Attempting to write to: {file_path}")
                try:
                    with open(file_path, 'a', encoding='utf-8') as f:
                        for playUrl in playUrlList:
                            if playUrl.startswith('='):  # 仅保存加密数据
                                f.write(f"{playUrl}\n")
                                self.T.logger(f"Saved encrypted URL for {info['title']}: {playUrl}")
                    self.T.logger(f"Successfully saved encrypted URLs to {file_path}")
                except Exception as e:
                    self.T.logger(f"Failed to write to {file_path}: {str(e)}")
                self.T.logger(f"Encrypted URLs saved to {file_path}")
        except Exception as e:
            self.T.logger(f"Error in detectData for {title}, {url}: {str(e)}")

    def addData(self, data):
        DB = db.DataBase()
        sql = "SELECT * FROM %s WHERE url = '%s'" % (DB.table, data['url'])
        result = DB.query(sql)

        if len(result) == 0:
            data['enable'] = 1
            DB.insert(data)
        else:
            id = result[0][0]
            DB.edit(id, data)

if __name__ == '__main__':
    Source().getSource()
