#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tools
import time
import re
import db
import threading
import urllib.parse # 1. 新增了 urlparse 库

class Source (object) :
    def __init__ (self):
        self.T = tools.Tools()
        self.now = int(time.time() * 1000)
        self.siteUrl = str('http://m.iptv807.com/')

    def getSource (self) :
        # (此函数保持不变)
        urlList = []
        url = self.siteUrl
        req = [
            'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Mobile Safari/537.36',
        ]
        res = self.T.getPage(url, req)
        if res['code'] == 200 :
            pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">.*?<\/a><\/li>", re.I|re.S)
            postList = pattern.findall(res['body'])
            for post in postList :
                url = self.siteUrl + post
                req = [
                    'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                ]
                res = self.T.getPage(url, req)
                if res['code'] == 200 :
                    pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">(.*?)<\/a><\/li>", re.I|re.S)
                    channelList = pattern.findall(res['body'])
                    threads = []
                    for channel in channelList :
                        # 确保我们构造一个完整的 URL
                        if channel[0].startswith('http'):
                            channelUrl = channel[0]
                        else:
                            # 从 self.siteUrl 构建绝对URL
                            channelUrl = urllib.parse.urljoin(self.siteUrl, channel[0])

                        thread = threading.Thread(target = self.detectData, args = (channel[1], channelUrl, ), daemon = True)
                        thread.start()
                        threads.append(thread)
                    for t in threads:
                        t.join()
                else :
                    pass # MAYBE later :P

    # 2. 这是被完全重写的关键函数
    def detectData (self, title, url) :
        """
        新的数据检测函数，采用简化、正确的逻辑。
        """
        info = self.T.fmtTitle(title)

        # 步骤 1: 从URL中安全地提取 'id' 参数
        # 例如从 'http://m.iptv807.com/play.html?id==wJiFGR1' 中提取 '==wJiFGR1'
        try:
            parsed_url = urllib.parse.urlparse(url)
            channel_id = urllib.parse.parse_qs(parsed_url.query)['id'][0]
        except (KeyError, IndexError):
            self.T.logger(f"错误: 无法从URL [ {url} ] 中提取 'id'")
            return  # 如果URL格式不正确，则跳过

        self.T.logger(f"正在分析频道 [{info['title']}] (ID: {channel_id})")

        # 步骤 2: 直接调用 getRealUrl 函数进行解码
        m3u = self.T.getRealUrl(channel_id)

        # 步骤 3: 检查返回的m3u地址是否有效并处理
        if m3u and m3u.startswith('http'):
            netstat = self.T.chkPlayable(m3u)
            if netstat > 0:
                cros = 1 if self.T.chkCros(m3u) else 0
                data = {
                    'title'  : str(info['id']) if info['id'] != '' else str(info['title']),
                    'url'    : str(m3u),
                    'quality': str(info['quality']),
                    'delay'  : netstat,
                    'level'  : str(info['level']),
                    'cros'   : cros,
                    'online' : 1,
                    'udTime' : self.now,
                }
                self.addData(data)
                self.T.logger(f"添加成功 [ {info['title']} ]: {m3u}")
            else:
                self.T.logger(f"源不可用 [ {info['title']} ]: {m3u}")
        else:
            self.T.logger(f"解码失败 [{info['title']}]")

    def addData (self, data) :
        # (此函数保持不变)
        DB = db.DataBase()
        sql = "SELECT * FROM %s WHERE url = '%s'" % (DB.table, data['url'])
        result = DB.query(sql)
        if len(result) == 0 :
            data['enable'] = 1
            DB.insert(data)
        else :
            id = result[0][0]
            DB.edit(id, data)
