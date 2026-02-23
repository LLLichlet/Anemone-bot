"""
基础模块 - 服务基类和通用基础设施

提供统一的服务基类、错误处理和日志系统。
所有服务应继承 ServiceBase，所有可能失败的操作应返回 Result[T]。

快速开始:
    >>> from plugins.common.base import ServiceBase, Result
    
    >>> # 创建服务
    >>> class MyService(ServiceBase):
    ...     def initialize(self):
    ...         # 初始化逻辑
    ...         pass
    
    >>> # 使用服务
    >>> service = MyService.get_instance()
    
    >>> # 使用 Result
    >>> def divide(a, b) -> Result[float]:
    ...     if b == 0:
    ...         return Result.fail("除数不能为0")
    ...     return Result.success(a / b)
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import TypeVar, Generic, Optional, Type, Callable
import logging

T = TypeVar('T', bound='ServiceBase')


class ServiceBase(ABC):
    """
    服务基类 - 统一管理单例模式和生命周期
    
    所有服务应继承此类，自动获得：
    - 单例模式管理（全局唯一实例）
    - 延迟初始化（首次使用时初始化）
    - 日志记录器
    - 初始化状态追踪
    
    使用方式:
        >>> class DatabaseService(ServiceBase):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.connection = None
        ...     
        ...     def initialize(self):
        ...         # 延迟初始化，避免启动时耗时
        ...         if self._initialized:
        ...             return
        ...         self.connection = create_connection()
        ...         self._initialized = True
        
        >>> # 获取实例（始终返回同一对象）
        >>> db = DatabaseService.get_instance()
        >>> db2 = DatabaseService.get_instance()
        >>> assert db is db2  # True
    
    Attributes:
        _instances: 类级别的实例字典，存储所有服务的单例
        _initialized: 实例是否已初始化
        logger: 日志记录器，自动创建
    """
    
    _instances: dict[Type, 'ServiceBase'] = {}
    _logger_name = "plugins.common.services"
    
    def __init__(self) -> None:
        """初始化服务基类，子类必须调用 super().__init__()"""
        self._initialized = False
        self.logger = logging.getLogger(self._logger_name)
    
    @classmethod
    def get_instance(cls: Type[T]) -> T:
        """
        获取服务单例实例
        
        这是获取服务实例的唯一方式，确保全局只有一个实例。
        首次调用时会创建实例，后续调用返回已创建的实例。
        
        Returns:
            服务的单例实例
            
        Example:
            >>> ai = AIService.get_instance()
            >>> ban = BanService.get_instance()
        """
        if cls not in cls._instances:
            cls._instances[cls] = cls()
        return cls._instances[cls] # type: ignore
    
    @property
    def is_initialized(self) -> bool:
        """检查服务是否已初始化（只读）"""
        return self._initialized
    
    def ensure_initialized(self) -> None:
        """
        确保服务已初始化
        
        如果未初始化，自动调用 initialize() 方法。
        通常在服务方法开头调用，确保状态正确。
        
        Example:
            >>> def query(self, sql):
            ...     self.ensure_initialized()  # 确保已连接
            ...     return self.connection.execute(sql)
        """
        if not self._initialized:
            self.initialize()
    
    def initialize(self) -> None:
        """
        初始化服务（子类应重写）
        
        在这里执行实际的初始化逻辑，如连接数据库、加载配置等。
        必须检查 self._initialized 避免重复初始化。
        
        注意：
        - 不要直接在 __init__ 中执行耗时操作
        - 多次调用应无副作用（幂等）
        
        Example:
            >>> def initialize(self):
            ...     if self._initialized:
            ...         return
            ...     self.data = load_data()  # 耗时操作
            ...     self._initialized = True
            ...     self.logger.info("Service initialized")
        """
        self._initialized = True
    
    def reset(self) -> None:
        """
        重置服务状态（用于测试）
        
        清除初始化状态，下次使用时会重新初始化。
        警告：生产环境慎用，可能导致状态丢失。
        """
        self._initialized = False


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """
    操作结果封装 - 替代异常的错误处理方式
    
    封装操作成功/失败状态和返回值，使错误处理显式化。
    
    Example:
        >>> return Result.ok(value)
        >>> return Result.err("error message")
        >>> if result:  # 布尔判断
        ...     print(result.value)
    """
    value: Optional[T] = None
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """操作是否成功"""
        return self.error is None
    
    @property
    def is_failure(self) -> bool:
        """操作是否失败"""
        return self.error is not None
    
    def __bool__(self) -> bool:
        """布尔值判断"""
        return self.is_success
    
    def unwrap(self) -> T:
        """解包值，失败时抛出 RuntimeError"""
        if self.is_failure:
            raise RuntimeError(f"Cannot unwrap failed result: {self.error}")
        return self.value  # type: ignore
    
    def unwrap_or(self, default: T) -> T:
        """解包值，失败返回默认值"""
        return self.value if self.is_success else default  # type: ignore
    
    @classmethod
    def ok(cls, value: T) -> 'Result[T]':
        """创建成功结果"""
        return cls(value=value)
    
    @classmethod
    def err(cls, error: str) -> 'Result[T]':
        """创建失败结果"""
        return cls(error=error)
    
    # 保留旧接口向后兼容
    success = ok
    fail = err


def safe_call(func: Callable, *args, error_msg: str = "Operation failed", **kwargs) -> Result[T]: # type: ignore
    """
    安全调用函数，捕获异常并返回 Result
    
    将可能抛出异常的函数包装为返回 Result 的函数。
    
    Args:
        func: 要调用的函数
        *args: 位置参数
        error_msg: 错误信息前缀
        **kwargs: 关键字参数
        
    Returns:
        封装了结果或错误的 Result 对象
        
    Example:
        >>> def risky_divide(a, b):
        ...     return a / b  # 可能抛出 ZeroDivisionError
        ...
        >>> result = safe_call(risky_divide, 10, 0, error_msg="除法失败")
        >>> if not result.is_success:
        ...     print(result.error)  # "除法失败: division by zero"
    """
    try:
        result = func(*args, **kwargs)
        return Result.success(result)
    except Exception as e:
        return Result.fail(f"{error_msg}: {e}")
