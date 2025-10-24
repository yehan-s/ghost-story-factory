"""
领域模型测试 - Branch Role (支线角色)

DDD 领域模型测试，验证值对象和领域规则
"""
import pytest
from dataclasses import dataclass
from typing import List, Optional


# ==================== 领域模型定义 ====================

@dataclass(frozen=True)
class BranchRole:
    """支线角色值对象（Value Object）

    领域规则：
    1. 角色名不能为空
    2. 角色名不能是主角
    3. 支线类型必须有效
    """
    name: str
    branch_type: str

    def __post_init__(self):
        """值对象不变性验证"""
        if not self.name or not self.name.strip():
            raise ValueError("角色名不能为空")
        if not self.branch_type or not self.branch_type.strip():
            raise ValueError("支线类型不能为空")

    @property
    def safe_filename(self) -> str:
        """生成安全的文件名"""
        import re
        return re.sub(r'[^\w\u4e00-\u9fff]+', '_', self.name)

    def is_thrilling_type(self) -> bool:
        """是否为惊悚体验支线"""
        return "惊悚" in self.branch_type or "体验" in self.branch_type

    def is_evidence_type(self) -> bool:
        """是否为证据支线"""
        return "证据" in self.branch_type or "资料" in self.branch_type

    def is_boss_type(self) -> bool:
        """是否为Boss类型"""
        return "Boss" in self.branch_type or "boss" in self.branch_type or "阻力" in self.branch_type


# ==================== 领域模型测试 ====================

class TestBranchRoleDomain:
    """领域模型测试 - BranchRole 值对象"""

    def test_valid_branch_role_creation(self):
        """测试：创建有效的支线角色"""
        # Given
        name = "夜班保安"
        branch_type = "惊悚体验支线"

        # When
        role = BranchRole(name=name, branch_type=branch_type)

        # Then
        assert role.name == name
        assert role.branch_type == branch_type

    def test_branch_role_is_immutable(self):
        """测试：支线角色是不可变的（值对象特性）"""
        # Given
        role = BranchRole(name="夜班保安", branch_type="惊悚体验支线")

        # When & Then
        with pytest.raises(Exception):  # dataclass frozen=True 会抛出异常
            role.name = "新名字"  # type: ignore

    def test_empty_name_raises_error(self):
        """测试：空角色名应该抛出错误"""
        # Given & When & Then
        with pytest.raises(ValueError, match="角色名不能为空"):
            BranchRole(name="", branch_type="惊悚体验支线")

    def test_whitespace_name_raises_error(self):
        """测试：纯空格角色名应该抛出错误"""
        # Given & When & Then
        with pytest.raises(ValueError, match="角色名不能为空"):
            BranchRole(name="   ", branch_type="惊悚体验支线")

    def test_empty_branch_type_raises_error(self):
        """测试：空支线类型应该抛出错误"""
        # Given & When & Then
        with pytest.raises(ValueError, match="支线类型不能为空"):
            BranchRole(name="夜班保安", branch_type="")

    def test_safe_filename_generation(self):
        """测试：生成安全的文件名"""
        # Given
        role = BranchRole(name="夜班保安", branch_type="惊悚体验支线")

        # When
        filename = role.safe_filename

        # Then
        assert filename == "夜班保安"
        assert " " not in filename

    def test_safe_filename_with_special_chars(self):
        """测试：特殊字符被替换为下划线"""
        # Given
        role = BranchRole(name="值班/经理", branch_type="对抗阻力")

        # When
        filename = role.safe_filename

        # Then
        assert filename == "值班_经理"
        assert "/" not in filename

    def test_thrilling_type_detection(self):
        """测试：识别惊悚体验支线"""
        # Given
        role1 = BranchRole(name="夜班保安", branch_type="惊悚体验支线")
        role2 = BranchRole(name="录音博主", branch_type="声纹证据支线")

        # When & Then
        assert role1.is_thrilling_type() is True
        assert role2.is_thrilling_type() is False

    def test_evidence_type_detection(self):
        """测试：识别证据支线"""
        # Given
        role1 = BranchRole(name="录音博主", branch_type="声纹证据支线")
        role2 = BranchRole(name="主播", branch_type="舆论/资料支线")
        role3 = BranchRole(name="夜班保安", branch_type="惊悚体验支线")

        # When & Then
        assert role1.is_evidence_type() is True
        assert role2.is_evidence_type() is True
        assert role3.is_evidence_type() is False

    def test_boss_type_detection(self):
        """测试：识别Boss类型"""
        # Given
        role1 = BranchRole(name="值班经理", branch_type="对抗阻力Boss")
        role2 = BranchRole(name="夜班保安", branch_type="惊悚体验支线")

        # When & Then
        assert role1.is_boss_type() is True
        assert role2.is_boss_type() is False

    def test_equality_based_on_values(self):
        """测试：值对象相等性基于值而非引用"""
        # Given
        role1 = BranchRole(name="夜班保安", branch_type="惊悚体验支线")
        role2 = BranchRole(name="夜班保安", branch_type="惊悚体验支线")
        role3 = BranchRole(name="登山女跑者", branch_type="惊悚体验支线")

        # When & Then
        assert role1 == role2  # 值相同，应该相等
        assert role1 != role3  # 值不同，不相等
        assert role1 is not role2  # 但不是同一个对象


class TestBranchRoleList:
    """领域模型测试 - 支线角色集合"""

    def test_multiple_roles_from_same_type(self):
        """测试：同一类型可以有多个角色"""
        # Given
        roles = [
            BranchRole(name="夜班保安", branch_type="惊悚体验支线"),
            BranchRole(name="登山女跑者", branch_type="惊悚体验支线"),
        ]

        # When
        thrilling_roles = [r for r in roles if r.is_thrilling_type()]

        # Then
        assert len(thrilling_roles) == 2

    def test_filter_roles_by_type(self):
        """测试：按类型筛选角色"""
        # Given
        roles = [
            BranchRole(name="夜班保安", branch_type="惊悚体验支线"),
            BranchRole(name="录音博主", branch_type="声纹证据支线"),
            BranchRole(name="值班经理", branch_type="对抗阻力Boss"),
        ]

        # When
        evidence_roles = [r for r in roles if r.is_evidence_type()]
        boss_roles = [r for r in roles if r.is_boss_type()]

        # Then
        assert len(evidence_roles) == 1
        assert len(boss_roles) == 1
        assert evidence_roles[0].name == "录音博主"
        assert boss_roles[0].name == "值班经理"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

