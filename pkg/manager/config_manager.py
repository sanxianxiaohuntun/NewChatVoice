import yaml
import os
import shutil
from typing import Any, Dict

class ConfigManager:
    def __init__(self, config_path: str):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        
        # 确保配置目录存在
        os.makedirs(self.config_path, exist_ok=True)
        
        # 同步配置模板
        self._sync_config_template()
        
        # 加载配置
        self.global_config = self._load_global_config()

    def _sync_config_template(self) -> None:
        """同步配置模板文件"""
        template_path = "plugins/NewChatVoice/templates/global_config.yaml"
        config_file = os.path.join(self.config_path, "global_config.yaml")
        
        # 如果配置文件不存在，从模板复制
        if not os.path.exists(config_file):
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            shutil.copy2(template_path, config_file)

    def _load_global_config(self) -> Dict[str, Any]:
        """加载全局配置
        
        Returns:
            包含全局配置的字典
        """
        config_file = os.path.join(self.config_path, "global_config.yaml")
        with open(config_file, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def save_global_config(self) -> None:
        """保存全局配置"""
        config_file = os.path.join(self.config_path, "global_config.yaml")
        with open(config_file, "w", encoding="utf-8") as file:
            yaml.dump(self.global_config, file, allow_unicode=True)

    @property
    def default_provider(self) -> str:
        """获取默认TTS提供者"""
        # 修改默认值列表
        valid_providers = ["acgn_ttson", "ttson", "fish_studio", "fish_audio"]
        provider = self.global_config.get("default_provider", "acgn_ttson")
        return provider if provider in valid_providers else "acgn_ttson"
    
    @property
    def temp_dir_path(self) -> str:
        """获取临时文件目录路径"""
        return self.global_config.get("temp_dir_path")
    
    @property
    def data_dir_path(self) -> str:
        """获取数据文件目录路径"""
        return self.global_config.get("data_dir_path")
    
    @property
    def one_tts_url(self) -> str:
        """获取TTS服务URL"""
        return self.global_config.get("one_tts_url")
    
    @property
    def return_text(self) -> bool:
        """是否同时返回文本"""
        return self.global_config.get("return_text", False)
    
    @property
    def default_voice_switch(self) -> bool:
        """获取默认语音开关状态"""
        return self.global_config.get("default_voice_switch", True)
    
    @property
    def default_text_switch(self) -> bool:
        """获取默认文本返回状态"""
        return self.global_config.get("default_text_switch", False)
    
    @property
    def max_characters(self) -> int:
        """获取最大字符数限制,超过此长度的文本将使用File发送"""
        return self.global_config.get("max_characters", 300)
    
    @property
    def default_translate(self) -> Dict[str, Any]:
        """获取默认翻译配置"""
        return self.global_config.get("default_translate", {
            "switch": False,
            "translate_direction": "zh2jp"
        })