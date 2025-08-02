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

    # ==================== 【函数区】 ====================
    # 我们所有的修改都集中在这里
    # =================================================

    def logger(self, content, level='INFO'):
        if not isinstance(level, str):
            level_str = 'INFO'
        else:
            level_str = level.upper()
        print(f"{time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())} [{level_str}]: {content}")

    def getRealUrl(self, url):
        if url.startswith("="):
            self.logger(f"开始解码, 原始URL: {url[:70]}...", level="INFO")
            try:
                encoded_str = url[1:]
                pattern_key_encoded = encoded_str[:44]
                url_fragment_encoded = encoded_str[45:]
                
                self.logger(f"检测到模式密钥: {pattern_key_encoded}", level="DEBUG")
                self.logger(f"正在解码片段: {url_fragment_encoded[:50]}...", level="DEBUG")

                def pad_base64(data):
                    missing_padding = len(data) % 4
                    if missing_padding != 0:
                        data += '=' * (4 - missing_padding)
                    return data

                pattern_key_padded = pad_base64(pattern_key_encoded)
                fragment_padded = pad_base64(url_fragment_encoded)

                decoded_key_bytes = base64.b64decode(pattern_key_padded)
                decoded_fragment_bytes = base64.b64decode(fragment_padded)
                
                key_len = len(decoded_key_bytes)
                decrypted_bytes = bytearray()
                for i in range(len(decoded_fragment_bytes)):
                    decrypted_byte = decoded_fragment_bytes[i] ^ decoded_key_bytes[i % key_len]
                    decrypted_bytes.append(decrypted_byte)

                # ==================== 【核心修改区域开始】 ====================
                # 我们将用下面的智能“翻译”逻辑替换掉原来单一的UTF-8解码

                real_url = ""
                try:
                    # 1. 优先尝试用 UTF-8 解码
                    real_url = decrypted_bytes.decode('utf-8')
                    self.logger(f"使用 UTF-8 解码成功", level="DEBUG")
                except UnicodeDecodeError:
                    # 2. 如果 UTF-8 失败，马上尝试 GBK 解码
                    self.logger(f"UTF-8 解码失败, 正在尝试使用 GBK 编码...", level="WARNING")
                    try:
                        real_url = decrypted_bytes.decode('gbk')
                        self.logger(f"使用 GBK 解码成功", level="DEBUG")
                    except Exception as gbk_e:
                        self.logger(f"GBK 解码也失败了: {gbk_e}", level="ERROR")
                        self.logger(f"无法将解密后的二进制内容转换为字符串。", level="ERROR")
                        return "" # 两种编码都失败，返回空

                # ==================== 【核心修改区域结束】 ====================
                
                self.logger(f"解码成功, 得到真实URL: {real_url[:80]}...", level="SUCCESS")
                return real_url

            except Exception as e:
                self.logger(f"解码过程中发生未知错误: {e}", level="ERROR")
                self.logger(f"解码失败, 模式密钥: {pattern_key_encoded}", level="ERROR")
                return ""
        else:
            return url

    # =================================================
    # ------ 以下是文件中原有的其他函数，保持不变 ------
    # =================================================

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
