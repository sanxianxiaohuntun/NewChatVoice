import json
import os
from typing import Any, Dict

class UserDataManager:
    def __init__(self, data_dir_path: str, config_manager):
        """初始化用户数据管理器
        
        Args:
            data_dir_path: 用户数据存储目录
            config_manager: 配置管理器实例
        """
        self.data_dir_path = data_dir_path
        self.config_manager = config_manager
        os.makedirs(data_dir_path, exist_ok=True)

    def load_user_preference(self, user_id: int) -> Dict[str, Any]:
        """加载用户偏好设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户偏好设置字典
        """
        user_file = os.path.join(self.data_dir_path, f"userData_{user_id}.json")
        if os.path.exists(user_file):
            with open(user_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # 为新用户创建默认配置
            default_prefs = self._create_default_preferences()
            self.save_user_preference(user_id, default_prefs)
            return default_prefs

    def save_user_preference(self, user_id: int, preferences: Dict[str, Any]) -> None:
        """保存用户偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 偏好设置字典
        """
        user_file = os.path.join(self.data_dir_path, f"userData_{user_id}.json")
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(preferences, f, ensure_ascii=False, indent=2)

    def _create_default_preferences(self) -> Dict[str, Any]:
        """创建默认用户偏好设置
        
        Returns:
            默认偏好设置字典
        """
        # 获取默认平台
        default_provider = self.config_manager.default_provider
        
        # 获取该平台的默认配置
        default_tts_config = self.config_manager.global_config.get("default_tts_config", {})
        provider_config = default_tts_config.get(default_provider, {})
        
        # 从全局配置中读取默认开关状态
        default_voice_switch = self.config_manager.global_config.get("default_voice_switch", True)
        default_text_switch = self.config_manager.global_config.get("default_text_switch", True)
        
        # 获取默认翻译配置
        default_translate = self.config_manager.global_config.get("default_translate", {})
        
        return {
            "provider": default_provider,
            "character": str(provider_config.get("character_id", "")),
            "voice_switch": default_voice_switch,
            "return_text": default_text_switch,
            "translate": {
                "switch": default_translate.get("switch", False),
                "translate_direction": default_translate.get("translate_direction", "zh2jp")
            }
        }
