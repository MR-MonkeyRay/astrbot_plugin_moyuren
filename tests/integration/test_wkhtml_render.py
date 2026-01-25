#!/usr/bin/env python3
"""测试 wkhtmltoimage 渲染器"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.rendering.data_provider import MoyuDataProvider
from core.rendering.wkhtml_renderer import WkhtmlMoyuRenderer
import tempfile

def test_wkhtml_renderer():
    """测试 wkhtmltoimage 渲染器"""
    print("=" * 60)
    print("测试 wkhtmltoimage 渲染器")
    print("=" * 60)

    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()

        # 生成数据
        provider = MoyuDataProvider()
        data = provider.generate_moyu_data()

        print(f"✅ 数据生成成功")
        print(f"   日期: {data.year_month} {data.day}日 {data.weekday}")
        print(f"   摸鱼指数: {data.moyu_index}% | {data.moyu_level}")

        # 渲染图片
        renderer = WkhtmlMoyuRenderer(temp_dir)
        image_path = renderer.render(data)

        if image_path and os.path.exists(image_path):
            file_size = os.path.getsize(image_path) / 1024
            print(f"\n✅ wkhtmltoimage 渲染成功！")
            print(f"✅ 图片路径: {image_path}")
            print(f"✅ 文件大小: {file_size:.2f} KB")

            # 复制到 assets 目录
            import shutil
            dest_path = "assets/wkhtml-render-example.png"
            os.makedirs("assets", exist_ok=True)
            shutil.copy(image_path, dest_path)
            print(f"✅ 已复制到: {dest_path}")

            return True
        else:
            print(f"\n❌ 渲染失败: 图片未生成")
            return False

    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n请安装依赖:")
        print("  pip install imgkit")
        print("  并安装 wkhtmltoimage: https://wkhtmltopdf.org/downloads.html")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wkhtml_renderer()
    sys.exit(0 if success else 1)
