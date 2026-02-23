import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from nonebot.log import logger, default_format

__version__ = "2.2.4"

# 初始化NoneBot
nonebot.init()

# 获取驱动器
driver = nonebot.get_driver()
driver.register_adapter(Adapter)


# 启动时初始化服务
@driver.on_startup
async def init_services():
    """初始化所有核心服务"""
    from plugins.common.services import (
        AIService, BanService, ChatService, BotService,
        TokenService, SystemMonitorService
    )
    
    # 初始化并注册所有服务到 ServiceLocator
    AIService.get_instance().initialize()
    BanService.get_instance().initialize()
    ChatService.get_instance().initialize()
    BotService.get_instance().initialize()
    TokenService.get_instance().initialize()
    SystemMonitorService.get_instance().initialize()
    
    logger.success("核心服务初始化完成")


# 启动信息
@driver.on_startup
async def startup():
    logger.success(f"机器人启动成功!当前版本{__version__}")


# 加载所有插件（从plugins目录及其子目录）
nonebot.load_plugins("plugins")


# nb-cli 入口点
def main():
    """nb-cli 入口"""
    nonebot.run()


if __name__ == "__main__":
    main()
