import os
from typing import List, Dict, Any, Optional
from .manager.config_manager import ConfigManager
from .manager.user_data_manager import UserDataManager
from .client.tts_client import TTSClient
from .service.tts_service import TTSService
from .service.translate_service import BaiduTranslateService

class NCV:
    """NewChatVoice主控制器"""
    
    def __init__(self):
        """初始化NCV控制器"""
        # 加载配置
        self.config_manager = ConfigManager("data/plugins/NewChatVoice/config")
        
        # 初始化用户数据管理器
        self.user_manager = UserDataManager(
            self.config_manager.data_dir_path,
            self.config_manager
        )
        
        # 初始化TTS客户端和服务
        self.tts_client = TTSClient(self.config_manager.one_tts_url)
        self.tts_service = TTSService(self.tts_client, self.config_manager.temp_dir_path)
        
        # 创建临时目录
        os.makedirs(self.config_manager.temp_dir_path, exist_ok=True)
        
        # 初始化翻译服务
        baidu_config = self.config_manager.global_config.get("baidu_translate", {})
        self.translate_service = BaiduTranslateService(
            app_id=baidu_config.get("app_id", ""),
            api_key=baidu_config.get("api_key", ""),
            secret_key=baidu_config.get("secret_key", "")
        )

    async def get_platforms(self) -> List[str]:
        """获取支持的平台列表"""
        return await self.tts_service.get_platforms()

    async def get_characters(self, platform: str) -> List[Dict[str, Any]]:
        """获取指定平台的角色列表"""
        return await self.tts_service.get_characters(platform)

    def get_user_preference(self, user_id: int) -> Dict[str, Any]:
        """获取用户偏好设置"""
        return self.user_manager.load_user_preference(user_id)

    def update_user_preference(self, user_id: int, preferences: Dict[str, Any]) -> None:
        """更新用户偏好设置"""
        self.user_manager.save_user_preference(user_id, preferences)

    async def generate_audio(
        self,
        user_id: int,
        text: str,
    ) -> Optional[str]:
        """生成语音文件
        
        Args:
            user_id: 用户ID
            text: 要转换的文本
            
        Returns:
            生成的语音文件路径,如果文本过长则返回None
        """
        try:
            # 检查文本长度
            if len(text) > self.config_manager.max_characters:
                print(f"文本过长({len(text)}字符),已忽略")
                return None
            
            # 获取用户配置
            user_prefs = self.get_user_preference(user_id)
            platform = user_prefs.get("provider", self.config_manager.default_provider)
            voice_id = user_prefs.get("character", "")
            
            # 初始化options
            options = {
                "to_lang": "ZH",  # 默认中文
                "auto_translate": 0
            }
            
            # 检查是否需要翻译
            translate_config = user_prefs.get("translate", self.config_manager.default_translate)
            if translate_config.get("switch", False):
                direction = translate_config.get("translate_direction", "")
                if direction == "zh2jp":
                    translated_result = await self.translate_service.translate(text, "zh", "jp")
                    if translated_result and isinstance(translated_result, list) and len(translated_result) > 0:
                        text = translated_result[0].get("dst", text)
                        # print(f"翻译结果: {text}")
                        # 设置为日语
                        options["to_lang"] = "JP"
                elif direction == "zh2en":
                    translated_result = await self.translate_service.translate(text, "zh", "en")
                    if translated_result and isinstance(translated_result, list) and len(translated_result) > 0:
                        text = translated_result[0].get("dst", text)
                        # print(f"翻译结果: {text}")
                        # 设置为英语
                        options["to_lang"] = "EN"
            
            if not voice_id:
                raise ValueError("未设置语音角色")
            
            # 生成语音
            path = await self.tts_service.generate_audio(
                platform=platform,
                text=text,
                voice_id=voice_id,
                options=options  # 传入语言选项
            )
            
            if not path:
                print(f"生成语音失败: {text}")
                return None
            
            return path
            
        except Exception as e:
            print(f"生成语音失败: {str(e)}")
            return None

    def cleanup(self) -> None:
        """清理临时文件"""
        temp_dir = self.config_manager.temp_dir_path
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                try:
                    os.remove(os.path.join(temp_dir, file))
                except Exception as e:
                    print(f"清理临时文件失败: {e}")
