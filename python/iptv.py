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
        print("!!! DEBUG: IPTV.start() 方法已开始执行。")
        self.logger.info(f"iptv-m3u-maker 开始运行。")
        
        # 获取配置
        config = tools.getConfig()
        
        # 检查 "enable" 键是否存在且是一个非空列表
        if "enable" not in config or not isinstance(config.get("enable"), list) or not config.get("enable"):
            self.logger.warning("配置文件中没有启用任何插件 (enable 列表为空、不存在或格式不正确)。")
        else:
            enabled_plugins = config["enable"]
            self.logger.info(f"已启用的插件: {enabled_plugins}")

            # 直接遍历启用的插件列表
            for plugin_name in enabled_plugins:
                try:
                    self.logger.info(f"正在加载插件: {plugin_name}")
                    plugin_module = importlib.import_module(f"plugins.{plugin_name}")
                    
                    # 检查插件是否有 start 方法
                    if hasattr(plugin_module, 'start') and callable(getattr(plugin_module, 'start')):
                        # 调用插件的 start 方法，并传入 logger 和配置
                        new_channels = plugin_module.start(self.logger, config)
                        if new_channels:
                            self.channel_list.extend(new_channels)
                            self.logger.info(f"插件 {plugin_name} 成功获取到 {len(new_channels)} 个频道。")
                        else:
                            self.logger.warning(f"插件 {plugin_name} 未返回任何频道。")
                    else:
                        self.logger.error(f"插件 {plugin_name} 中没有找到可执行的 start 方法。")

                except ImportError:
                    self.logger.error(f"导入插件 {plugin_name} 失败，请检查 plugins 文件夹下是否存在 {plugin_name}.py 文件。")
                except Exception as e:
                    self.logger.error(f"运行插件 {plugin_name} 时发生错误: {e}")
                    # 打印更详细的错误堆栈信息，便于调试
                    import traceback
                    self.logger.error(traceback.format_exc())

        # 生成 m3u 文件
        self.save_m3u_file()


if __name__ == '__main__':
    IPTV().start()
