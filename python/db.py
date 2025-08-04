#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

class DataBase(object):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.cur = self.conn.cursor()
        self.table = 'iptv'
        self.chkTable()

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def chkTable(self):
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS iptv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                quality TEXT,
                delay INTEGER,
                cros INTEGER,
                level INTEGER,
                enable INTEGER,
                online INTEGER,
                udTime INTEGER
            )
        ''')
        self.conn.commit()

    def select(self, sql):
        self.cur.execute(sql)
        return self.cur.fetchall()

    def insert(self, data):
        sql = '''
            INSERT OR IGNORE INTO iptv (title, url, quality, delay, cros, level, enable, online, udTime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.cur.execute(sql, (
            data['title'], data['url'], data['quality'], data['delay'],
            data['cros'], data['level'], data.get('enable', 1), data['online'], data['udTime']
        ))
        self.conn.commit()
        return self.cur.rowcount > 0

    def update(self, data):
        sql = '''
            UPDATE iptv SET title=?, quality=?, delay=?, cros=?, level=?, enable=?, online=?, udTime=?
            WHERE url=?
        '''
        self.cur.execute(sql, (
            data['title'], data['quality'], data['delay'], data['cros'],
            data['level'], data.get('enable', 1), data['online'], data['udTime'], data['url']
        ))
        self.conn.commit()
        return self.cur.rowcount > 0
