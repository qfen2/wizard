import json
import requests
import time
from typing import Dict, Any

class ComfyClient:
    """处理与 ComfyUI 服务端的底层交互"""
    def __init__(self, host: str = "http://127.0.0.1:8188"):
        self.host = host

    def upload_image(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            resp = requests.post(f"{self.host}/upload/image", files={"image": f})
            return resp.json()["name"]

    def run_workflow(self, workflow_data: Dict[str, Any]) -> str:
        resp = requests.post(f"{self.host}/prompt", json={"prompt": workflow_data})
        return resp.json()["prompt_id"]

    def poll_result(self, prompt_id: str) -> str:
        """轮询结果，直到图片生成完毕"""
        while True:
            resp = requests.get(f"{self.host}/history/{prompt_id}").json()
            if prompt_id in resp:
                # 假设输出节点 ID 为 9 (Save Image)
                file_name = resp[prompt_id]['outputs']['9']['images'][0]['filename']
                return f"{self.host}/view?filename={file_name}"
            time.sleep(1)