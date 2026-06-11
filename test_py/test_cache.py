"""
测试智能缓存机制
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.agent import ContextCache

def test_cache():
    """测试缓存功能"""
    print("=" * 60)
    print("🧪 智能缓存机制测试")
    print("=" * 60)
    
    db = SessionLocal()
    cache = ContextCache()
    
    try:
        # 测试1：首次访问（缓存未命中）
        print("\n【测试1】首次获取团队信息（缓存未命中）")
        start_time = time.time()
        result1 = cache.get_team_context(db)
        elapsed1 = time.time() - start_time
        print(f"⏱️  耗时: {elapsed1*1000:.2f}ms")
        print(f"📊 缓存统计: {cache.get_stats()}")
        
        # 测试2：第二次访问（缓存命中）
        print("\n【测试2】再次获取团队信息（缓存命中）")
        start_time = time.time()
        result2 = cache.get_team_context(db)
        elapsed2 = time.time() - start_time
        print(f"⏱️  耗时: {elapsed2*1000:.2f}ms")
        print(f"📊 缓存统计: {cache.get_stats()}")
        print(f"✅ 性能提升: {(elapsed1 - elapsed2) / elapsed1 * 100:.1f}%")
        
        # 测试3：轻量级摘要
        print("\n【测试3】获取轻量级摘要")
        summary = cache.get_lightweight_summary(db)
        print(f"📋 任务统计: {summary}")
        print(f"📊 缓存统计: {cache.get_stats()}")
        
        # 测试4：缓存失效
        print("\n【测试4】清除缓存后重新获取")
        cache.invalidate()
        print("🗑️  缓存已清除")
        result3 = cache.get_team_context(db)
        print(f"📊 缓存统计: {cache.get_stats()}")
        
        # 测试5：验证数据一致性
        print("\n【测试5】验证缓存数据一致性")
        if result1 == result2 == result3:
            print("✅ 缓存数据一致")
        else:
            print("❌ 缓存数据不一致")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_cache()
