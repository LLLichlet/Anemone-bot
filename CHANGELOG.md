# 版本更新日志 (Changelog)

本文档记录 Anemone bot 的所有版本更新历史。

完整项目信息请参见 [README.md](README.md)。

---

### Version 2.3.0 (2026-02-26)

**新功能**

- 新增**复读插件** (`plugins/echo/`)：随机复读群聊消息，有概率倒着复读
  - 配置项 `echo_probability`：复读概率（默认 1%）
  - 配置项 `echo_reverse_probability`：倒序复读概率（默认 20%）

**功能调整**

- **随机回复插件**逻辑调整：
  - 移除随机概率回复机制
  - 现在只在被@或消息包含关键词 ("ane"/"anem"/"anemone") 时回复
  - 移除相关配置项：`random_reply_probability`, `random_reply_probability_at`, `random_reply_cooldown`, `random_reply_min_length`

---

### Version 2.2.6 (2026-02-25)

**Bug修复**

- 修复消息发送并发bug：使用 ContextVar 隔离请求上下文，解决多请求共享 `_current_matcher` 导致的消息丢失问题
- 重构 `SendBuffer`：改用 `asyncio.Lock` 替代后台 task，在调用者上下文中执行发送，避免 ContextVar 丢失

---

### Version 2.2.5 (2026-02-24)

**品牌更新**

- 项目正式更名为 **Anemone bot**
- 更新所有相关文档和配置文件中的项目名称

**命令国际化**

- 所有插件命令改为英文，原中文命令作为别名保留
  - 数学定义: `/define` (别名: `/定义`)
  - 数学谜题: `/mathpuzzle` (别名: `/数学谜`), `/ask` (别名: `/问`), `/guess` (别名: `/猜`), `/reveal` (别名: `/答案`)
  - 午时已到: `/highnoon` (别名: `/午时已到`), `/fire` (别名: `/开枪`)
  - PJSK: `/chart` (别名: `/pjsk随机谱面`)
  - 状态控制: `/token` (别名: `/申请令牌`), `/admin` (别名: `/状态控制`), 子指令: `toggle`/`ban`/`unban`/`status`/`system`
- 帮助: 支持 `/help 指令名/别名` 查看指定指令的详细信息
  - 帮助: `/help` (别名: `/帮助`)

---

### Version 2.2.4 (2026-02-23)

**代码精简与优化**

- `Result[T]` 改用 dataclass 实现，代码量减少 50%
- 简化 `PluginHandler` API：`send()` / `reply()` 统一，支持 `finish` 参数
- 移除 `ConfigProvider` 服务层，直接使用 `config` 对象
- 集中导入保护到 `compat.py`，消除重复代码
- 清理未使用的函数和过度封装（-19% 代码量）

---

### Version 2.2.3 (2026-02-23)

**Bug 修复**
- 修复数学谜题猜对后无法自动结束游戏的问题：`make_guess` 中缺少 `await self.end_game()`
- 修复私聊消息触发群聊处理器的问题：`MessageReceiver` 添加 `isinstance(event, GroupMessageEvent)` 检查

**优化**
- 简化数学谜题 AI 提示词：移除历史问答记录，减少 token 消耗
- 移除 `MathPuzzleState` 中的 `history` 字段及相关代码

---

### Version 2.2.2 (2026-02-21)

**重构完成**

**架构升级**
- 完成 7 层严格分层架构：配置层 → 基础层 → 协议层 → 服务层 → 处理器层 → 接收层 → 插件层
- 引入协议接口（Protocol）：所有服务定义抽象协议，实现与使用完全解耦
- 引入 `ServiceLocator` 服务定位器：统一服务注册与查找，支持类型安全的通用查询
- 拆分 `receiver.py` 为 `handler.py` + `receiver.py`：业务逻辑与命令接收完全分离
- 重命名 `cfgprov.py` 为 `provider.py`：代码结构更清晰

**服务注册机制**
- 所有服务在 `initialize()` 中注册到 `ServiceLocator`，而非 `__init__`
- `bot.py` 启动时自动初始化所有核心服务
- `receiver` 层添加 `_ensure_service_initialized()` 保险机制，确保服务可用

**插件架构**
- 插件通过 `ServiceLocator.get(Protocol)` 访问服务，禁止直接 `XxxService.get_instance()`
- `PluginHandler` 与 `MessageHandler` 定义业务逻辑接口
- `CommandReceiver` 与 `MessageReceiver` 负责命令注册和前置检查

**工具新增**
- 新增 `utils/prompt.py`：`read_prompt()` 函数读取 `prompts/` 目录下的提示词文件

---

### Version 2.2.1 (2026-02-20)

**新功能**
- 新增「状态控制」插件（重构原管理员系统）
  - 一次性令牌验证：私聊申请令牌，5分钟有效期，使用一次即失效
  - 管理员白名单机制：通过 `QUERY_ADMIN_USER_IDS` 配置
  - 四个操作：`状态`（查看开关）、`开关`（切换功能）、`拉黑`/`解封`（用户管理）、`系统`（监控资源）
- 新增 `TokenService` 服务：安全的短期令牌生成与验证
- 新增 `SystemMonitorService` 服务：监控 bot 进程的 CPU、内存、线程数、运行时间
- 新增 `PluginRegistry` 服务：自动收集插件元数据，帮助系统动态生成
- 支持 nb-cli 启动：`nb run` / `nb run --reload` 热重载

**架构改进**
- 重构帮助插件：从 PluginRegistry 自动读取插件信息，无需手动维护
- 插件基类新增 `hidden_in_help` 属性：隐藏功能不在帮助中显示
- 统一版本管理：所有模块版本号同步

---

### Version 2.2.0 (2026-02-20)

**新功能**
- 新增「数学谜题」插件 (`/数学谜`)
  - 20 Questions 游戏模式：AI 想一个数学概念，玩家通过是/否/不确定问题猜测
  - 支持 325+ 数学概念：涵盖拓扑学（95个）、代数学（94个）、数学分析（136个）
  - 文本相似度判定：猜测相似度 > 50% 提示"很接近了"
  - 无次数限制，可无限提问
  - 四个命令：`/数学谜` 开始、`/问` 提问、`/猜` 猜测、`/答案` 揭示

**架构改进**
- 新增 `GameServiceBase` 统一游戏状态管理基类
  - 支持多群同时游戏，每群独立状态
  - 单例模式确保状态一致性
  - 泛型设计支持自定义游戏状态类型
  - 重构 `high_noon` 插件使用新基类

**开发体验**
- 新增调试模式配置 (`debug_mode`, `debug_math_soup`, `debug_highnoon`)

---

### Version 2.1.1 (2026-02-17)

**Bug 修复**
- 修复并发竞争条件：使用 `contextvars` 确保多用户同时请求时回复正确 @ 对应用户
- 修复插件直接调用 NoneBot API 的问题，统一通过 `BotService` 调用

**架构完善**
- 新增 `BotService` 服务层，封装所有 Bot API（禁言、群成员管理等）
- 重构 `high_noon` 和 `hidden_operator` 插件，使用 `CommandPlugin` 基类
- 统一消息构建，使用 `build_at_message` 工具函数

**代码质量**
- 所有插件现在严格建立在封装 API 之上，无直接底层调用
- 完善错误处理，服务层统一返回 `Result[T]` 类型

---

### Version 2.1.0 (2026-02-16)

**架构升级**
- 引入 `ServiceBase` 基类，统一服务单例管理
- 引入 `Result[T]` 类型，替代异常的错误处理方式
- 引入 `PluginBase`、`CommandPlugin`、`MessagePlugin` 基类，大幅简化插件开发
- 服务层返回 `Result` 类型，错误处理更明确

**性能优化**
- AI 服务改用 `AsyncOpenAI`，异步调用不阻塞事件循环
- 网络请求支持异步版本（`fetch_html_async`、`download_image_async`）
- 新增 `HttpClient` 连接池类，支持复用连接

**开发体验**
- 插件开发从繁琐的样板代码变为简单的类定义
- 基类自动处理权限检查、功能开关、错误处理
- 完整的类型提示支持

---

### Version 2.0.0 (2026-02-16)

**重大架构重构**
- 引入分层架构：配置层、服务层、接口层、工具层
- 新增服务层：`AIService`、`BanService`、`ChatService`
- 新增装饰器层：`CommandGuard`、`PermissionChecker`、`FeatureChecker`
- 新增依赖注入支持，兼容 NoneBot 原生 `Depends()`
- 工具层抽离：消息构建、网络请求、图片处理

**功能改进**
- 黑名单管理改为 JSON 格式，自动迁移旧版 pickle 数据
- 聊天记录支持上下文获取，用于 AI 回复
- 配置管理改用 Pydantic Settings，支持环境变量

---

### Version 1.2.0 (*)

**新功能**
- 新增 `/pjsk随机谱面` 命令，获取 Project Sekai 游戏随机谱面图片
- 支持图片下载、合并、发送

---

### Version 1.1.2 (*)

**Bug 修复**
- 修复若干稳定性问题

---

### Version 1.1.1 (*)

**改进**
- 更新帮助文档，动态显示功能开关状态
- 新增功能管理系统，支持通过命令启用/禁用功能

---

### Version 1.1.0 (*)

**新功能**
- 新增随机回复功能，机器人小概率随机回复群聊消息
- 新增被@后回复功能，被@时高概率回复
- 新增 `/午时已到` + `/开枪` 俄罗斯轮盘赌禁言游戏

**移除**
- 移除凯尔希聊天功能

---

### Version 1.0.0 (*)

**初始版本**
- 支持 `/定义 [数学名词]` 查询数学定义（香蕉空间风格）
- 支持凯尔希角色聊天（后移除）

---

**最新版本**: 2.3.0  
查看完整项目信息：[README.md](README.md)


