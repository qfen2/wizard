# client.py
import asyncio
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    # 1. 配置服务器连接
    server_config = {
        "my_data_server": {
            "command": sys.executable,  # 使用当前 Python 解释器
            "args": ["mcp_server.py"],  # 启动 server.py
            "transport": "stdio"
        }
    }

    print("🔌 初始化客户端 (v0.1.0+ 模式)...")

    # --- 修正点：不再使用 async with ---
    # 直接实例化客户端
    client = MultiServerMCPClient(server_config)

    try:
        # 2. 获取服务器上的所有资源列表
        # 注意：这里根据新版 API，可能需要先列出资源，或者直接获取
        print("🔍 正在连接服务器并获取资源...")

        # 尝试从指定服务器获取所有暴露的资源
        # 注意：get_resources 通常返回资源的内容(Blobs)
        # 如果你想先看有什么资源，可以用 client.list_resources("my_data_server")

        # 这里演示：直接获取所有可用资源的内容
        blobs = await client.get_resources("my_data_server", uris = ["memo://secret_sauce.md"])

        print(f"✅ 获取到 {len(blobs)} 个资源资源包")

        for blob in blobs:
            print("-" * 30)
            print(f"📄 URI: {blob.metadata.get('uri', 'Unknown URI')}")
            print(f"🏷️ 类型: {blob.mimetype}")

            # 解析内容 (blob.data 通常是 bytes，需要 decode)
            if hasattr(blob, "as_string"):
                content = blob.as_string()
            else:
                # 兼容性处理，如果 as_string 不存在
                content = blob.data.decode("utf-8")

            print(f"📝 内容:\n{content}")
            print("-" * 30)

    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        # 如果新版有 close 方法，建议在这里调用
        # await client.close()
        pass


if __name__ == "__main__":
    asyncio.run(main())