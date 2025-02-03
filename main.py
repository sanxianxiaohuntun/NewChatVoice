import base64
from typing import List, AsyncGenerator
from mirai import *
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.command import entities
from pkg.command.operator import CommandOperator, operator_class
from .pkg.ncv import NCV
from mirai import Voice, Plain
from pkg.platform.types import MessageChain, Plain, Voice
from .pkg.utils.text_cleaner import clean_markdown
from graiax import silkcoder
import os

# 命令常量
CMD_ON = "开启"
CMD_OFF = "关闭"
CMD_STATUS = "状态"
CMD_LIST = "角色列表"
CMD_PROVIDER = "平台"
CMD_CHARACTER = "角色"
CMD_HELP = "帮助"
CMD_TEXT_ON = "文本开启"
CMD_TEXT_OFF = "文本关闭"
CMD_PLATFORMS = "平台列表"
CMD_TRANSLATE_ON = "翻译开启"
CMD_TRANSLATE_OFF = "翻译关闭"
CMD_TRANSLATE_MODE = "翻译模式"

HELP_TEXT = """
!ncv 开启 - 开启语音功能
!ncv 关闭 - 关闭语音功能
!ncv 文本开启 - 开启文本返回
!ncv 文本关闭 - 关闭文本返回
!ncv 状态 - 查看当前设置
!ncv 角色列表 - 查看可用角色
!ncv 平台列表 - 查看支持的平台
!ncv 平台 <平台名> - 切换TTS平台
!ncv 角色 <角色ID> - 切换角色
!ncv 帮助 - 显示此帮助
!ncv 翻译开启 - 开启翻译功能
!ncv 翻译关闭 - 关闭翻译功能
!ncv 翻译模式 <zh2jp/zh2en> - 设置翻译模式"""

CHARACTER_LIST = """
由于角色过多，请在在线文档中查看角色列表
【腾讯文档】NewChatVoice-海豚AI二次元角色列表（acgn_ttson）
https://docs.qq.com/smartsheet/DSFZKZ1NEUUV5S0NS?tab=I36MjF
【腾讯文档】NewChatVoice-海豚AI角色列表（ttson）
https://docs.qq.com/smartsheet/DSFJ2cFVGbXdMZmhx?tab=hQeEMS"""


@operator_class(name="ncv", help="获取帮助请输入：！ncv 帮助", privilege=1)
class NCVOperator(CommandOperator):
    """NCV命令处理器"""

    def __init__(self, host: APIHost):
        super().__init__(host)
        self.ncv = NCV()

    async def execute(self, context: entities.ExecuteContext) -> AsyncGenerator[entities.CommandReturn, None]:
        sender_id = int(context.query.sender_id)
        command = context.crt_params[0] if context.crt_params else ""

        try:
            result = await self._handle_command(sender_id, command, context.crt_params[1:])
        except Exception as e:
            result = f"执行命令时出错: {str(e)}"

        yield entities.CommandReturn(text=result)

    async def _handle_command(self, sender_id: int, command: str, params: List[str]) -> str:
        """处理命令"""
        if command in [CMD_ON, "on"]:
            return await self._enable_voice(sender_id)

        elif command in [CMD_OFF, "off"]:
            return await self._disable_voice(sender_id)

        elif command in [CMD_TEXT_ON, "text_on"]:
            return await self._enable_text(sender_id)

        elif command in [CMD_TEXT_OFF, "text_off"]:
            return await self._disable_text(sender_id)

        elif command in [CMD_STATUS, "status"]:
            return await self._check_status(sender_id)

        elif command in [CMD_LIST, "list"]:
            return await self._list_characters(sender_id)

        elif command in [CMD_PLATFORMS, "platforms"]:
            return await self._list_platforms(sender_id)

        elif command in [CMD_PROVIDER, "provider"]:
            if not params:
                return "请指定TTS平台名称"
            return await self._switch_provider(sender_id, params[0])

        elif command in [CMD_CHARACTER, "character"]:
            if not params:
                return "请指定角色ID"
            return await self._switch_character(sender_id, params[0])

        elif command in [CMD_HELP, "help"]:
            return self._get_help()

        elif command in ["翻译开启", "translate_on"]:
            return await self._enable_translate(sender_id)
        
        elif command in ["翻译关闭", "translate_off"]:
            return await self._disable_translate(sender_id)
        
        elif command in ["翻译模式", "translate_mode"]:
            if not params:
                return "请指定翻译模式(zh2jp/zh2en)"
            return await self._set_translate_mode(sender_id, params[0])

        return '无效指令，请输入"!ncv 帮助"查看帮助'

    async def _enable_voice(self, sender_id: int) -> str:
        """启用语音"""
        prefs = self.ncv.get_user_preference(sender_id)
        prefs["voice_switch"] = True
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已为用户 {sender_id} 开启语音功能"

    async def _disable_voice(self, sender_id: int) -> str:
        """禁用语音"""
        prefs = self.ncv.get_user_preference(sender_id)
        prefs["voice_switch"] = False
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已为用户 {sender_id} 关闭语音功能"

    async def _enable_text(self, sender_id: int) -> str:
        """启用文本返回"""
        prefs = self.ncv.get_user_preference(sender_id)
        prefs["return_text"] = True
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已为用户 {sender_id} 开启文本返回"

    async def _disable_text(self, sender_id: int) -> str:
        """禁用文本返回"""
        prefs = self.ncv.get_user_preference(sender_id)
        prefs["return_text"] = False
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已为用户 {sender_id} 关闭文本返回"

    async def _check_status(self, sender_id: int) -> str:
        """检查状态"""
        prefs = self.ncv.get_user_preference(sender_id)
        status = []
        status.append(f"用户: {sender_id}")
        status.append(f"语音开关: {'开启' if prefs.get('voice_switch') else '关闭'}")
        status.append(f"文本返回: {'开启' if prefs.get('return_text') else '关闭'}")
        status.append(f"当前平台: {prefs.get('provider', '未设置')}")
        status.append(f"当前角色: {prefs.get('character', '未设置')}")
        translate_config = prefs.get("translate", {})
        status.append(f"翻译功能: {'开启' if translate_config.get('switch') else '关闭'}")
        status.append(f"翻译模式: {translate_config.get('translate_direction', '未设置')}")
        return "\n".join(status)

    async def _list_characters(self, sender_id: int) -> str:
        """列出角色"""
        prefs = self.ncv.get_user_preference(sender_id)
        platform = prefs.get("provider")
        if not platform:
            return "请先设置TTS平台"

        return CHARACTER_LIST

    async def _switch_provider(self, sender_id: int, provider: str) -> str:
        """切换平台"""
        platforms = await self.ncv.get_platforms()
        if provider not in platforms:
            return f"不支持的平台: {provider}"

        # 获取该平台的默认配置
        default_tts_config = self.ncv.config_manager.global_config.get(
            "default_tts_config", {})
        provider_config = default_tts_config.get(provider, {})
        default_character = str(provider_config.get("character_id", ""))

        # 更新用户配置
        prefs = self.ncv.get_user_preference(sender_id)
        prefs["provider"] = provider
        prefs["character"] = default_character  # 设置默认角色
        self.ncv.update_user_preference(sender_id, prefs)

        return f"已切换到平台: {provider}，默认角色ID: {default_character}"

    async def _switch_character(self, sender_id: int, character_id: str) -> str:
        """切换角色"""
        prefs = self.ncv.get_user_preference(sender_id)
        prefs["character"] = str(character_id)  # 确保是字符串
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已切换到角色ID: {character_id}，请确保角色ID正确且存在，角色ID请通过!ncv 角色列表查看"

    def _get_help(self) -> str:
        """获取帮助信息"""
        return HELP_TEXT

    async def _list_platforms(self, sender_id: int) -> str:
        """列出支持的平台"""
        platforms = await self.ncv.get_platforms()
        if not platforms:
            return "暂无可用的TTS平台"

        current_platform = self.ncv.get_user_preference(
            sender_id).get("provider", "未设置")

        result = ["支持的TTS平台:"]
        for platform in platforms:
            if platform == current_platform:
                result.append(f"* {platform} (当前)")
            else:
                result.append(f"* {platform}")

        return "\n".join(result)

    async def _enable_translate(self, sender_id: int) -> str:
        """启用翻译"""
        prefs = self.ncv.get_user_preference(sender_id)
        if "translate" not in prefs:
            prefs["translate"] = {}
        prefs["translate"]["switch"] = True
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已为用户 {sender_id} 开启翻译功能"

    async def _disable_translate(self, sender_id: int) -> str:
        """禁用翻译"""
        prefs = self.ncv.get_user_preference(sender_id)
        if "translate" not in prefs:
            prefs["translate"] = {}
        prefs["translate"]["switch"] = False
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已为用户 {sender_id} 关闭翻译功能"

    async def _set_translate_mode(self, sender_id: int, mode: str) -> str:
        """设置翻译模式"""
        if mode not in ["zh2jp", "zh2en"]:
            return "不支持的翻译模式，请使用: zh2jp(中译日) 或 zh2en(中译英)"
        
        prefs = self.ncv.get_user_preference(sender_id)
        if "translate" not in prefs:
            prefs["translate"] = {}
        prefs["translate"]["translate_direction"] = mode
        self.ncv.update_user_preference(sender_id, prefs)
        return f"已设置翻译模式为: {mode}"


@register(name="NewChatVoice", description="语音合成插件", version="3.0", author="the-lazy-me")
class NCVPlugin(BasePlugin):
    """NCV插件主类"""

    def __init__(self, host: APIHost):
        super().__init__(host)
        self.ncv = NCV()
        
        # 清空临时文件夹
        temp_dir = self.ncv.config_manager.temp_dir_path
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                try:
                    file_path = os.path.join(temp_dir, file)
                    os.remove(file_path)
                except Exception as e:
                    print(f"清理临时文件失败: {e}")

    @handler(NormalMessageResponded)
    async def handle_message(self, ctx: EventContext):
        """处理消息"""
        # 获取用户配置
        user_id = ctx.event.sender_id
        prefs = self.ncv.get_user_preference(user_id)

        # 检查是否启用语音
        if not prefs.get("voice_switch"):
            return

        # 清理Markdown格式并生成语音
        text = clean_markdown(ctx.event.response_text)
        try:
            audio_path = await self.ncv.generate_audio(user_id, text)
            if not audio_path:  # 文本过长或生成失败
                return
            
            # 构建消息链
            message_elements = []
            
            # 使用Voice消息发送
            with open(audio_path, "rb") as f:
                base64_audio = base64.b64encode(f.read()).decode()
            message_elements.append(Voice(base64=base64_audio))

            # 构建消息链并发送
            if message_elements:
                msg_chain = MessageChain(message_elements)
                await ctx.reply(msg_chain)

            # 根据用户设置决定是否返回文本
            if not prefs.get("return_text"):
                ctx.prevent_default()

        except Exception as e:
            print(f"生成语音失败: {e}")
            return
        finally:
            # 清理临时文件
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception as e:
                    print(f"清理临时文件失败: {e}")

    def __del__(self):
        """清理资源"""
        self.ncv.cleanup()
