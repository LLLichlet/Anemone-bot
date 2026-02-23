"""
文本处理工具模块

提供文本标准化、相似度计算等纯函数工具。
"""

import difflib
import re
from typing import List


# ========== 文本标准化常量 ==========

# 需要移除的标点符号和特殊字符
NORMALIZABLE_CHARS = " ·•-ˈ·•\u00b7\u2022\u2219"

# 字符串相似度计算常量
class SimilarityConstants:
    """字符串相似度计算使用的常量"""
    
    # 完全匹配的相似度值
    EXACT_MATCH = 100.0
    
    # 子串匹配的基础分（一方是另一方的子串）
    SUBSTRING_BASE = 70.0
    
    # 子串匹配的额外分数比例系数（根据长度比例增加）
    SUBSTRING_BONUS_FACTOR = 25.0
    
    # 短字符串阈值（长度小于等于此值的字符串使用特殊处理）
    SHORT_STRING_THRESHOLD = 4
    
    # 短字符串的相似度比例阈值（低于此值应用惩罚）
    SHORT_STRING_RATIO_THRESHOLD = 0.8
    
    # 短字符串相似度惩罚系数
    SHORT_STRING_PENALTY_FACTOR = 80.0


# ========== 文本标准化函数 ==========

def normalize_text(text: str) -> str:
    """
    标准化文本，用于比较
    
    移除空格、特殊标点，转为小写。
    
    Args:
        text: 原始文本
        
    Returns:
        标准化后的文本
        
    Example:
        >>> normalize_text("Hello · World")
        'helloworld'
        >>> normalize_text("群论·定义")
        '群论定义'
    """
    if not text:
        return ""
    
    result = text.lower()
    for char in NORMALIZABLE_CHARS:
        result = result.replace(char, "")
    return result


def normalize_texts(texts: List[str]) -> List[str]:
    """
    批量标准化文本
    
    Args:
        texts: 文本列表
        
    Returns:
        标准化后的文本列表
    """
    return [normalize_text(t) for t in texts]


# ========== 相似度计算函数 ==========

def calculate_similarity(s1: str, s2: str) -> float:
    """
    计算两个字符串的相似度（0-100%）
    
    使用改进的算法：
    1. 完全匹配返回 100.0
    2. 子串匹配返回 70-95 分（根据长度比例）
    3. 其他情况使用 difflib.SequenceMatcher
    4. 短字符串（<=4字符）相似度低于 0.8 时应用惩罚
    
    Args:
        s1: 第一个字符串
        s2: 第二个字符串
        
    Returns:
        相似度分数（0.0 - 100.0）
        
    Example:
        >>> calculate_similarity("hello", "hello")
        100.0
        >>> calculate_similarity("群论", "群论的定义")
        85.0  # 子串匹配，4/6 * 25 + 70
    """
    s1_clean = normalize_text(s1)
    s2_clean = normalize_text(s2)
    
    if not s1_clean or not s2_clean:
        return 0.0
    
    # 完全匹配
    if s1_clean == s2_clean:
        return SimilarityConstants.EXACT_MATCH
    
    const = SimilarityConstants()
    
    # 子串匹配（一方包含另一方）
    if s1_clean in s2_clean or s2_clean in s1_clean:
        shorter = min(len(s1_clean), len(s2_clean))
        longer = max(len(s1_clean), len(s2_clean))
        # 基础分 + 根据覆盖比例的额外分数
        return const.SUBSTRING_BASE + const.SUBSTRING_BONUS_FACTOR * (shorter / longer)
    
    # 使用 difflib 计算相似度
    matcher = difflib.SequenceMatcher(None, s1_clean, s2_clean)
    ratio = matcher.ratio()
    
    # 短字符串特殊处理：相似度低的应用惩罚
    if len(s1_clean) <= const.SHORT_STRING_THRESHOLD or len(s2_clean) <= const.SHORT_STRING_THRESHOLD:
        if ratio < const.SHORT_STRING_RATIO_THRESHOLD:
            return ratio * const.SHORT_STRING_PENALTY_FACTOR
    
    return ratio * 100


def find_best_match(text: str, candidates: List[str]) -> tuple[str, float]:
    """
    在候选列表中找到最佳匹配
    
    Args:
        text: 要匹配的文本
        candidates: 候选文本列表
        
    Returns:
        (最佳匹配的候选, 相似度分数)
        
    Example:
        >>> find_best_match("群论", ["群论", "环论", "域论"])
        ('群论', 100.0)
    """
    if not candidates:
        return ("", 0.0)
    
    best_candidate = candidates[0]
    best_score = calculate_similarity(text, candidates[0])
    
    for candidate in candidates[1:]:
        score = calculate_similarity(text, candidate)
        if score > best_score:
            best_score = score
            best_candidate = candidate
    
    return (best_candidate, best_score)


def is_text_match(text: str, target: str, threshold: float = 90.0) -> bool:
    """
    判断文本是否匹配目标（考虑别名）
    
    Args:
        text: 输入文本
        target: 目标文本
        threshold: 相似度阈值（默认90%）
        
    Returns:
        是否匹配
    """
    return calculate_similarity(text, target) >= threshold


# ========== 导出 ==========

__all__ = [
    # 常量
    "NORMALIZABLE_CHARS",
    "SimilarityConstants",
    # 文本标准化
    "normalize_text",
    "normalize_texts",
    # 相似度计算
    "calculate_similarity",
    "find_best_match",
    "is_text_match",
]
