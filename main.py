# -*- coding: utf-8 -*-
"""
主应用程序入口文件
文件路径: main.py

抗量子数字资产保护系统 - 启动入口
"""

import sys
import os
import threading
import traceback
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

try:
    from GUI.main_window import MainWindow
    from src.network.p2p_manager import P2PNode
    from src.crypto_lattice.wrapper import LatticeWrapper
    from src.config import NetworkParams
except ImportError as e:
    print(f"[Error] Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


class QSPApplication:
    """QSP 应用管理器"""
    
    def __init__(self):
        self.p2p_node: P2PNode = None
        self.node_identity = None
        
    def initialize_identity(self):
        """初始化本机身份（生成或加载密钥对）"""
        keys_dir = os.path.join(os.path.dirname(__file__), "data", "keys")
        os.makedirs(keys_dir, exist_ok=True)
        
        identity_file = os.path.join(keys_dir, "node_identity.json")
        
        if os.path.exists(identity_file):
            import json
            with open(identity_file, 'r') as f:
                data = json.load(f)
                self.node_identity = {
                    "id": data.get("node_id", "unknown"),
                    "pk": base64.b64decode(data["pk"]),
                    "sk": base64.b64decode(data["sk"])
                }
            print(f"[Identity] Loaded existing identity: {self.node_identity['id']}")
        else:
            print("[Identity] Generating new node identity...")
            pk, sk = LatticeWrapper.generate_signing_keypair()
            import json
            import uuid
            node_id = f"QSP_{uuid.uuid4().hex[:8].upper()}"
            
            data = {
                "node_id": node_id,
                "pk": base64.b64encode(pk).decode(),
                "sk": base64.b64encode(sk).decode()
            }
            
            with open(identity_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.node_identity = {
                "id": node_id,
                "pk": pk,
                "sk": sk
            }
            print(f"[Identity] Created new identity: {node_id}")
        
        return self.node_identity
    
    def start_p2p_network(self, port: int = 9999):
        """启动 P2P 网络节点"""
        if self.node_identity is None:
            self.initialize_identity()
        
        self.p2p_node = P2PNode(
            host='0.0.0.0',
            port=port,
            static_sk=self.node_identity["sk"],
            dil_pk=self.node_identity["pk"]
        )
        self.p2p_node.start()
        return self.p2p_node
    
    def get_invite_code(self) -> str:
        """生成本机邀请码 - 使用正确的格式"""
        if not hasattr(self.p2p_node, 'generate_invite_code'):
            raise RuntimeError("P2P node not initialized")
        
        return self.p2p_node.generate_invite_code()


def main():
    """主程序入口"""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = QSPApplication()
    
    try:
        identity = app.initialize_identity()
        p2p_node = app.start_p2p_network(port=9999)
        
        # 先尝试发现公网坐标
        print("[P2P] Discovering public coordinates...")
        p2p_node.discover_public_coordinates()
        
        invite_code = app.get_invite_code()
        
    except Exception as e:
        print(f"[Fatal] Initialization failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    root = ctk.CTk()
    root.title("抗量子数字资产保护系统 (QSP)")
    root.geometry("900x650")
    root.resizable(False, False)
    
    gui = MainWindow(root, p2p_node, app, invite_code)
    
    root.mainloop()
    
    if p2p_node:
        p2p_node.stop()


if __name__ == "__main__":
    main()
