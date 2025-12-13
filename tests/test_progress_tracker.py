"""
ProgressTracker 单元测试

测试进度追踪器的核心功能。
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from ghost_story_factory.pregenerator.progress_tracker import ProgressTracker


class TestProgressTracker:
    """ProgressTracker 测试套件"""

    def test_initialization(self):
        """测试初始化"""
        tracker = ProgressTracker(total_estimated_nodes=2000)

        assert tracker.total_estimated_nodes == 2000
        assert tracker.generated_nodes == 0
        assert tracker.current_depth == 0
        assert tracker.total_tokens == 0
        assert tracker.max_depth == 20

    def test_start_normal_mode(self):
        """测试开始追踪（正常模式）"""
        tracker = ProgressTracker()
        tracker.start(max_depth=30, test_mode=False)

        assert tracker.max_depth == 30
        assert tracker.start_time > 0
        # 进度条应该已启动（如果 rich 可用）

    def test_start_test_mode(self):
        """测试开始追踪（测试模式）"""
        tracker = ProgressTracker()
        tracker.start(max_depth=10, test_mode=True)

        assert tracker.max_depth == 10
        assert tracker.start_time > 0

    def test_update_progress(self):
        """测试更新进度"""
        tracker = ProgressTracker(total_estimated_nodes=1000)
        tracker.start()

        tracker.update(
            current_depth=5,
            node_count=100,
            current_branch="S1 -> S2",
            tokens_used=500
        )

        assert tracker.current_depth == 5
        assert tracker.generated_nodes == 100
        assert tracker.total_tokens == 500

    def test_update_total_estimate(self):
        """测试更新总节点数估算"""
        tracker = ProgressTracker(total_estimated_nodes=1000)
        tracker.start()

        tracker.update_total_estimate(1500)

        assert tracker.total_estimated_nodes == 1500

    def test_token_accumulation(self):
        """测试 Token 累计统计"""
        tracker = ProgressTracker()
        tracker.start()

        tracker.update(1, 10, tokens_used=100)
        tracker.update(2, 20, tokens_used=150)
        tracker.update(3, 30, tokens_used=200)

        assert tracker.total_tokens == 450

    def test_save_checkpoint(self):
        """测试保存检查点"""
        tracker = ProgressTracker()
        tracker.start()

        # 模拟生成进度
        tracker.update(5, 50, tokens_used=1000)

        # 保存检查点
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "test_checkpoint.json"

            test_tree = {
                "root": {"node_id": "root", "depth": 0},
                "node_001": {"node_id": "node_001", "depth": 1}
            }

            tracker.save_checkpoint(test_tree, str(checkpoint_path))

            # 验证文件存在
            assert checkpoint_path.exists()

            # 验证文件内容
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data["nodes_count"] == 50
            assert data["current_depth"] == 5
            assert data["total_tokens"] == 1000
            assert "tree" in data

    def test_load_checkpoint(self):
        """测试加载检查点"""
        tracker = ProgressTracker()

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "test_checkpoint.json"

            # 创建测试检查点
            checkpoint_data = {
                "generated_at": "2025-12-14T10:00:00",
                "nodes_count": 75,
                "current_depth": 8,
                "total_tokens": 1500,
                "elapsed_time": 3600,
                "tree": {
                    "root": {"node_id": "root", "depth": 0},
                    "node_001": {"node_id": "node_001", "depth": 1}
                }
            }

            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f)

            # 加载检查点
            tree = tracker.load_checkpoint(str(checkpoint_path))

            assert tree is not None
            assert tracker.generated_nodes == 75
            assert tracker.current_depth == 8
            assert tracker.total_tokens == 1500
            assert "root" in tree

    def test_load_nonexistent_checkpoint(self):
        """测试加载不存在的检查点"""
        tracker = ProgressTracker()

        result = tracker.load_checkpoint("/tmp/nonexistent_checkpoint.json")

        assert result is None

    def test_load_full_checkpoint_complete_structure(self):
        """测试加载完整检查点（完整结构）"""
        tracker = ProgressTracker()

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "full_checkpoint.json"

            # 创建完整结构的检查点
            full_checkpoint = {
                "generated_at": "2025-12-14T10:00:00",
                "nodes_count": 100,
                "current_depth": 10,
                "total_tokens": 2000,
                "tree": {
                    "root": {"node_id": "root", "depth": 0}
                },
                "queue": [{"node_id": "node_100", "depth": 10}],
                "node_counter": 100,
                "state_cache": {},
                "scene_index": {}
            }

            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(full_checkpoint, f)

            # 加载完整检查点
            result = tracker.load_full_checkpoint(str(checkpoint_path))

            assert result is not None
            assert result["node_counter"] == 100
            assert "queue" in result
            assert tracker.generated_nodes == 100
            assert tracker.current_depth == 10

    def test_load_full_checkpoint_simplified_structure(self):
        """测试加载完整检查点（简化结构）"""
        tracker = ProgressTracker()

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "simple_checkpoint.json"

            # 创建简化结构的检查点（旧版格式）
            simple_checkpoint = {
                "root": {"node_id": "root", "depth": 0},
                "node_001": {"node_id": "node_001", "depth": 1},
                "node_002": {"node_id": "node_002", "depth": 2}
            }

            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(simple_checkpoint, f)

            # 加载简化检查点
            result = tracker.load_full_checkpoint(str(checkpoint_path))

            assert result is not None
            assert "tree" in result
            assert result["nodes_count"] == 3
            assert "queue" in result
            assert tracker.generated_nodes == 3

    def test_show_stats(self):
        """测试显示统计信息"""
        tracker = ProgressTracker(total_estimated_nodes=1000)
        tracker.start()

        # 模拟一些进度
        time.sleep(0.1)  # 等待一点时间
        tracker.update(5, 100, tokens_used=500)

        # show_stats 不应该抛出异常
        try:
            tracker.show_stats()
            success = True
        except Exception:
            success = False

        assert success

    def test_finish_success(self):
        """测试成功完成"""
        tracker = ProgressTracker()
        tracker.start()

        tracker.update(10, 200, tokens_used=1000)

        # finish 不应该抛出异常
        try:
            tracker.finish(success=True)
            success = True
        except Exception:
            success = False

        assert success

    def test_finish_failure(self):
        """测试失败完成"""
        tracker = ProgressTracker()
        tracker.start()

        tracker.update(5, 50, tokens_used=500)

        # finish 不应该抛出异常
        try:
            tracker.finish(success=False)
            success = True
        except Exception:
            success = False

        assert success

    def test_elapsed_time_calculation(self):
        """测试耗时计算"""
        tracker = ProgressTracker()
        tracker.start()

        # 等待一小段时间
        time.sleep(0.2)

        elapsed = time.time() - tracker.start_time

        assert elapsed >= 0.2
        assert elapsed < 0.5  # 不应该超过太多


# 集成测试
class TestProgressTrackerIntegration:
    """ProgressTracker 集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        tracker = ProgressTracker(total_estimated_nodes=500)

        # 1. 开始追踪
        tracker.start(max_depth=15)

        # 2. 模拟生成过程
        for depth in range(1, 6):
            node_count = depth * 20
            tracker.update(
                current_depth=depth,
                node_count=node_count,
                current_branch=f"S{depth}",
                tokens_used=100
            )

        # 3. 保存检查点
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "workflow_checkpoint.json"

            test_tree = {
                "root": {"node_id": "root", "depth": 0},
                "node_100": {"node_id": "node_100", "depth": 5}
            }

            tracker.save_checkpoint(test_tree, str(checkpoint_path))

            # 4. 创建新的 tracker 并加载检查点
            new_tracker = ProgressTracker()
            loaded_tree = new_tracker.load_checkpoint(str(checkpoint_path))

            # 5. 验证恢复状态
            assert loaded_tree is not None
            assert new_tracker.generated_nodes == 100
            assert new_tracker.current_depth == 5
            assert new_tracker.total_tokens == 500

        # 6. 完成追踪
        tracker.finish(success=True)

        # 7. 验证最终状态
        assert tracker.generated_nodes == 100
        assert tracker.total_tokens == 500

    def test_checkpoint_resume_scenario(self):
        """测试检查点恢复场景"""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "resume_checkpoint.json"

            # 第一阶段：生成并保存检查点
            tracker1 = ProgressTracker(total_estimated_nodes=1000)
            tracker1.start(max_depth=20)

            tracker1.update(10, 300, tokens_used=1500)

            test_tree = {"root": {"node_id": "root"}}
            tracker1.save_checkpoint(test_tree, str(checkpoint_path))

            # 第二阶段：模拟中断后恢复
            tracker2 = ProgressTracker(total_estimated_nodes=1000)
            loaded_tree = tracker2.load_checkpoint(str(checkpoint_path))

            # 验证恢复的状态正确
            assert loaded_tree is not None
            assert tracker2.generated_nodes == 300
            assert tracker2.current_depth == 10
            assert tracker2.total_tokens == 1500

            # 继续生成
            tracker2.start(max_depth=20)
            tracker2.update(15, 500, tokens_used=1000)

            assert tracker2.generated_nodes == 500
            assert tracker2.total_tokens == 2500
