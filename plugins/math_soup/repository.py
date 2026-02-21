"""
数学谜题插件 - 概念题库

管理数学概念的加载和查询。
"""

import json
import os
import random
from typing import Dict, Optional

from .models import MathConcept


class ConceptRepository:
    """数学概念题库"""
    
    DEFAULT_CONCEPTS = [
        {
            "id": "fermat_last_theorem",
            "answer": "费马大定理",
            "aliases": ["费马最后定理"],
            "category": "数论",
            "tags": ["数论", "证明", "358年"],
            "description": "当整数n>2时，方程a^n+b^n=c^n没有正整数解"
        }
    ]
    
    def __init__(self) -> None:
        self._concepts: Dict[str, MathConcept] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """延迟初始化，加载概念数据"""
        if self._initialized:
            return
        
        data_file = os.path.join("prompts", "math_concepts.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get("concepts", []):
                        concept = MathConcept.from_dict(item)
                        self._concepts[concept.id] = concept
            except Exception:
                self._load_defaults()
        else:
            self._load_defaults()
        
        self._initialized = True
    
    def _load_defaults(self) -> None:
        """加载内置默认概念"""
        for item in self.DEFAULT_CONCEPTS:
            concept = MathConcept.from_dict(item)
            self._concepts[concept.id] = concept
    
    def get_random_concept(self) -> Optional[MathConcept]:
        """随机获取一个数学概念"""
        self.initialize()
        concepts = list(self._concepts.values())
        if not concepts:
            return None
        return random.choice(concepts)
    
    def get_concept_count(self) -> int:
        """获取概念总数"""
        self.initialize()
        return len(self._concepts)
