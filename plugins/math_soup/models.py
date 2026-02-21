"""
数学谜题插件 - 数据模型

定义游戏所需的数据结构。
"""

from typing import Optional, List
from dataclasses import dataclass, field

from plugins.common import GameState


@dataclass
class MathConcept:
    """数学概念数据类"""
    id: str
    answer: str
    aliases: List[str] = field(default_factory=list)
    category: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathConcept":
        """从字典创建对象"""
        return cls(
            id=data["id"],
            answer=data["answer"],
            aliases=data.get("aliases", []),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            description=data.get("description", "")
        )


@dataclass
class MathPuzzleState(GameState):
    """数学谜题游戏状态"""
    concept: Optional[MathConcept] = None
    question_count: int = 0
    guess_count: int = 0
    history: List[tuple] = field(default_factory=list)
