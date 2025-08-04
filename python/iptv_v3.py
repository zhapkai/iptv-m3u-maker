import os
import logging
import importlib
import tools

class IPTV:
    def __init__(self):
        """
        初始化 IPTV 类，设置日志记录器、频道列表和根目录。
        """
        self.logger = tools.setup_logger()
        self.channel_list = []
        # 获取项目根目录 (iptv.py 文件的上一级的上一级目录)
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def start(self):
        """
        核心方法，用于启动整个流程：
        1. 读取配置文件。
        2. 根据配置加载并运行启用的插件。
        3. 收集所有插件返回的频道。
        4. 保存为 m3u 文件。
        """
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
                    # 动态导入插件模块
                    plugin_module = importlib.import_module(f"plugins.{plugin_name}")
                    
                    # 检查插件是否有 start 方法
                    if hasattr(plugin_module, 'start') and callable(getattr(plugin_module, 'start')):
                        # 调用插件的 start 方法，并传入 logger 和 config
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

    def save_m3u_file(self):
        """
        将收集到的频道列表保存到项目根目录的 iptv.m3u 文件中。
        """
        # 定义输出文件路径在项目的根目录
        output_file_path = os.path.join(self.root_dir, 'iptv.m3u')
        
        self.logger.info(f"总共获取到 {len(self.channel_list)} 个频道。")

        if not self.channel_list:
            self.logger.warning("没有可用的频道来生成 M3U 文件。")
            # 即使没有频道，也创建一个空文件或带有标题的文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
            self.logger.info(f"已在项目根目录创建空的 M3U 文件: {output_file_path}")
            return

        self.logger.info(f"正在生成 M3U 文件: {output_file_path}")

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for channel in self.channel_list:
                f.write(f'#EXTINF:-1 tvg-id="{channel["id"]}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n')
                f.write(f'{channel["url"]}\n')
        
        self.logger.info("M3U 文件生成成功！")


if __name__ == '__main__':
    print("!!! DEBUG: 文件 iptv.py 已开始执行。")
    IPTV().start()
