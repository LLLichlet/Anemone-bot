# query-bot

[![Version](https://img.shields.io/badge/version-2.2.1-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![NoneBot2](https://img.shields.io/badge/NoneBot-2.4+-green.svg)](https://nonebot.dev/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

**[中文](#中文文档)** | **[English](#english-documentation)**

---

<a name="中文文档"></a>
# 中文文档

基于 NoneBot2 框架的 QQ 群聊机器人，提供数学知识查询、游戏娱乐和智能对话功能。

## 功能特性

- **数学定义查询**: 基于 DeepSeek API 的数学概念解释（香蕉空间风格）
- **数学谜题**: 是/否回答游戏模式，支持 325+ 数学概念
- **随机回复**: 基于上下文的 AI 群聊回复，可配置触发概率
- **午时已到**: 俄罗斯轮盘赌禁言小游戏
- **PJSK 谱面**: 随机 Project Sekai 游戏谱面获取
- **状态控制**: 基于一次性令牌的管理员系统

## 技术架构

```
query-bot/
├── bot.py                  # 应用程序入口
├── pyproject.toml          # 项目配置 (PEP 621)
├── requirements.txt        # 生产依赖
├── .env.example            # 环境变量模板
├── CHANGELOG.md            # 版本变更日志
├── data/                   # 运行时数据存储
├── prompts/                # LLM 系统提示词
└── plugins/                # 插件目录
    ├── common/             # 核心基础设施
    │   ├── base.py         # 基础层: ServiceBase, Result[T]
    │   ├── config.py       # 配置层: Pydantic Settings
    │   ├── protocols.py    # 协议层: 接口定义、ServiceLocator
    │   ├── handler.py      # 处理器层: PluginHandler, MessageHandler
    │   ├── receiver.py     # 接收层: CommandReceiver, MessageReceiver
    │   └── services/       # 服务层: 协议实现
    ├── math_definition/    # 数学定义查询
    ├── math_soup/          # 数学谜题游戏
    ├── random_reply/       # 随机回复监听
    ├── high_noon/          # 轮盘赌游戏
    ├── pjskpartition/      # PJSK 谱面获取
    ├── status_control/     # 管理员系统
    └── help/               # 帮助命令
```

### 架构设计

采用 7 层严格分层架构：

```
插件层 → 处理器层 → 接收层 → 协议层 → 服务层 → 基础层 → 配置层
```

- **配置层**: Pydantic Settings 管理，支持环境变量和 `.env` 文件
- **基础层**: `ServiceBase` 单例基类，`Result[T]` 统一错误处理
- **协议层**: Protocol 接口定义，`ServiceLocator` 服务定位器实现解耦
- **服务层**: AIService、BanService、ChatService 等协议实现
- **处理器层**: `PluginHandler` / `MessageHandler` 业务逻辑接口
- **接收层**: `CommandReceiver` / `MessageReceiver` 命令注册与前置检查
- **插件层**: 具体功能实现（数学定义、游戏等）

**独立工具层**: 消息构建、网络请求、图片处理等纯函数工具（无状态，被各层调用）

依赖规则：上层仅依赖协议层，不依赖具体实现；服务层通过 `ServiceLocator` 注册，插件层通过 `ServiceLocator.get(Protocol)` 获取。

## 快速开始

### 环境要求

- Python >= 3.9
- NoneBot2 >= 2.4.0
- OneBot V11 协议适配器
- DeepSeek API 密钥

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/query-bot.git
cd query-bot

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env`，配置以下必需项：

```env
# DeepSeek API 密钥
QUERY_DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 管理员 QQ 号列表（逗号分隔）
QUERY_ADMIN_USER_IDS=123456789,987654321
```

可选配置项：

```env
# 功能开关
QUERY_MATH_ENABLED=True
QUERY_RANDOM_ENABLED=True
QUERY_HIGHNOON_ENABLED=True
QUERY_PJSKPARTTION_ENABLED=True
QUERY_MATH_SOUP_ENABLED=True

# 随机回复概率 (0.0-1.0)
QUERY_RANDOM_REPLY_PROBABILITY=0.02
QUERY_RANDOM_REPLY_PROBABILITY_AT=0.8

# 数据目录
QUERY_DATA_DIR=data
QUERY_MAX_HISTORY_PER_GROUP=50
```

### 启动

```bash
# 使用 nb-cli（推荐，支持热重载）
nb run

# 或热重载模式
nb run --reload

# 或直接运行
python bot.py
```

## 开发指南

### 创建新插件

继承 `CommandPlugin` 基类：

```python
from plugins.common import CommandPlugin, AIService, config

class ExamplePlugin(CommandPlugin):
    name = "示例插件"
    description = "插件功能描述"
    command = "示例"
    feature_name = "example"  # 对应 config.example_enabled
    aliases = {"别名1", "别名2"}
    
    async def handle(self, event, args: str) -> None:
        """处理命令
        
        Args:
            event: MessageEvent 消息事件
            args: 命令参数（已去除首尾空格）
        """
        if not args:
            await self.reply("请输入参数")
            return
        
        # 使用 AI 服务
        ai = AIService.get_instance()
        result = await ai.chat(
            system_prompt="系统提示词",
            user_input=args,
            temperature=0.3
        )
        
        if result.is_success:
            await self.reply(result.value)
        else:
            await self.reply(f"错误: {result.error}")

# 实例化即注册
plugin = ExamplePlugin()
```

基类自动处理：
- 命令处理器注册 (`on_command`)
- 黑名单检查 (`BanService`)
- 功能开关检查 (`config.{feature_name}_enabled`)
- 错误处理和日志记录

### 服务层开发

继承 `ServiceBase` 实现单例服务：

```python
from plugins.common import ServiceBase, Result

class MyService(ServiceBase):
    def __init__(self):
        super().__init__()
        self._data = None
    
    def initialize(self):
        """延迟初始化，首次使用时调用"""
        if self._initialized:
            return
        self._data = self._load_data()
        self._initialized = True
    
    def operation(self) -> Result[str]:
        """返回 Result[T] 替代抛出异常"""
        try:
            result = self._do_something()
            return Result.success(result)
        except Exception as e:
            return Result.fail(f"操作失败: {e}")

# 使用
service = MyService.get_instance()
result = service.operation()
if result.is_success:
    value = result.value
else:
    error = result.error
```

### 配置扩展

在 `plugins/common/config.py` 中添加新配置项：

```python
class PluginConfig(BaseSettings):
    # 现有配置...
    
    # 新增配置
    myfeature_enabled: bool = Field(default=True, description="功能开关")
    myfeature_timeout: int = Field(default=30, gt=0, description="超时时间")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "QUERY_"
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### 生产环境配置

```env
# 关闭调试模式
QUERY_DEBUG_MODE=False

# 降低随机回复频率
QUERY_RANDOM_REPLY_PROBABILITY=0.01
QUERY_RANDOM_REPLY_COOLDOWN=60

# 数据持久化
QUERY_DATA_DIR=/data
```

## 管理员系统

基于一次性令牌的身份验证机制：

1. **申请令牌**: 管理员私聊 `/申请令牌`，获取 5 分钟有效期的随机令牌
2. **执行操作**: 群内发送 `/状态控制 [令牌] [操作] [参数]`
3. **令牌验证**: 一次性使用，验证后立即失效

支持操作：
- `状态` - 查看功能开关状态
- `开关 [功能名]` - 切换功能（math, random, highnoon, pjskpartiton, math_soup）
- `拉黑 [user_id]` - 将用户加入黑名单
- `解封 [user_id]` - 将用户移出黑名单
- `系统` - 查看进程资源使用情况

## 监控

内置 `SystemMonitorService` 提供进程级监控：

```python
from plugins.common import SystemMonitorService

service = SystemMonitorService.get_instance()
status = service.get_status()
# status.cpu_percent      # 进程 CPU 使用率
# status.memory_mb        # 内存使用 (MB)
# status.threads          # 线程数
# status.uptime_seconds   # 运行时间
```

## 依赖

生产依赖：
- `nonebot2[fastapi]>=2.4.0`
- `nonebot-adapter-onebot>=2.4.0`
- `openai>=1.0.0`
- `pydantic-settings>=2.0.0`
- `psutil>=5.9.0`

开发依赖：
- `nb-cli>=1.2.0`

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)

- **v2.2.2**: 7层架构重构, ServiceLocator, Protocol接口, 处理器/接收器分离
- **v2.2.1**: PluginRegistry, TokenService, SystemMonitorService, nb-cli 支持
- **v2.2.0**: 数学谜题插件, GameServiceBase, 325+ 数学概念
- **v2.1.1**: 并发安全修复, BotService API 封装
- **v2.1.0**: ServiceBase, Result[T], PluginBase 架构

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

本项目代码部分使用 [Kimi Code](https://kimi.moonshot.cn/) 辅助编写。

---

<a name="english-documentation"></a>
# English Documentation

A QQ group chat bot based on the NoneBot2 framework, providing mathematical knowledge queries, gaming entertainment, and intelligent conversation capabilities.

## Features

- **Math Definition Query**: Mathematical concept explanations powered by DeepSeek API (Banana Space style)
- **Math Puzzle**: Yes/No answer-asking mode with 325+ mathematical concepts
- **Random Reply**: Context-aware AI group chat replies with configurable trigger probability
- **High Noon**: Russian roulette mute game
- **PJSK Charts**: Random Project Sekai game chart images
- **Status Control**: Admin system based on one-time tokens

## Architecture

```
query-bot/
├── bot.py                  # Application entry point
├── pyproject.toml          # Project config (PEP 621)
├── requirements.txt        # Production dependencies
├── .env.example            # Environment template
├── CHANGELOG.md            # Version changelog
├── data/                   # Runtime data storage
├── prompts/                # LLM system prompts
└── plugins/                # Plugin directory
    ├── common/             # Core infrastructure
    │   ├── base.py         # Base: ServiceBase, Result[T]
    │   ├── config.py       # Config: Pydantic Settings
    │   ├── protocols.py    # Protocol: interfaces & ServiceLocator
    │   ├── handler.py      # Handler: PluginHandler, MessageHandler
    │   ├── receiver.py     # Receiver: CommandReceiver, MessageReceiver
    │   └── services/       # Services: protocol implementations
    ├── math_definition/    # Math query plugin
    ├── math_soup/          # Math puzzle game
    ├── random_reply/       # Random reply listener
    ├── high_noon/          # Roulette game
    ├── pjskpartition/      # PJSK chart fetcher
    ├── status_control/     # Admin system
    └── help/               # Help command
```

### Layered Architecture

- **Config Layer**: Pydantic Settings, supports env vars and `.env` files
- **Service Layer**: ServiceBase singleton pattern, provides AIService, BanService, ChatService, etc.
- **Interface Layer**: CommandPlugin/MessagePlugin base classes with permission checks
- **Utility Layer**: Message building, HTTP requests, image processing

## Quick Start

### Requirements

- Python >= 3.9
- NoneBot2 >= 2.4.0
- OneBot V11 protocol adapter
- DeepSeek API key

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/query-bot.git
cd query-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example config:

```bash
cp .env.example .env
```

Edit `.env` with required settings:

```env
# DeepSeek API key
QUERY_DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Admin QQ numbers (comma-separated)
QUERY_ADMIN_USER_IDS=123456789,987654321
```

Optional settings:

```env
# Feature toggles
QUERY_MATH_ENABLED=True
QUERY_RANDOM_ENABLED=True
QUERY_HIGHNOON_ENABLED=True
QUERY_PJSKPARTTION_ENABLED=True
QUERY_MATH_SOUP_ENABLED=True

# Random reply probability (0.0-1.0)
QUERY_RANDOM_REPLY_PROBABILITY=0.02
QUERY_RANDOM_REPLY_PROBABILITY_AT=0.8

# Data directory
QUERY_DATA_DIR=data
QUERY_MAX_HISTORY_PER_GROUP=50
```

### Start

```bash
# Using nb-cli (recommended, with hot reload)
nb run

# Or hot reload mode
nb run --reload

# Or run directly
python bot.py
```

## Development Guide

### Creating Plugins

Extend `CommandPlugin` base class:

```python
from plugins.common import CommandPlugin, AIService, config

class ExamplePlugin(CommandPlugin):
    name = "Example Plugin"
    description = "Plugin description"
    command = "example"
    feature_name = "example"  # Maps to config.example_enabled
    aliases = {"alias1", "alias2"}
    
    async def handle(self, event, args: str) -> None:
        """Handle command
        
        Args:
            event: MessageEvent
            args: Command arguments (stripped)
        """
        if not args:
            await self.reply("Please input parameters")
            return
        
        # Use AI service
        ai = AIService.get_instance()
        result = await ai.chat(
            system_prompt="System prompt",
            user_input=args,
            temperature=0.3
        )
        
        if result.is_success:
            await self.reply(result.value)
        else:
            await self.reply(f"Error: {result.error}")

# Instantiation registers the plugin
plugin = ExamplePlugin()
```

Base class automatically handles:
- Command handler registration (`on_command`)
- Blacklist checking (`BanService`)
- Feature toggle checking (`config.{feature_name}_enabled`)
- Error handling and logging

### Service Layer Development

Extend `ServiceBase` for singleton services:

```python
from plugins.common import ServiceBase, Result

class MyService(ServiceBase):
    def __init__(self):
        super().__init__()
        self._data = None
    
    def initialize(self):
        """Lazy initialization on first use"""
        if self._initialized:
            return
        self._data = self._load_data()
        self._initialized = True
    
    def operation(self) -> Result[str]:
        """Return Result[T] instead of raising exceptions"""
        try:
            result = self._do_something()
            return Result.success(result)
        except Exception as e:
            return Result.fail(f"Failed: {e}")

# Usage
service = MyService.get_instance()
result = service.operation()
if result.is_success:
    value = result.value
else:
    error = result.error
```

### Configuration Extension

Add new config in `plugins/common/config.py`:

```python
class PluginConfig(BaseSettings):
    # Existing configs...
    
    # New config
    myfeature_enabled: bool = Field(default=True, description="Feature toggle")
    myfeature_timeout: int = Field(default=30, gt=0, description="Timeout seconds")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "QUERY_"
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### Production Configuration

```env
# Disable debug mode
QUERY_DEBUG_MODE=False

# Reduce random reply frequency
QUERY_RANDOM_REPLY_PROBABILITY=0.01
QUERY_RANDOM_REPLY_COOLDOWN=60

# Data persistence
QUERY_DATA_DIR=/data
```

## Admin System

Identity verification based on one-time tokens:

1. **Request Token**: Private chat `/申请令牌` to get a 5-minute random token
2. **Execute**: Group chat `/状态控制 [token] [action] [params]`
3. **Token Expires**: 5 minutes / one-time use

Supported actions:
- `status` - View feature toggle status
- `toggle [feature]` - Toggle feature (math, random, highnoon, pjskpartiton, math_soup)
- `ban [user_id]` - Ban user
- `unban [user_id]` - Unban user
- `system` - View resource usage

## Monitoring

Built-in `SystemMonitorService` provides process-level monitoring:

```python
from plugins.common import SystemMonitorService

service = SystemMonitorService.get_instance()
status = service.get_status()
# status.cpu_percent      # Process CPU usage
# status.memory_mb        # Memory usage (MB)
# status.threads          # Thread count
# status.uptime_seconds   # Uptime
```

## Dependencies

Production:
- `nonebot2[fastapi]>=2.4.0`
- `nonebot-adapter-onebot>=2.4.0`
- `openai>=1.0.0`
- `pydantic-settings>=2.0.0`
- `psutil>=5.9.0`

Development:
- `nb-cli>=1.2.0`

## Version History

See [CHANGELOG.md](CHANGELOG.md)

- **v2.2.1**: PluginRegistry, TokenService, SystemMonitorService, nb-cli support
- **v2.2.0**: Math puzzle plugin, GameServiceBase, 325+ math concepts
- **v2.1.1**: Concurrency safety fix, BotService API encapsulation
- **v2.1.0**: ServiceBase, Result[T], PluginBase architecture

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

Code partially written with assistance from [Kimi Code](https://kimi.moonshot.cn/).
