"""
数据模型定义

使用 dataclass 定义数据结构，对应数据库表
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class City:
    """城市数据模型"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    story_count: int = 0  # 该城市的故事数量（查询时填充）

    @classmethod
    def from_db_row(cls, row: Dict) -> 'City':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            name=row.get('name', ''),
            description=row.get('description'),
            created_at=row.get('created_at'),
            story_count=row.get('story_count', 0)
        )


@dataclass
class Story:
    """故事数据模型"""
    id: Optional[int] = None
    city_id: int = 0
    title: str = ""
    synopsis: str = ""
    estimated_duration_minutes: int = 0
    total_nodes: int = 0
    max_depth: int = 0
    generation_cost_usd: float = 0.0
    created_at: Optional[datetime] = None
    character_count: int = 0  # 角色数量（查询时填充）

    @classmethod
    def from_db_row(cls, row: Dict) -> 'Story':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            city_id=row.get('city_id', 0),
            title=row.get('title', ''),
            synopsis=row.get('synopsis', ''),
            estimated_duration_minutes=row.get('estimated_duration_minutes', 0),
            total_nodes=row.get('total_nodes', 0),
            max_depth=row.get('max_depth', 0),
            generation_cost_usd=row.get('generation_cost_usd', 0.0),
            created_at=row.get('created_at'),
            character_count=row.get('character_count', 0)
        )


@dataclass
class Character:
    """角色数据模型"""
    id: Optional[int] = None
    story_id: int = 0
    name: str = ""
    is_protagonist: bool = False
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Dict) -> 'Character':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            story_id=row.get('story_id', 0),
            name=row.get('name', ''),
            is_protagonist=bool(row.get('is_protagonist', 0)),
            description=row.get('description'),
            created_at=row.get('created_at')
        )


@dataclass
class DialogueTree:
    """对话树数据模型"""
    id: Optional[int] = None
    story_id: int = 0
    character_id: int = 0
    tree_data: Dict[str, Any] = field(default_factory=dict)  # 完整对话树
    compressed: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Dict, tree_data: Dict = None) -> 'DialogueTree':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            story_id=row.get('story_id', 0),
            character_id=row.get('character_id', 0),
            tree_data=tree_data or {},
            compressed=bool(row.get('compressed', 0)),
            created_at=row.get('created_at')
        )


@dataclass
class GenerationMetadata:
    """生成元数据模型"""
    id: Optional[int] = None
    story_id: int = 0
    total_tokens: int = 0
    generation_time_seconds: int = 0
    model_used: str = ""
    generated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Dict) -> 'GenerationMetadata':
        """从数据库行创建实例"""
        return cls(
            id=row.get('id'),
            story_id=row.get('story_id', 0),
            total_tokens=row.get('total_tokens', 0),
            generation_time_seconds=row.get('generation_time_seconds', 0),
            model_used=row.get('model_used', ''),
            generated_at=row.get('generated_at')
        )

