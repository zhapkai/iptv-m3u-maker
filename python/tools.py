#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import urllib.error
import re
import ssl
import io
import gzip
import random
import socket
import time
import area
import os
import base64

socket.setdefaulttimeout(5.0)

class Tools (object) :
    def __init__ (self) :
        # 初始化日志文件
        self.logger("====== Script Start / New Run ======", new=True)
        pass

    def getPage (self, url, requestHeader = [], postData = {}) :
        fakeIp = self.fakeIp()
        requestHeader.append('CLIENT-IP:' + fakeIp)
        requestHeader.append('X-FORWARDED-FOR:' + fakeIp)
        if postData == {} :
            request = urllib.request.Request(url)
        elif isinstance(postData, str) :
            request = urllib.request.Request(url, postData)
        else :
            request = urllib.request.Request(url, urllib.parse.urlencode(postData).encode('utf-8'))
        for x in requestHeader :
            headerType = x.split(':')[0]
            headerCon = x.replace(headerType + ':', '')
            request.add_header(headerType, headerCon)
        try :
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urllib.request.urlopen(request, context = ctx)
            header = response.headers
            body = response.read().decode('utf-8')
            code = response.code
        except urllib.error.HTTPError as e:
            header = e.headers
            body = e.read().decode('utf-8')
            code = e.code
        except Exception as e:
            self.logger(f"getPage Error: {e}, URL: {url}")
            header = ''
            body = ''
            code = 500
        result = {
            'code': code,
            'header': header,
            'body': body
        }
        return result

    def getRealUrl(self, url, requestHeader=[]):
        self.logger(f"开始处理 getRealUrl, 接收到的原始字符串: {url}")
        
        # 【第一步】检查并去除特定的前缀和后缀
        # 根据观察，前缀可能是 'k'，后缀可能是 '5CW' 或其他。我们用更通用的方式处理。
        # 这里的实现是，如果字符串以 'k' 开头并且以 '5CW' 结尾，就去掉它们。
        processed_url = url
        if processed_url.startswith('k') and processed_url.endswith('5CW'):
            processed_url = processed_url[1:-3]
            self.logger(f"已去除头'k'和尾'5CW', 处理后: {processed_url}")
        else:
            self.logger("警告: 原始字符串不符合 'k...5CW' 的格式，将尝试直接解码。")

        # 【第二步】进行 Base64 解码
        try:
            # Base64编码的字符串长度必须是4的倍数，如果不是，需要用'='补齐
            missing_padding = len(processed_url) % 4
            if missing_padding != 0:
                processed_url += '=' * (4 - missing_padding)
                self.logger(f"Base64 字符串长度不足，已补全'=': {processed_url}")
            
            decoded_bytes = base64.b64decode(processed_url)
            decoded_url = decoded_bytes.decode('utf-8')
            self.logger(f"Base64 解码成功, 得到解码后的URL: {decoded_url}")
            
            # 【第三步】获取最终跳转地址 (很多时候解码出来的是一个会跳转的URL)
            self.logger(f"正在访问解码后的URL以获取最终地址...")
            final_url = self.get_redirect_url(decoded_url)
            self.logger(f"获取最终地址成功: {final_url}")
            return final_url

        except Exception as e:
            self.logger(f"!!!!!! 解码或跳转失败: {e}, 处理中的字符串: {processed_url}")
            return "" # 返回空字符串表示失败

    def get_redirect_url(self, url):
        """
        一个辅助函数，用于访问一个URL并获取其最终的地址（处理重定向）
        """
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            # .geturl() 可以获取请求的最终URL，如果发生了重定向，它会返回重定向后的URL
            final_url = response.geturl()
            return final_url
        except Exception as e:
            self.logger(f"get_redirect_url 访问失败: {e}, URL: {url}")
            # 如果访问解码后的URL失败，直接返回解码后的URL本身
            return url

    def fakeIp (self) :
        fakeIpList = []
        for x in range(0, 4):
            fakeIpList.append(str(int(random.uniform(0, 255))))
        fakeIp = '.'.join(fakeIpList)
        return fakeIp

    def fmtTitle (self, string) :
        pattern = re.compile(r"(cctv[-|\s]*\d*)?(.*)", re.I)
        tmp = pattern.findall(string)
        channelId = tmp[0][0].strip('-').strip()
        channeTitle = tmp[0][1]
        channeTitle = channeTitle.replace('.m3u8', '')
        pattern = re.compile(r"<.*?>", re.I)
        channeTitle = re.sub(pattern, "", channeTitle)
        pattern = re.compile(r"(fhd|hd|sd)", re.I)
        tmp = pattern.findall(channeTitle)
        quality = ''
        if len(tmp) > 0 :
            quality = tmp[0]
            channeTitle = channeTitle.replace(tmp[0], '')
        try :
            channeTitle.index('高清')
            channeTitle = channeTitle.replace('高清', '')
            quality = 'hd'
        except :
            pass
        try :
            channeTitle.index('超清')
            channeTitle = channeTitle.replace('超清', '')
            quality = 'fhd'
        except :
            pass
        result = {
            'id'     : channelId,
            'title'  : channeTitle.strip('-').strip(),
            'quality': quality.strip('-').strip(),
            'level'  : 4,
        }
        if result['id'] != '':
            pattern = re.compile(r"cctv[-|\s]*(\d*)", re.I)
            result['id'] = re.sub(pattern, "CCTV-\\1", result['id'])
            if '+' in result['title'] :
                result['id'] = result['id'] + str('+')
        pattern = re.compile(r"\[\d+\*\d+\]", re.I)
        result['title'] = re.sub(pattern, "", result['title'])
        Area = area.Area()
        result['level'] = Area.classify(str(result['id']) + str(result['title']))
        pattern = re.compile(r"(radio|fm)", re.I)
        tmp = pattern.findall(result['title'])
        if len(tmp) > 0 :
            result['level'] = 7
        return result

    def chkPlayable (self, url) :
        try:
            self.logger(f"开始检查可用性 (chkPlayable): {url}")
            startTime = int(round(time.time() * 1000))
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            code = urllib.request.urlopen(req).getcode()
            if code == 200 :
                endTime = int(round(time.time() * 1000))
                useTime = endTime - startTime
                self.logger(f"可用! 延迟: {useTime}ms, URL: {url}")
                return int(useTime)
            else:
                self.logger(f"不可用, HTTP状态码: {code}, URL: {url}")
                return 0
        except Exception as e:
            self.logger(f"检查可用性时发生异常: {e}, URL: {url}")
            return 0
            
    def chkCros (self, url) :
        return 0

    def logger (self, txt, new = False) :
        # 日志文件路径，放在与 tools.py 同级的目录中
        filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
        if new :
            typ = 'w' # 'w' 模式会覆盖旧日志
        else :
            typ = 'a' # 'a' 模式会追加新日志
        try:
            # 增加 encoding='utf-8' 以避免中文乱码
            with open(filePath, typ, encoding='utf-8') as f:
                log_entry = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ": " + txt + "\n"
                f.write(log_entry)
                print(log_entry.strip()) # 同时在控制台打印日志，方便实时查看
        except Exception as e:
            print(f"写入日志失败: {e}")
