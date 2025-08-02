#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tools
import time
import re
import db
import threading

class Source (object) :
    def __init__ (self):
        self.T = tools.Tools()
        self.now = int(time.time() * 1000)
        self.siteUrl = str('http://m.iptv807.com/')

    def getSource (self) :
        urlList = []
        url = self.siteUrl
        req = [
            'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        ]
        res = self.T.getPage(url, req)
        if res['code'] == 200 :
            pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">.*?<\/a><\/li>", re.I|re.S)
            postList = pattern.findall(res['body'])
            for post in postList :
                url = self.siteUrl + post
                req = [
                    'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                ]
                res = self.T.getPage(url, req)
                if res['code'] == 200 :
                    pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">(.*?)<\/a><\/li>", re.I|re.S)
                    channelList = pattern.findall(res['body'])
                    threads = []
                    for channel in channelList :
                        channelUrl = self.siteUrl + channel[0]
                        # 使用多线程处理，对 self.detectData 的调用保持不变
                        thread = threading.Thread(target = self.detectData, args = (channel[1], channelUrl, ), daemon = True)
                        thread.start()
                        threads.append(thread)
                    for t in threads:
                        t.join()
                else :
                    pass # MAYBE later :P

    def detectData (self, title, url) :
        req = [
            'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        ]
        info = self.T.fmtTitle(title)
        playInfo = self.T.getPage(url, req)
        pattern = re.compile(r"<option value=\"(.*?)\">.*?<\/option>", re.I|re.S)
        playUrlList = pattern.findall(playInfo['body'])

        if len(playUrlList) > 0 :
            playUrl = playUrlList[0]
            m3u = "" # 初始化最终的m3u变量

            # ==================== 【核心修改区域开始】 ====================
            # 我们将用下面的智能判断逻辑替换掉原来写死的 "if not playUrl.startswith('http')"
            
            self.T.logger(f"开始处理频道 '{title}', 获取到原始 playUrl: {playUrl[:70]}...")

            # 【新增逻辑】: 判断是否是我们的加密格式
            if playUrl.startswith("="):
                self.T.logger(f"检测到加密链接, 调用解码函数...", level="INFO")
                # 直接调用解码函数得到最终m3u地址
                m3u = self.T.getRealUrl(playUrl)

            # 【保留原有逻辑】: 如果是http开头的，说明是旧格式，需要访问页面再提取
            elif playUrl.startswith("http"):
                self.T.logger(f"检测到标准链接, 准备访问中间页...", level="INFO")
                try:
                    midM3uInfo = self.T.getPage(playUrl, req)
                    # 从返回的页面中用正则提取 'url: ...'
                    pattern = re.compile(r"url: '(.*?)',", re.I|re.S)
                    midM3uUrlList = pattern.findall(midM3uInfo['body'])
                    if len(midM3uUrlList) > 0 :
                        # 提取到的这个就是最终的m3u地址
                        m3u = midM3uUrlList[0]
                    else:
                        self.T.logger(f"在页面 {playUrl} 中未找到 'url: ...' 格式的链接", level="WARNING")
                except Exception as e:
                    self.T.logger(f"[ERROR] 获取 {playUrl} 失败: {e}", level="ERROR")
                    return # 出错则直接返回

            # 【新增逻辑】: 处理未知格式的URL
            else:
                self.T.logger(f"[跳过未知格式的URL] {title} -> {playUrl}", level="WARNING")
                return # 跳过并返回

            # ==================== 【核心修改区域结束】 ====================

            # 下面的代码是公用的，无论m3u是通过哪种方式获取的，都会经过这里的检查
            if m3u and m3u.strip() != '':
                # 过滤掉一个已知的无效链接模式
                if 'migu.php?token=' in m3u:
                    return

                netstat = self.T.chkPlayable(m3u)
                if netstat > 0 :
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
                    # 日志记录修改，使用 T.logger
                    self.T.logger('分析成功 [ %s ]: %s' % (str(info['id']) + str(info['title']), m3u), level="SUCCESS")
                else :
                    pass # 不可用的链接，不做处理
            else:
                self.T.logger(f"未能获取到有效的 m3u 链接: 频道 '{title}'", level="DEBUG")

    def addData (self, data) :
        DB = db.DataBase()
        sql = "SELECT * FROM %s WHERE url = '%s'" % (DB.table, data['url'])
        result = DB.query(sql)
        if len(result) == 0 :
            data['enable'] = 1
            DB.insert(data)
        else :
            id = result[0][0]
            DB.edit(id, data)
