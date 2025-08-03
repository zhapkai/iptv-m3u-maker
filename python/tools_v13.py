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
import base64 # 1. 新增了 base64 库

socket.setdefaulttimeout(10.0) # 适当延长超时时间

class Tools (object) :
    def __init__ (self) :
        pass

    def getPage (self, url, requestHeader = [], postData = {}) :
        # (此函数保持不变，和您原来的一样)
        fakeIp = self.fakeIp()
        # 伪造一个常见的浏览器User-Agent
        hd = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'CLIENT-IP': fakeIp,
            'X-FORWARDED-FOR': fakeIp,
        }
        if postData == {} :
            request = urllib.request.Request(url)
        elif isinstance(postData, str) :
            request = urllib.request.Request(url, postData)
        else :
            request = urllib.request.Request(url, urllib.parse.urlencode(postData).encode('utf-8'))
        
        # 添加自定义和默认的headers
        for key, value in hd.items():
            request.add_header(key, value)
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
            # 尝试自动检测编码
            charset = response.info().get_content_charset()
            if charset is None:
                charset = 'utf-8' # 默认使用 utf-8
            body = response.read().decode(charset, errors='ignore')
            code = response.code
        except urllib.error.HTTPError as e:
            header = e.headers
            try:
                body = e.read().decode('utf-8')
            except:
                body = ''
            code = e.code
        except:
            header = ''
            body = ''
            code = 500
        result = {
            'code': code,
            'header': header,
            'body': body
        }
        return result

    # 2. 这是被完全重写的关键函数
    def getRealUrl(self, midM3uUrl):
        """
        新的解码函数，用于处理 m.iptv807.com 的加密链接
        """
        # listb.py 传递过来的 midM3uUrl 就是那个加密令牌
        # 网站的域名是固定的
        site_url = 'http://m.iptv807.com'
        
        # 步骤 1: 构造播放页面的URL
        player_page_url = f"{site_url}/play.html?id={midM3uUrl}"
        self.logger(f"开始解码, 访问播放页: {player_page_url}")

        try:
            # 步骤 2: 获取播放页面的HTML内容
            page_data = self.getPage(player_page_url)
            if page_data['code'] != 200:
                self.logger(f"错误: 无法访问播放页, 状态码: {page_data['code']}")
                return ""
            
            html_body = page_data['body']

            # 步骤 3: 从HTML中用正则表达式提取 'vqtes' 变量的值
            match = re.search(r'var vqtes="([^"]+)"', html_body)
            if not match:
                self.logger(f"错误: 在播放页 {player_page_url} 未找到加密变量 'vqtes'")
                return ""

            encrypted_string = match.group(1)

            # 步骤 4: 模拟JavaScript, 将字符串反转
            reversed_string = encrypted_string[::-1]

            # 步骤 5: 对反转后的字符串进行Base64解码
            decoded_bytes = base64.b64decode(reversed_string)
            final_url = decoded_bytes.decode('utf-8') # 将解码后的字节流转换为字符串

            # 步骤 6: 检查解码结果是否是一个有效的m3u8地址
            if final_url.startswith('http') and '.m3u8' in final_url:
                self.logger(f"解码成功! 真实地址: {final_url}")
                return final_url
            else:
                # 如果解码出来不是URL，可能是更复杂的逻辑，先记录下来
                self.logger(f"警告: 解码内容不是一个直接的m3u8地址: {final_url}")
                # 再次尝试从解码后的内容里提取URL
                url_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', final_url)
                if url_match:
                    real_final_url = url_match.group(0)
                    self.logger(f"二次提取成功! 真实地址: {real_final_url}")
                    return real_final_url
                return ""

        except Exception as e:
            self.logger(f"解码过程中发生严重错误: {e}")
            return ""

    # (以下的所有函数都保持不变，和您原来的一样)
    def fakeIp (self) :
        fakeIpList = []
        for x in range(0, 4):
            fakeIpList.append(str(int(random.uniform(0, 255))))
        fakeIp = '.'.join(fakeIpList)
        return fakeIp

    def fmtCookie (self, string) :
        result = re.sub(r"path\=\/.", "", string)
        result = re.sub(r"(\S*?)\=deleted.", "", result)
        result = re.sub(r"expires\=(.*?)GMT;", "", result)
        result = re.sub(r"domain\=(.*?)tv.", "", result)
        result = re.sub(r"httponly", "", result)
        result = re.sub(r"\s", "", result)
        return result

    def urlencode(self, str) :
        reprStr = repr(str).replace(r'\x', '%')
        return reprStr[1:-1]

    def gzdecode(self, data) :
        try:
            compressedstream = io.StringIO(data)
            gziper = gzip.GzipFile(fileobj = compressedstream)
            html = gziper.read()
            return html
        except :
            return data

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
        # Radio
        pattern = re.compile(r"(radio|fm)", re.I)
        tmp = pattern.findall(result['title'])
        if len(tmp) > 0 :
            result['level'] = 7
        return result

    def chkPlayable (self, url) :
        try:
            startTime = int(round(time.time() * 1000))
            # 使用 getPage 函数来检查，因为它有更完整的header
            res = self.getPage(url)
            code = res['code']
            if code == 200 :
                endTime = int(round(time.time() * 1000))
                useTime = endTime - startTime
                return int(useTime)
            else:
                self.logger(f"检查播放失败: {url} , 状态码: {code}")
                return 0
        except:
            return 0

    def chkCros (self, url) :
        return 0

    def logger (self, txt, new = False) :
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'http')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filePath = os.path.join(log_dir, 'log.txt')
        if new :
            typ = 'w'
        else :
            typ = 'a'
        try:
            with open(filePath, typ, encoding='utf-8') as f:
                f.write(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ": " + txt + "\n")
        except Exception as e:
            print(f"写入日志失败: {e}")
