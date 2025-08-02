#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import urllib.error
import re
import ssl
import sys
import os
import base64
import time
import random
import area
import socket

socket.setdefaulttimeout(5.0)

class Tools (object) :
    def __init__ (self) :
        self.logger("====== Script Start / New Run ======", level="INFO")
        pass

    def logger(self, txt, level="DEBUG"):
        try:
            log_entry = f"{time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())} [{level.upper()}]: {txt}"
            print(log_entry, file=sys.stderr)
        except Exception as e:
            print(f"LOGGER FAILED: {e}", file=sys.stderr)

    def getRealUrl(self, url, requestHeader=[]):
        """
        智能解码函数，用于处理多种动态加密链接。
        """
        self.logger(f"开始解码, 原始URL: {url}", level="INFO")

        if not url.startswith('='):
            self.logger(f"URL格式不正确，缺少起始'=': {url}", level="ERROR")
            return ""

        # 【已修正】: 使用 lstrip('=') 移除所有前导'='，无论是1个还是2个
        encoded_str = url.lstrip('=')

        parts = encoded_str.split('/')
        if len(parts) < 2:
            self.logger(f"URL格式不正确，无法按'/'分割: {encoded_str}", level="ERROR")
            return ""

        mode_key = parts[0]
        self.logger(f"检测到模式密钥: {mode_key}")

        real_url = ""
        try:
            if mode_key in ["kwIxYjF", "MkUhUAD", "QEVic1w", "EQQY92F"] or True: # 暂时放宽，接受所有模式
                data_to_decode = "".join(parts[1:])
                real_url = self.decode_base64_with_padding(data_to_decode)
            else:
                self.logger(f"发现未知的模式密钥 '{mode_key}', 无法解码!", level="ERROR")
                return ""

            if real_url:
                self.logger(f"解码成功, 得到真实URL: {real_url}", level="INFO")
                return real_url
            else:
                self.logger(f"解码失败，模式密钥: {mode_key}", level="ERROR")
                return ""

        except Exception as e:
            self.logger(f"解码过程中发生未知异常: {e}", level="CRITICAL")
            return ""

    def decode_base64_with_padding(self, b64_string):
        self.logger(f"正在解码片段: {b64_string[:50]}...")
        try:
            missing_padding = len(b64_string) % 4
            if missing_padding:
                b64_string += '=' * (4 - missing_padding)
            
            decoded_bytes = base64.b64decode(b64_string)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            self.logger(f"Base64解码失败: {e}", level="ERROR")
            return None
            
    # ------ 以下是文件中原有的其他函数，保持不变 ------
    
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
            self.logger(f"getPage Error: {e}, URL: {url}", level="ERROR")
            header = ''
            body = ''
            code = 500
        result = {
            'code': code,
            'header': header,
            'body': body
        }
        return result

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
            startTime = int(round(time.time() * 1000))
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            code = urllib.request.urlopen(req, context = ctx, timeout=5).getcode()
            if code == 200 :
                endTime = int(round(time.time() * 1000))
                useTime = endTime - startTime
                self.logger(f"可用! 延迟: {useTime}ms, URL: {url}")
                return int(useTime)
            else:
                self.logger(f"不可用, HTTP状态码: {code}, URL: {url}", level="WARNING")
                return 0
        except Exception as e:
            self.logger(f"检查可用性时发生异常: {e}, URL: {url}", level="WARNING")
            return 0
            
    def chkCros (self, url) :
        return 0
