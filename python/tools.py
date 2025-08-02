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

    # 替换 tools.py 中旧的 logger 函数
    def logger(self, content, level='INFO'): # 使用字符串 'INFO' 作为默认值，修复 bool 错误
        # 检查 level 是否为字符串，提供健壮性
        if not isinstance(level, str):
            level_str = 'INFO' # 如果传入了非字符串，则使用默认值
        else:
            level_str = level.upper()
        
        # 使用和您日志中一致的时间格式
        print(f"{time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())} [{level_str}]: {content}")

    # 替换 tools.py 中旧的 getRealUrl 函数
    def getRealUrl(self, url):
        if url.startswith("="):
            self.logger(f"开始解码, 原始URL: {url[:70]}...", level="INFO")
            try:
                # 移除开头的'='
                encoded_str = url[1:]

                # 分割模式密钥和URL片段 (密钥是前44位, 第45位是'/', 片段从第46位开始)
                pattern_key_encoded = encoded_str[:44]
                url_fragment_encoded = encoded_str[45:]
                
                self.logger(f"检测到模式密钥: {pattern_key_encoded}", level="DEBUG")
                self.logger(f"正在解码片段: {url_fragment_encoded[:50]}...", level="DEBUG")

                # --- 增加健壮性：为Base64字符串自动补齐 '=' ---
                def pad_base64(data):
                    missing_padding = len(data) % 4
                    if missing_padding != 0:
                        data += '=' * (4 - missing_padding)
                    return data

                pattern_key_padded = pad_base64(pattern_key_encoded)
                fragment_padded = pad_base64(url_fragment_encoded)
                # --- 补齐结束 ---

                # 1. 对模式密钥进行 Base64 解码
                decoded_key_bytes = base64.b64decode(pattern_key_padded)
                
                # 【重要修正】: 解码后的密钥是原始字节流，不一定是可读字符串。
                # 移除下面这行导致程序崩溃的错误代码！
                # decoded_key_str = decoded_key_bytes.decode('utf-8') 

                # 2. 对URL片段进行 Base64 解码
                decoded_fragment_bytes = base64.b64decode(fragment_padded)
                
                # 3. 执行异或解密
                key_len = len(decoded_key_bytes)
                decrypted_bytes = bytearray()
                for i in range(len(decoded_fragment_bytes)):
                    decrypted_byte = decoded_fragment_bytes[i] ^ decoded_key_bytes[i % key_len]
                    decrypted_bytes.append(decrypted_byte)

                # 4. 将解密后的字节流用 UTF-8 解码成最终的 URL 字符串
                real_url = decrypted_bytes.decode('utf-8')
                
                self.logger(f"解码成功, 得到真实URL: {real_url[:80]}...", level="SUCCESS")
                return real_url

            except UnicodeDecodeError as e:
                # 捕获更具体的错误，如果最终解密的URL不是UTF-8，会在这里捕获
                self.logger(f"解码后内容非UTF-8编码: {e}", level="ERROR")
                self.logger(f"解码失败, 模式密钥: {pattern_key_encoded}", level="ERROR")
                return ""
            except Exception as e:
                # 捕获其他所有异常，比如 b64decode 的 binascii.Error
                self.logger(f"解码时发生未知错误: {e}", level="ERROR")
                self.logger(f"解码失败, 模式密钥: {pattern_key_encoded}", level="ERROR")
                return ""
        else:
            # 如果传入的不是加密URL，直接返回
            return url
          
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
