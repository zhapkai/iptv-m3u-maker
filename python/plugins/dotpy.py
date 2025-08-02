#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tools
import time
import re
import db
import threading
# 注意：您的项目中可能是 from .threads import ThreadPool，也可能是 from threads import ThreadPool
# 请根据您项目实际的文件结构确认，如果报错，请修改这一行。
from threads import ThreadPool 

class Source (object) :
    def __init__ (self):
        self.T = tools.Tools()
        self.now = int(time.time() * 1000)

    def getSource (self) :
        # 【修改点 1】: 将 sourcePath 改为绝对路径，增强在不同环境下的稳定性
        sourcePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dotpy_source')
        
        if not os.path.exists(sourcePath):
            self.T.logger(f"源文件不存在，跳过: {sourcePath}", level="ERROR")
            return

        with open(sourcePath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total = len(lines)
            threads = ThreadPool(20) # 线程池可以按需调整
            
            for i in range(0, total):
                line = lines[i].strip()
                if not line:
                    continue
                    
                item = line.split(',', 1)
                if len(item) != 2:
                    self.T.logger(f"格式错误，跳过行: {line}", level="WARNING")
                    continue
                
                title = item[0].strip()
                original_url = item[1].strip()

                # --- 【核心修改逻辑】 ---
                # 我们不再简单地检查 .m3u8，而是要进行分情况处理
                
                url_to_check = "" # 将要用于检测的最终URL

                if original_url.startswith('='):
                    # 1. 如果是加密链接，我们先调用解码函数
                    self.T.logger(f"发现加密链接，准备解码: {title}")
                    # 此处调用我们在 tools.py 中写好的解码器
                    url_to_check = self.T.getRealUrl(original_url)
                    
                    if not url_to_check:
                        # 如果解码失败或返回空字符串，记录日志并跳过
                        self.T.logger(f"解码失败，跳过: {title}", level="WARNING")
                        continue

                elif original_url.startswith('http'):
                    # 2. 如果是普通的 http/https 链接，直接使用
                    url_to_check = original_url
                
                else:
                    # 3. 其他无法识别的格式，跳过
                    self.T.logger(f"跳过无法识别的链接格式: {title} - {original_url}", level="WARNING")
                    continue

                # 只有获得了真实有效的URL (url_to_check)，才添加到任务队列
                threads.add_task(self.detectData, title=title, url=url_to_check)

            threads.wait_completion()

    def detectData (self, title, url) :
        # 这个函数现在接收到的 url 都应该是解码后的真实地址了
        self.T.logger(f"正在检测: {title} | URL: {url}")
        info = self.T.fmtTitle(title)
        netstat = self.T.chkPlayable(url)
        if netstat > 0 :
            cros = 1 if self.T.chkCros(url) else 0 # chkCros 似乎总是返回0，可按需修改
            data = {
                'title'  : str(info['id']) if info['id'] != '' else str(info['title']),
                'url'    : str(url), # 存储解码后的真实URL
                'quality': str(info['quality']),
                'delay'  : netstat,
                'level'  : info['level'],
                'cros'   : cros,
                'online' : 1,
                'udTime' : self.now,
            }
            self.addData(data)
            self.T.logger(f"✅ 有效源: [ {str(info['id']) or str(info['title'])} ] 延迟:{netstat}ms", level="INFO")
        else :
            self.T.logger(f"❌ 无效或超时源: {title}", level="WARNING")
            pass

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

# --- 为了让这个文件能独立运行测试，可以加上这两行 ---
# 这不会影响它被其他脚本调用
# if __name__ == '__main__':
#     s = Source()
#     s.getSource()
