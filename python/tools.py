#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import urllib.error
import re
import ssl
import sys  # <---【第一处修改】: 导入 sys 模块
import os
import base64
import time
import area
import socket

socket.setdefaulttimeout(5.0)

class Tools (object) :
    def __init__ (self) :
        self.logger("====== Script Start / New Run ======", level="INFO")
        pass

    # <---【第二处修改】: 全面重写 logger 函数
    def logger(self, txt, level="DEBUG"):
        """
        新的日志函数，直接打印到标准错误输出，确保在GitHub Actions中可见。
        """
        try:
            # 格式化日志条目，包含时间戳和日志级别
            log_entry = f"{time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())} [{level}]: {txt}"
            # 打印到标准错误流 (stderr)，Actions会将其捕获到日志中
            print(log_entry, file=sys.stderr)
        except Exception as e:
            # 如果打印日志本身都失败了，就用最基本的方式打印错误
            print(f"LOGGER FAILED: {e}", file=sys.stderr)

    # <---【第三处修改】: 彻底重写 getRealUrl 函数以应对多种加密模式
    def getRealUrl(self, url, requestHeader=[]):
        """
        智能解码函数，用于处理 m.iptv807.com 的多种动态加密链接。
        """
        self.logger(f"开始解码, 原始URL: {url}", level="INFO")

        if not url.startswith('='):
            self.logger(f"URL格式不正确，缺少起始'=': {url}", level="ERROR")
            return ""

        # 去掉起始的 '='
        encoded_str = url[1:]

        # 将字符串按 '/' 分割成多个部分
        parts = encoded_str.split('/')
        if len(parts) < 2:
            self.logger(f"URL格式不正确，无法按'/'分割: {encoded_str}", level="ERROR")
            return ""

        # 第一个部分是“模式”密钥
        mode_key = parts[0]
        self.logger(f"检测到模式密钥: {mode_key}")

        real_url = ""
        try:
            # 根据不同的模式密钥，选择不同的解码方法
            if mode_key in ["kwIxYjF", "MkUhUAD"]:
                # 这种模式下，后面的部分是需要解码的Base64字符串
                # 示例: QmeMkGYRhFP, VARSxHP...
                # 我们需要将这些部分组合起来进行解码
                data_to_decode = "".join(parts[1:])
                real_url = self.decode_base64_with_padding(data_to_decode)

            elif mode_key in ["QEVic1w", "EQQY92F"]:
                # 这种模式逻辑类似，也是将后续部分组合起来解码
                # 示例: GYTfaZ2MFw..., NQPx0wBWYS...
                data_to_decode = "".join(parts[1:])
                real_url = self.decode_base64_with_padding(data_to_decode)

            else:
                # 如果遇到未知的模式密钥，打印错误日志并返回失败
                self.logger(f"发现未知的模式密钥 '{mode_key}', 无法解码!", level="ERROR")
                return ""

            if real_url:
                self.logger(f"解码成功, 得到真实URL: {real_url}", level="INFO")
                # 最终可以再加一步跳转，以防解码出来的是一个重定向地址
                # return self.get_redirect_url(real_url) 
                return real_url # 为简化起见，暂时先不跳转
            else:
                self.logger(f"解码失败，模式密钥: {mode_key}", level="ERROR")
                return ""

        except Exception as e:
            self.logger(f"解码过程中发生未知异常: {e}", level="CRITICAL")
            return ""

    def decode_base64_with_padding(self, b64_string):
        """
        一个辅助函数，用于解码可能缺少填充符'='的Base64字符串。
        """
        self.logger(f"正在解码片段: {b64_string[:50]}...") # 只记录前50个字符，避免日志过长
        try:
            # Base64字符串的长度必须是4的倍数，如果不是，需要用'='在末尾补齐
            missing_padding = len(b64_string) % 4
            if missing_padding:
                b64_string += '=' * (4 - missing_padding)
            
            decoded_bytes = base64.b64decode(b64_string)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            self.logger(f"Base64解码失败: {e}", level="ERROR")
            return None
            
    # ------ 以下是文件中原有的其他函数，保持不变 ------

    def get_redirect_url(self, url):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            final_url = response.geturl()
            return final_url
        except Exception as e:
            self.logger(f"get_redirect_url 访问失败: {e}, URL: {url}", level="WARNING")
            return url

    def getPage (self, url, requestHeader = [], postData = {}) :
        # ... (此函数及以下其他函数保持原样)
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
        # ... (省略了未修改的代码以节约篇幅)
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
            code = urllib.request.urlopen(req).getcode()
            if code == 200 :
                endTime = int(round(time.time() * 1000))
                useTime = endTime - startTime
                self.logger(f"可用! 延迟: {useTime}ms, URL: {url}")
                return int(useTime)
            else:
                self.logger(f"不可用, HTTP状态码: {code}, URL: {url}", level="WARNING")
                return 0
        except:
            self.logger(f"检查可用性时发生异常: {url}", level="WARNING")
            return 0
            
    def chkCros (self, url) :
        return 0
