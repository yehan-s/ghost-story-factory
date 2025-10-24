"""
进度追踪器

负责显示生成进度、估算剩余时间、保存检查点
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn


class ProgressTracker:
    """进度追踪器"""

    def __init__(self, total_estimated_nodes: int = 1500):
        """
        初始化进度追踪器

        Args:
            total_estimated_nodes: 预计总节点数
        """
        self.console = Console()
        self.total_estimated_nodes = total_estimated_nodes
        self.generated_nodes = 0
        self.start_time = time.time()
        self.current_depth = 0
        self.max_depth = 20

        # Token 统计
        self.total_tokens = 0

        # 进度条
        self.progress = None
        self.task_id = None

    def start(self, max_depth: int = 20, test_mode: bool = False):
        """
        开始追踪

        Args:
            max_depth: 最大深度
            test_mode: 是否为测试模式
        """
        self.max_depth = max_depth
        self.start_time = time.time()

        self.console.print("\n")
        self.console.print("╔══════════════════════════════════════════════════════════════════╗", style="bold blue")
        if test_mode:
            self.console.print("║              🧪 生成测试对话树 (MVP)                            ║", style="bold green")
        else:
            self.console.print("║              🚀 开始生成完整故事对话树                          ║", style="bold blue")
        self.console.print("╚══════════════════════════════════════════════════════════════════╝", style="bold blue")
        self.console.print("\n")

        if test_mode:
            self.console.print(f"⚡ [bold green][测试模式] 预计时间: 3-5 分钟 (单个角色)[/bold green]")
        else:
            self.console.print(f"⚠️  [bold yellow]注意：生成过程预计 2-4 小时，请勿中断！[/bold yellow]")
            self.console.print(f"⚠️  [bold yellow]关闭窗口或强制退出将导致生成失败，需重新开始！[/bold yellow]")

        self.console.print("\n")

        # 创建进度条
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        self.task_id = self.progress.add_task(
            "[cyan]生成对话树节点...",
            total=self.total_estimated_nodes
        )
        self.progress.start()

    def update(
        self,
        current_depth: int,
        node_count: int,
        current_branch: str = "",
        tokens_used: int = 0
    ):
        """
        更新进度

        Args:
            current_depth: 当前深度
            node_count: 已生成节点数
            current_branch: 当前分支描述
            tokens_used: 本次使用的 Token 数
        """
        self.current_depth = current_depth
        self.generated_nodes = node_count
        self.total_tokens += tokens_used

        # 更新进度条
        if self.progress and self.task_id is not None:
            self.progress.update(
                self.task_id,
                completed=node_count,
                description=f"[cyan]深度 {current_depth}/{self.max_depth} | 节点 {node_count} | {current_branch}"
            )

    def update_total_estimate(self, new_estimate: int):
        """
        更新总节点数估算

        Args:
            new_estimate: 新的估算值
        """
        self.total_estimated_nodes = new_estimate
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, total=new_estimate)

    def show_stats(self):
        """显示详细统计信息"""
        elapsed = time.time() - self.start_time
        speed = self.generated_nodes / elapsed if elapsed > 0 else 0
        remaining = (self.total_estimated_nodes - self.generated_nodes) / speed if speed > 0 else 0

        eta = datetime.now() + timedelta(seconds=remaining)

        self.console.print("\n")
        self.console.print("┌─────────────────────────────────────────────────────────┐", style="dim")
        self.console.print(f"│ 当前深度: {self.current_depth}/{self.max_depth}                          │", style="dim")
        self.console.print(f"│ 已生成节点: {self.generated_nodes}/{self.total_estimated_nodes}                       │", style="dim")
        self.console.print(f"│ 已用 Token: {self.total_tokens:,}                            │", style="dim")
        self.console.print(f"│ 预计完成时间: {eta.strftime('%H:%M:%S')}                      │", style="dim")
        self.console.print("└─────────────────────────────────────────────────────────┘", style="dim")
        self.console.print("\n")

    def save_checkpoint(self, tree: Dict[str, Any], checkpoint_path: str = "checkpoint.json"):
        """
        保存检查点

        Args:
            tree: 当前对话树
            checkpoint_path: 检查点文件路径
        """
        checkpoint = {
            "generated_at": datetime.now().isoformat(),
            "nodes_count": self.generated_nodes,
            "current_depth": self.current_depth,
            "total_tokens": self.total_tokens,
            "elapsed_time": time.time() - self.start_time,
            "tree": tree
        }

        checkpoint_file = Path(checkpoint_path)
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        self.console.print(f"💾 [dim]检查点已保存：{checkpoint_path}[/dim]")

    def load_checkpoint(self, checkpoint_path: str = "checkpoint.json") -> Optional[Dict[str, Any]]:
        """
        加载检查点

        Args:
            checkpoint_path: 检查点文件路径

        Returns:
            检查点数据（如果存在）
        """
        checkpoint_file = Path(checkpoint_path)
        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        self.generated_nodes = checkpoint.get("nodes_count", 0)
        self.current_depth = checkpoint.get("current_depth", 0)
        self.total_tokens = checkpoint.get("total_tokens", 0)

        self.console.print(f"✅ [green]检查点已加载：{checkpoint_path}[/green]")
        self.console.print(f"   已生成 {self.generated_nodes} 个节点，深度 {self.current_depth}")

        return checkpoint.get("tree")

    def finish(self, success: bool = True):
        """
        完成追踪

        Args:
            success: 是否成功
        """
        if self.progress:
            self.progress.stop()

        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)

        self.console.print("\n")
        if success:
            self.console.print("╔══════════════════════════════════════════════════════════════════╗", style="bold green")
            self.console.print("║              ✅ 故事生成完成！                                  ║", style="bold green")
            self.console.print("╚══════════════════════════════════════════════════════════════════╝", style="bold green")
        else:
            self.console.print("╔══════════════════════════════════════════════════════════════════╗", style="bold red")
            self.console.print("║              ❌ 生成失败                                        ║", style="bold red")
            self.console.print("╚══════════════════════════════════════════════════════════════════╝", style="bold red")

        self.console.print("\n")
        self.console.print(f"生成节点数: [bold]{self.generated_nodes}[/bold] 个")
        self.console.print(f"最大深度: [bold]{self.current_depth}[/bold] 层")
        self.console.print(f"总 Token: [bold]{self.total_tokens:,}[/bold]")
        self.console.print(f"总耗时: [bold]{hours}小时 {minutes}分 {seconds}秒[/bold]")
        self.console.print("\n")

