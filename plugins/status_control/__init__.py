"""
状态控制插件

管理员功能：查看和控制各功能开关状态、用户管理。
使用一次性令牌验证，令牌通过私聊 "/申请令牌" 获取，5分钟内有效。

使用新架构（PluginHandler + CommandReceiver）重构
"""
from typing import List, Tuple, Set

try:
    from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PrivateMessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    BanServiceProtocol,
    TokenServiceProtocol,
    SystemMonitorProtocol,
    ConfigProviderProtocol,
)


class RequestTokenHandler(PluginHandler):
    """申请令牌处理器（私聊）"""
    
    name = "申请令牌"
    description = "私聊申请管理员操作令牌"
    command = "申请令牌"
    priority = 10
    feature_name = None
    hidden_in_help = True
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理令牌申请（仅私聊）"""
        if not isinstance(event, PrivateMessageEvent):
            await self.reply("请私聊机器人申请令牌")
            return
        
        user_id = event.user_id
        
        # 检查管理员权限
        config = ServiceLocator.get(ConfigProviderProtocol)
        if config is None:
            await self.reply("配置服务不可用")
            return
        
        admin_ids = config.get("admin_user_ids_set", set())
        if user_id not in admin_ids:
            await self.reply("您没有管理员权限")
            return
        
        # 通过协议层获取令牌服务
        token_service = ServiceLocator.get(TokenServiceProtocol)
        if token_service is None:
            await self.reply("令牌服务不可用")
            return
        
        token = token_service.generate_token(user_id)
        
        await self.finish(
            f"您的操作令牌: {token}\n"
            f"有效期: 5分钟\n"
            f"使用方式: 在群内发送 \"状态控制 {token} [操作]\"\n"
            f"可用操作: 开关/拉黑/解封/状态/系统"
        )


class StatusControlHandler(PluginHandler):
    """状态控制处理器"""
    
    name = "状态控制"
    description = "管理员功能：查看和控制各功能开关状态"
    command = "状态控制"
    aliases = {"状态", "控制"}
    priority = 100
    feature_name = None
    hidden_in_help = True
    
    CONTROLLABLE_FEATURES: List[Tuple[str, str, str]] = [
        ("math", "数学定义", "数学"),
        ("random", "随机回复", "随机"),
        ("highnoon", "午时已到", "午时已到"),
        ("pjskpartiton", "PJSK谱面", "PJSK"),
        ("math_soup", "数学谜题", "数学谜"),
    ]
    
    def _get_config(self) -> ConfigProviderProtocol:
        """获取配置提供者"""
        config = ServiceLocator.get(ConfigProviderProtocol)
        if config is None:
            raise RuntimeError("配置服务不可用")
        return config
    
    def _check_admin(self, user_id: int) -> bool:
        """检查是否为管理员"""
        config = self._get_config()
        admin_ids = config.get("admin_user_ids_set", set())
        return user_id in admin_ids
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理状态控制命令"""
        user_id = event.user_id
        
        if not self._check_admin(user_id):
            await self.reply("您没有管理员权限")
            return
        
        if not args:
            await self._show_status()
            return
        
        parts = args.split(maxsplit=1)
        token = parts[0]
        remaining = parts[1] if len(parts) > 1 else ""
        
        # 验证令牌
        token_service = ServiceLocator.get(TokenServiceProtocol)
        if token_service is None:
            await self.reply("令牌服务不可用")
            return
        
        if not token_service.verify_token(user_id, token):
            if token_service.has_valid_token(user_id):
                remaining_time = token_service.get_token_remaining_time(user_id)
                await self.reply(f"令牌错误。您有有效令牌，剩余 {remaining_time} 秒")
            else:
                await self.reply("令牌无效或已过期，请私聊申请新令牌")
            return
        
        if not remaining:
            await self._show_status()
            return
        
        action_parts = remaining.split(maxsplit=1)
        action = action_parts[0].lower()
        action_args = action_parts[1] if len(action_parts) > 1 else ""
        
        if action == "开关":
            await self._handle_toggle(action_args)
        elif action == "拉黑":
            await self._handle_ban(action_args)
        elif action == "解封":
            await self._handle_unban(action_args)
        elif action == "状态":
            await self._show_status()
        elif action == "系统":
            await self._show_system_status()
        else:
            await self.reply(f"未知操作: {action}。可用: 开关/拉黑/解封/状态/系统")
    
    async def _show_status(self) -> None:
        """显示所有功能状态"""
        config = self._get_config()
        
        lines = ["功能状态:"]
        
        for feature_key, display_name, _ in self.CONTROLLABLE_FEATURES:
            is_enabled = config.is_feature_enabled(feature_key)
            status = "[开启]" if is_enabled else "[关闭]"
            lines.append(f"  {display_name}: {status}")
        
        # 通过协议层获取黑名单服务
        ban = ServiceLocator.get(BanServiceProtocol)
        banned_count = 0
        if ban is not None:
            banned_count = ban.get_banned_count()
        lines.append(f"\n已拉黑用户: {banned_count} 人")
        
        await self.finish("\n".join(lines))
    
    async def _handle_toggle(self, args: str) -> None:
        """处理功能开关"""
        if not args:
            await self.reply("请输入要切换的功能名，如: 开关 数学")
            return
        
        target = args.strip().lower()
        
        matched_feature = None
        for feature_key, display_name, short_name in self.CONTROLLABLE_FEATURES:
            if target in feature_key or target in display_name.lower() or target == short_name.lower():
                matched_feature = (feature_key, display_name)
                break
        
        if not matched_feature:
            available = ", ".join([name for _, name, _ in self.CONTROLLABLE_FEATURES])
            await self.finish(f"未知功能。可用: {available}")
            return
        
        feature_key, display_name = matched_feature
        
        # 注意：这里应该调用配置提供者的方法来切换功能
        # 但 ConfigProviderProtocol 只定义了读取接口
        # 实际实现可能需要扩展协议或直接使用 config 模块
        # 暂时保持简单实现
        from plugins.common import config as _config
        current_value = getattr(_config, f"{feature_key}_enabled", True)
        setattr(_config, f"{feature_key}_enabled", not current_value)
        new_status = "开启" if not current_value else "关闭"
        
        await self.finish(f"{display_name} 已{new_status}")
    
    async def _handle_ban(self, user_id_str: str) -> None:
        """处理拉黑用户"""
        if not user_id_str.strip():
            await self.reply("请输入用户ID，如: 拉黑 123456")
            return
        
        try:
            target_user_id = int(user_id_str.strip())
        except ValueError:
            await self.reply("用户ID必须是数字")
            return
        
        ban = ServiceLocator.get(BanServiceProtocol)
        if ban is None:
            await self.reply("黑名单服务不可用")
            return
        
        if ban.is_banned(target_user_id):
            await self.finish(f"用户 {target_user_id} 已在黑名单中")
            return
        
        result = ban.ban(target_user_id)
        if result.is_success:
            await self.finish(f"用户 {target_user_id} 已被拉黑")
        else:
            await self.finish(f"拉黑失败: {result.error}")
    
    async def _handle_unban(self, user_id_str: str) -> None:
        """处理解封用户"""
        if not user_id_str.strip():
            await self.reply("请输入用户ID，如: 解封 123456")
            return
        
        try:
            target_user_id = int(user_id_str.strip())
        except ValueError:
            await self.reply("用户ID必须是数字")
            return
        
        ban = ServiceLocator.get(BanServiceProtocol)
        if ban is None:
            await self.reply("黑名单服务不可用")
            return
        
        if not ban.is_banned(target_user_id):
            await self.finish(f"用户 {target_user_id} 不在黑名单中")
            return
        
        result = ban.unban(target_user_id)
        if result.is_success:
            await self.finish(f"用户 {target_user_id} 已解除拉黑")
        else:
            await self.finish(f"解封失败: {result.error}")
    
    async def _show_system_status(self) -> None:
        """显示系统状态"""
        monitor = ServiceLocator.get(SystemMonitorProtocol)
        if monitor is None:
            await self.finish("系统监控服务不可用")
            return
        
        status_text = monitor.get_status_text()
        await self.finish(status_text)


# ========== 创建处理器和接收器 ==========
request_token_handler = RequestTokenHandler()
status_control_handler = StatusControlHandler()

request_token_receiver = CommandReceiver(request_token_handler)
status_control_receiver = CommandReceiver(status_control_handler)


# ========== 导出元数据 ==========
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="状态控制",
        description="管理员功能：查看和控制各功能开关状态（需令牌）",
        usage="私聊: /申请令牌 | 群内: /状态控制 [令牌] [操作] [参数]",
        extra={"author": "Lichlet", "version": "2.3.0"}
    )
