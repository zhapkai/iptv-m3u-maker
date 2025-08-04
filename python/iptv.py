import threading
import time
from tools import Tools
from listb import Source as ListbSource
from db import DataBase

class Iptv(object):
    def __init__(self):
        self.T = Tools()
        self.DB = DataBase()

    def run(self):
        self.T.logger('start', 'w')
        self.DB.chkTable()
        # 只调用 listb.py 的直播源爬取
        ListbSource().getSource()
        self.outPut()
        self.outJson()
        self.T.logger('done')

    def outPut(self):
        sql = """
            SELECT title, url
            FROM iptv
            WHERE online=1 AND delay<500 AND title IS NOT NULL AND title NOT LIKE 'CCTV-%'
            ORDER BY level ASC, LENGTH(title) ASC, title ASC
        """
        rows = self.DB.select(sql)
        group = {1: '中央频道', 2: '地方频道', 7: '广播频道'}
        with open('tv.m3u', 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for row in rows:
                level = self.T.getLevel(row[0])
                f.write(f'#EXTINF:-1, group-title="{group.get(level, "其他频道")}", {row[0]}\n{row[1]}\n')

    def outJson(self):
        sql = """
            SELECT title, url
            FROM iptv
            WHERE online=1 AND delay<500 AND title IS NOT NULL
            ORDER BY level ASC, LENGTH(title) ASC, title ASC
        """
        rows = self.DB.select(sql)
        data = {'cctv': [], 'local': [], 'radio': [], 'other': []}
        for row in rows:
            level = self.T.getLevel(row[0])
            key = 'cctv' if level == 1 else 'local' if level == 2 else 'radio' if level == 7 else 'other'
            data[key].append({'title': row[0], 'url': row[1]})
        import json
        with open('tv.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    Iptv().run()
