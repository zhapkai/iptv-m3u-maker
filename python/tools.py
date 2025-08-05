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
import os

socket.setdefaulttimeout(10.0)  # 增加超时时间到 10 秒

class Tools(object):
    def __init__(self):
        pass

    def getPage(self, url, requestHeader=[], postData={}):
        fakeIp = self.fakeIp()
        requestHeader.append('CLIENT-IP:' + fakeIp)
        requestHeader.append('X-FORWARDED-FOR:' + fakeIp)

        if postData == {}:
            try:
                request = urllib.request.Request(url)
            except ValueError as e:
                self.logger(f"Invalid URL error in getPage: {url}, {str(e)}")
                return {'code': 400, 'header': '', 'body': ''}
        elif isinstance(postData, str):
            request = urllib.request.Request(url, postData)
        else:
            request = urllib.request.Request(url, urllib.parse.urlencode(postData).encode('utf-8'))

        for x in requestHeader:
            headerType = x.split(':')[0]
            headerCon = x.replace(headerType + ':', '')
            request.add_header(headerType, headerCon)

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urllib.request.urlopen(request, context=ctx, timeout=10.0)
            header = response.headers
            body = response.read().decode('utf-8', errors='ignore')
            code = response.code
        except urllib.error.HTTPError as e:
            self.logger(f"HTTPError in getPage: {url}, code: {e.code}")
            header = e.headers
            body = e.read().decode('utf-8', errors='ignore')
            code = e.code
        except Exception as e:
            self.logger(f"Exception in getPage: {url}, {str(e)}")
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
        fakeIp = self.fakeIp()
        requestHeader.append('CLIENT-IP:' + fakeIp)
        requestHeader.append('X-FORWARDED-FOR:' + fakeIp)

        request = urllib.request.Request(url)

        for x in requestHeader:
            headerType = x.split(':')[0]
            headerCon = x.replace(headerType + ':', '')
            request.add_header(headerType, headerCon)
        try:
            response = urllib.request.urlopen(request, timeout=10.0)
            realUrl = response.geturl()
        except Exception as e:
            self.logger(f"Exception in getRealUrl: {url}, {str(e)}")
            realUrl = ""
        
        return realUrl

    def fakeIp(self):
        fakeIpList = []
        for x in range(0, 4):
            fakeIpList.append(str(int(random.uniform(0, 255))))
        return '.'.join(fakeIpList)

    def fmtCookie(self, string):
        result = re.sub(r"path\=\/.", "", string)
        result = re.sub(r"(\S*?)\=deleted.", "", result)
        result = re.sub(r"expires\=(.*?)GMT;", "", result)
        result = re.sub(r"domain\=(.*?)tv.", "", result)
        result = re.sub(r"httponly", "", result)
        result = re.sub(r"\s", "", result)
        return result

    def urlencode(self, str):
        reprStr = repr(str).replace(r'\x', '%')
        return reprStr[1:-1]

    def gzdecode(self, data):
        try:
            compressedstream = io.StringIO(data)
            gziper = gzip.GzipFile(fileobj=compressedstream)
            html = gziper.read()
            return html
        except:
            return data

    def fmtTitle(self, string):
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
        if len(tmp) > 0:
            quality = tmp[0]
            channeTitle = channeTitle.replace(tmp[0], '')

        try:
            channeTitle.index('高清')
            channeTitle = channeTitle.replace('高清', '')
            quality = 'hd'
        except:
            pass

        try:
            channeTitle.index('超清')
            channeTitle = channeTitle.replace('超清', '')
            quality = 'fhd'
        except:
            pass

        result = {
            'id': channelId,
            'title': channeTitle.strip('-').strip(),
            'quality': quality.strip('-').strip(),
            'level': 4,
        }

        if result['id'] != '':
            pattern = re.compile(r"cctv[-|\s]*(\d*)", re.I)
            result['id'] = re.sub(pattern, "CCTV-\\1", result['id'])

            if '+' in result['title']:
                result['id'] = result['id'] + str('+')

        pattern = re.compile(r"\[\d+\*\d+\]", re.I)
        result['title'] = re.sub(pattern, "", result['title'])

        if result['id'].startswith('CCTV'):
            result['level'] = 1
        elif 'radio' in result['title'].lower() or 'fm' in result['title'].lower():
            result['level'] = 7
        else:
            result['level'] = 2

        return result

    def chkPlayable(self, url):
        try:
            startTime = int(round(time.time() * 1000))
            code = urllib.request.urlopen(url, timeout=10.0).getcode()
            if code == 200:
                endTime = int(round(time.time() * 1000))
                useTime = endTime - startTime
                return int(useTime)
            else:
                return 0
        except Exception as e:
            self.logger(f"Exception in chkPlayable: {url}, {str(e)}")
            return 0

    def chkCros(self, url):
        return 0

    def logger(self, txt, new=False):
        filePath = 'log.txt'  # 确保在当前工作目录
        try:
            typ = 'w' if new else 'a'
            with open(filePath, typ, encoding='utf-8') as f:
                f.write(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + ": " + txt + "\n")
            self.logger(f"Log written to {filePath}: {txt}", False)  # 递归记录，确保写入
        except Exception as e:
            print(f"Failed to write log: {str(e)}")  # 打印到控制台作为备用
