"""GameTree v1 运行时契约。

向外暴露 contracts 模块的核心类。播放器从 JSON 直接 load 故事树,
不再经过 SQLite/DialogueTreeLoader(那条路径已随 LLM 生成流水线归档到
`legacy/llm-pipeline` 分支)。
"""

from .contracts import EffectApplier, EndingResolver, RequirementEvaluator

__all__ = ["EffectApplier", "EndingResolver", "RequirementEvaluator"]
