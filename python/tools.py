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
import hashlib

socket.setdefaulttimeout(5.0)

class Tools (object) :
    def __init__ (self) :
        self.logger("====== Script Start / New Run ======", level="INFO")
        pass

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
                # 步骤 1: 分离出“初始密钥”和“第一层加密数据”
                encoded_str = url[1:]
                pattern_key_encoded = encoded_str[:44]
                url_fragment_encoded = encoded_str[45:]
                
                def pad_base64(data):
                    missing_padding = len(data) % 4
                    if missing_padding: data += '=' * (4 - missing_padding)
                    return data

                # 这是解密流程的起点，我们称之为“初始密钥”
                initial_key_bytes = base64.b64decode(pad_base64(pattern_key_encoded))
                decoded_fragment_bytes = base64.b64decode(pad_base64(url_fragment_encoded))
                
                # 步骤 2: 使用“初始密钥”进行第一层XOR解密，得到“加密包裹”
                key_len = len(initial_key_bytes)
                first_decrypted_bytes = bytearray()
                for i in range(len(decoded_fragment_bytes)):
                    decrypted_byte = decoded_fragment_bytes[i] ^ initial_key_bytes[i % key_len]
                    first_decrypted_bytes.append(decrypted_byte)

                self.logger("第一层解密完成, 开始进行最终解密...", level="DEBUG")

                # 步骤 3: 从“加密包裹”中分离出“MD5指纹”和“第二层加密数据”
                if len(first_decrypted_bytes) < 16:
                    self.logger("数据长度不足16字节, 无法应用MD5解密方法。", level="ERROR")
                    return ""

                md5_from_payload = first_decrypted_bytes[:16]
                encrypted_part = first_decrypted_bytes[16:]
                self.logger(f"提取到载荷中的MD5指纹: {md5_from_payload.hex()}", level="DEBUG")

                # ==================== 【最终解密逻辑】 ====================
                # 步骤 4: 创建第二把密钥，它是“初始密钥”的MD5哈希值
                second_key_bytes = hashlib.md5(initial_key_bytes).digest()
                self.logger(f"派生出第二密钥(初始密钥的MD5): {second_key_bytes.hex()}", level="DEBUG")

                # 步骤 5: 使用派生出的“第二密钥”进行第二次XOR解密，得到URL字节码
                second_key_len = len(second_key_bytes) # 恒为16
                decrypted_url_bytes = bytearray()
                for i in range(len(encrypted_part)):
                    decrypted_byte = encrypted_part[i] ^ second_key_bytes[i % second_key_len]
                    decrypted_url_bytes.append(decrypted_byte)
                # =========================================================

                # 步骤 6: 终极验证！计算解密出的URL的MD5，与载荷中的“MD5指纹”进行比对
                md5_of_result = hashlib.md5(decrypted_url_bytes).digest()

                if md5_of_result == md5_from_payload:
                    # 验证成功！
                    real_url = decrypted_url_bytes.decode('utf-8')
                    self.logger("MD5验证成功！已破解得到最终URL！", level="SUCCESS")
                    self.logger(f"最终URL: {real_url}", level="SUCCESS")
                    return real_url
                else:
                    # 如果这次还失败，那加密逻辑可能远比我们想象的更复杂
                    self.logger("MD5验证失败！最终解密失败。", level="ERROR")
                    self.logger(f"载荷中的MD5: {md5_from_payload.hex()}", level="DEBUG")
                    self.logger(f"我们计算的MD5: {md5_of_result.hex()}", level="DEBUG")
                    return ""

            except Exception as e:
                self.logger(f"解码过程中发生未知严重错误: {e}", level="CRITICAL")
                import traceback
                self.logger(traceback.format_exc(), level="DEBUG")
                return ""
        else:
            return url

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
