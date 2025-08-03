# coding:utf-8
import logging
import os
import sys
import json

class Tools:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 控制台输出
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # 文件输出
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        fh = logging.FileHandler(os.path.join(log_path, "log.log"), mode='a', encoding="utf-8")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def getConfig(self):
        """
        读取并解析项目根目录下的 config.json 文件。
        """
        # config.json 文件应该在 python 目录的上一级，也就是项目根目录
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self.logger.info(f"正在读取配置文件: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.logger.info("配置文件读取成功。")
                return config
        except FileNotFoundError:
            self.logger.error(f"错误: 配置文件 config.json 未找到! 请检查路径: {config_path}")
            return {}  # 返回一个空字典以避免程序完全崩溃
        except json.JSONDecodeError:
            self.logger.error("错误: config.json 文件格式不正确，无法解析!")
            return {}
        except Exception as e:
            self.logger.error(f"读取配置文件时发生未知错误: {e}")
            return {}

    def getChannel(self, name, id, tvg_id):
        return {"name": name, "id": id, "tvg_id": tvg_id}

    def generateM3u(self, channels):
        # 这是一个占位方法，我们后面会实现它
        pass
