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
                playUrl = playUrlList[0]
                # 确保文件路径正确（相对于 python 目录）
                file_path = os.path.join(os.path.dirname(__file__), 'encrypted_urls.txt')
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{playUrl}\n")
                self.T.logger(f"Saved encrypted URL for {info['title']}: {playUrl}")

                # 注释掉后续处理，等待解密
                # midM3uInfo = self.T.getPage(playUrl, req)
                # pattern = re.compile(r"url: '(.*?)',", re.I|re.S)
                # midM3uUrlList = pattern.findall(midM3uInfo['body'])
                # if len(midM3uUrlList) > 0:
                #     midM3uUrl = midM3uUrlList[0]
                #     if midM3uUrl != '':
                #         m3u = self.T.getRealUrl(midM3uUrl)
                #         try:
                #             m3u.index('migu.php?token=')
                #         except:
                #             if m3u != '':
                #                 netstat = self.T.chkPlayable(m3u)
                #             else:
                #                 netstat = 0
                #             if netstat > 0:
                #                 cros = 1 if self.T.chkCros(m3u) else 0
                #                 data = {
                #                     'title': str(info['id']) if info['id'] != '' else str(info['title']),
                #                     'url': str(m3u),
                #                     'quality': str(info['quality']),
                #                     'delay': netstat,
                #                     'level': str(info['level']),
                #                     'cros': cros,
                #                     'online': 1,
                #                     'udTime': self.now,
                #                 }
                #                 self.addData(data)
                #                 self.T.logger('正在分析[ %s ]: %s' % (str(info['id']) + str(info['title']), m3u))
                #             else:
                #                 pass
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
