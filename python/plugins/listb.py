#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tools
import time
import re
import db
import threading
import urllib.parse

class Source (object) :
    def __init__ (self):
        self.T = tools.Tools()
        self.now = int(time.time() * 1000)
        self.siteUrl = str('http://m.iptv807.com/')
        self.T.logger("初始化 listb 插件...", new=True) # 清理并开始新的日志

    def getSource (self) :
        urlList = []
        url = self.siteUrl
        self.T.logger(f"开始抓取主页: {url}")
        req = [
            'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Mobile Safari/537.36',
        ]
        res = self.T.getPage(url, req)
        if res['code'] == 200 :
            self.T.logger("主页抓取成功。")
            pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">.*?<\/a><\/li>", re.I|re.S)
            postList = pattern.findall(res['body'])
            
            # --- 新增诊断日志 ---
            self.T.logger(f"在主页上找到 {len(postList)} 个分类页面。")
            if not postList:
                self.T.logger("!!! 警告: 未在主页上找到任何分类链接。请检查网站HTML结构或正则表达式(1)。")
                return # 如果没有分类，直接退出

            for i, post in enumerate(postList):
                cat_url = self.siteUrl + post
                self.T.logger(f"--- 正在处理分类 {i+1}/{len(postList)}: {cat_url} ---")
                req = [
                    'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                ]
                res = self.T.getPage(cat_url, req)
                if res['code'] == 200 :
                    self.T.logger(f"分类页面抓取成功。")
                    pattern = re.compile(r"<li><a href=\"(.*?)\" data-ajax=\"false\">(.*?)<\/a><\/li>", re.I|re.S)
                    channelList = pattern.findall(res['body'])
                    
                    # --- 新增诊断日志 ---
                    self.T.logger(f"在分类页面找到 {len(channelList)} 个频道。")
                    if not channelList:
                         self.T.logger(f"!!! 警告: 在分类页面 {cat_url} 未找到任何频道链接。请检查网站HTML结构或正则表达式(2)。")
                         continue # 继续处理下一个分类

                    threads = []
                    for channel in channelList :
                        if channel[0].startswith('http'):
                            channelUrl = channel[0]
                        else:
                            channelUrl = urllib.parse.urljoin(self.siteUrl, channel[0])

                        thread = threading.Thread(target = self.detectData, args = (channel[1], channelUrl, ), daemon = True)
                        thread.start()
                        threads.append(thread)
                    
                    self.T.logger(f"等待该分类下的 {len(threads)} 个线程处理完成...")
                    for t in threads:
                        t.join()
                    self.T.logger(f"该分类所有线程处理完毕。")
                else :
                    self.T.logger(f"!!! 错误: 抓取分类页面 {cat_url} 失败, 状态码: {res['code']}")
        else:
            self.T.logger(f"!!! 严重错误: 抓取主页 {url} 失败, 状态码: {res['code']}")

    def detectData (self, title, url) :
        info = self.T.fmtTitle(title)
        try:
            parsed_url = urllib.parse.urlparse(url)
            channel_id = urllib.parse.parse_qs(parsed_url.query)['id'][0]
        except (KeyError, IndexError):
            self.T.logger(f"错误: 无法从URL [ {url} ] 中为频道“{title}”提取 'id'")
            return

        self.T.logger(f"-> 正在分析频道 [{info['title']}] (ID: {channel_id})")
        m3u = self.T.getRealUrl(channel_id)

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
                self.T.logger(f"   [成功] [ {info['title']} ]: {m3u}")
            else:
                self.T.logger(f"   [源不可用] [ {info['title']} ]: {m3u}")
        else:
            self.T.logger(f"   [解码失败] [{info['title']}]")

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
