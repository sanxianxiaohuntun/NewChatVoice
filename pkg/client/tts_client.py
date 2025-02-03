import aiohttp
from typing import Dict, Any, List, Optional
import json

class TTSClient:
    """TTS HTTP客户端类"""
    
    def __init__(self, base_url: str):
        """初始化TTS客户端
        
        Args:
            base_url: TTS服务的基础URL
        """
        self.base_url = base_url.rstrip('/')
        
    async def get_platforms(self) -> List[str]:
        """获取支持的平台列表
        
        Returns:
            支持的TTS平台列表
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/platforms") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    platforms = data.get("platforms", [])
                    if "fish_audio" not in platforms:
                        platforms.append("fish_audio")
                    return platforms
                raise Exception(f"获取平台列表失败: {resp.status}")

    async def get_characters(self, platform: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指定平台的语音角色列表
        
        Args:
            platform: 平台名称
            token: 平台token(如果需要)
            
        Returns:
            角色列表
        """
        data = {
            "platform": platform
        }
        if token:
            data["token"] = token
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/characters",
                json=data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("characters", [])
                raise Exception(f"获取角色列表失败: {resp.status}")

    async def get_emotions(self, platform: str) -> List[str]:
        """获取指定平台的情感列表(仅TTSON平台支持)
        
        Args:
            platform: 平台名称
            
        Returns:
            情感列表
        """
        params = {"platform": platform}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/emotions",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("emotions", [])
                raise Exception(f"获取情感列表失败: {resp.status}")

    async def text_to_speech(
        self,
        platform: str,
        text: str,
        character: str,
        token: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """将文本转换为语音
        
        Args:
            platform: 平台名称
            text: 要转换的文本
            character: 角色ID或名称
            token: 平台token(如果需要)
            options: 其他选项
            
        Returns:
            音频数据
        """
        data = {
            "platform": platform,
            "text": text,
            "character": character
        }
        
        if token:
            data["token"] = token
        if options:
            data["options"] = options
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/tts",
                json=data
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
                raise Exception(f"语音合成失败: {resp.status}, {await resp.text()}") 