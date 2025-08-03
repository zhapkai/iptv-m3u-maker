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

    def _rc4_decrypt(self, key, data):
        """RC4 stream cipher decryption."""
        S = list(range(256))
        j = 0
        # Key-scheduling algorithm (KSA)
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        
        # Pseudo-random generation algorithm (PRGA)
        i = 0
        j = 0
        res = bytearray()
        for char_byte in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            keystream_byte = S[(S[i] + S[j]) % 256]
            res.append(char_byte ^ keystream_byte)
        return res

    def getRealUrl(self, url):
        if url.startswith("="):
            self.logger(f"开始解码 (V6 - Final Attempt), 原始URL: {url[:70]}...", level="INFO")
            try:
                # 步骤 1: 分离出“初始密钥材料”和“加密数据”
                encoded_str = url[1:]
                pattern_key_encoded = encoded_str[:44]
                url_fragment_encoded = encoded_str[45:]
                
                def pad_base64(data):
                    missing_padding = len(data) % 4
                    if missing_padding: data += '=' * (4 - missing_padding)
                    return data

                initial_key_material = base64.b64decode(pad_base64(pattern_key_encoded))
                encrypted_payload = base64.b64decode(pad_base64(url_fragment_encoded))
                
                # ================== 【V6 终极解密核心】 ==================
                # 步骤 2: 使用“初始密钥材料”的 SHA1 哈希值作为最终的RC4密钥
                final_rc4_key = hashlib.sha1(initial_key_material).digest()
                self.logger(f"派生出最终RC4密钥 (初始密钥的SHA1): {final_rc4_key.hex()}", level="DEBUG")
                
                # 步骤 3: 使用派生出的密钥，通过RC4算法解密整个载荷
                decrypted_payload = self._rc4_decrypt(final_rc4_key, encrypted_payload)
                self.logger("RC4解密完成，开始验证MD5...", level="DEBUG")
                # ========================================================

                # 步骤 4: 分离“MD5指纹”和“URL”
                if len(decrypted_payload) < 16:
                    self.logger("解密后数据长度不足16字节，无法进行MD5校验。", level="ERROR")
                    return ""

                md5_from_payload = decrypted_payload[:16]
                final_url_bytes = decrypted_payload[16:]
                self.logger(f"提取到载荷中的MD5指纹: {md5_from_payload.hex()}", level="DEBUG")

                # 步骤 5: 终极验证！
                md5_of_result = hashlib.md5(final_url_bytes).digest()

                if md5_of_result == md5_from_payload:
                    real_url = final_url_bytes.decode('utf-8')
                    self.logger("MD5验证成功！V6最终方案破解成功！", level="SUCCESS")
                    self.logger(f"最终URL: {real_url}", level="SUCCESS")
                    return real_url
                else:
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
