# coding:utf-8
import os
import importlib
from tools import Tools

# ################### 新增的诊断代码 ###################
print("!!! DEBUG: 文件 iptv.py 已开始执行。")
# ######################################################

class IPTV:
    def __init__(self):
        self.T = Tools()

    def start(self):
        # ################### 新增的诊断代码 ###################
        print("!!! DEBUG: IPTV.start() 方法已开始执行。")
        # ######################################################

        plugin_path = os.path.join(os.path.dirname(__file__), "plugins")
        files = os.listdir(plugin_path)
        plugins = []
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                plugins.append(file[:-3])

        config = self.T.getConfig()
        all_channel = []
        
        # ################### 新增的诊断代码 ###################
        print(f"!!! DEBUG: 准备加载 {len(plugins)} 个插件: {plugins}")
        # ######################################################
        
        for plugin_name in plugins:
            if plugin_name in config and config[plugin_name]["enable"]:
                self.T.logger.info(f"加载插件:{plugin_name}")
                plugin = importlib.import_module(f"plugins.{plugin_name}")
                p = getattr(plugin, plugin_name.capitalize())(self.T)
                try:
                    channels = p.start(config)
                    all_channel.extend(channels)
                except Exception as e:
                    self.T.logger.error(f"插件{plugin_name}运行出错:{e}")
            else:
                self.T.logger.info(f"插件{plugin_name}未开启")
        self.T.logger.info(f"共获取到{len(all_channel)}个频道")
        self.T.generateM3u(all_channel)
        self.T.logger.info("m3u文件已生成")


if __name__ == '__main__':
    IPTV().start()
