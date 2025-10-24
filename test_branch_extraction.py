#!/usr/bin/env python3
"""
测试支线角色提取功能
"""
import re
from pathlib import Path

def extract_branch_roles(protagonist: str) -> list:
    """从角色分析中提取支线角色"""
    branch_roles = []

    # 查找"最终建议"部分推荐的主角
    main_role_match = re.search(r'(?:最终建议|最终推荐|主角线)[：:]\s*[*\*]*([^\n*]+)[*\*]*', protagonist, re.IGNORECASE)
    main_role = main_role_match.group(1).strip() if main_role_match else None

    print(f"📌 识别到主角: {main_role}")

    # 查找支线角色分类
    branch_lines = re.findall(
        r'[-–]\s*([^→\n]+?)\s*(?:→|->)\s*[*\*]*([^*\n]+?(?:支线|Boss|boss|线))[*\*]*',
        protagonist
    )

    for roles_part, branch_type in branch_lines:
        # 分割多个角色（可能用顿号、逗号分隔）
        role_names = re.split(r'[、,，]', roles_part.strip())
        for role_name in role_names:
            role_name = role_name.strip()
            if role_name and role_name != main_role:
                branch_roles.append({
                    "name": role_name,
                    "type": branch_type.strip()
                })

    # 如果没有找到明确的支线分类，则查找所有评估的角色
    if not branch_roles:
        print("⚠️ 未找到明确的支线分类，尝试从角色评估中提取...")
        all_roles = re.findall(r'###\s*\d+\.\s*([^\n]+)', protagonist)
        for role in all_roles:
            role = role.strip()
            if role and role != main_role:
                branch_roles.append({
                    "name": role,
                    "type": "支线"
                })

    print(f"🌿 识别到 {len(branch_roles)} 个支线角色: {[r['name'] for r in branch_roles]}")
    return branch_roles


def test_city(city_name: str, protagonist_file: str):
    """测试特定城市的角色提取"""
    print("\n" + "="*60)
    print(f"测试城市: {city_name}")
    print("="*60)

    protagonist_path = Path(protagonist_file)
    if not protagonist_path.exists():
        print(f"❌ 文件不存在: {protagonist_file}")
        return

    with open(protagonist_path, 'r', encoding='utf-8') as f:
        protagonist = f.read()

    branch_roles = extract_branch_roles(protagonist)

    print("\n📋 支线角色列表:")
    for idx, role_info in enumerate(branch_roles, start=1):
        safe_role_name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', role_info['name'])
        print(f"  {idx}. {role_info['name']:<15} ({role_info['type']})")
        print(f"     文件名: {city_name}_branch_{idx}_{safe_role_name}_story.md")

    print(f"\n✅ 如果运行完整生成，将创建 {len(branch_roles)} 条支线故事")
    print(f"📝 预计总字数: {len(branch_roles) * 1750} 字（支线）+ 4000字（主线）= {len(branch_roles) * 1750 + 4000} 字")
    print(f"⏱️  预计游玩时间: {len(branch_roles) * 9} 分钟（支线）+ 20分钟（主线）= {len(branch_roles) * 9 + 20} 分钟")


if __name__ == "__main__":
    # 测试杭州
    test_city("杭州", "examples/hangzhou/杭州_protagonist.md")

    # 测试武汉（如果存在）
    wuhan_protagonist = Path("examples/wuhan/武汉_protagonist.md")
    if wuhan_protagonist.exists():
        test_city("武汉", str(wuhan_protagonist))

    print("\n" + "="*60)
    print("🎯 如需完整生成，请运行:")
    print("  python generate_full_story.py --city 杭州")
    print("="*60)

