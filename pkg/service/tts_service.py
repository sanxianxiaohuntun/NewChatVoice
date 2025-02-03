import os
import wave
from typing import List, Dict, Any, Optional
from ..client.tts_client import TTSClient
from graiax import silkcoder

class TTSService:
    """TTS服务类"""
    
    def __init__(self, client: TTSClient, temp_dir: str):
        """初始化TTS服务"""
        self.client = client
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
    def _validate_audio_file(self, file_path: str) -> bool:
        """验证音频文件是否有效
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            bool: 文件是否有效
        """
        try:
            # 检查文件是否存在且大小不为0
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                return False
                
            # 尝试作为WAV文件打开
            try:
                with wave.open(file_path, 'rb') as wav_file:
                    if wav_file.getnchannels() == 0 or wav_file.getsampwidth() == 0:
                        return False
                return True
            except wave.Error:
                # 不是WAV文件，检查文件头
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    
                # 检查MP3文件头
                if header.startswith(b'\xff\xfb') or header.startswith(b'ID3'):
                    return True
                    
                # 如果需要支持其他格式，在这里添加相应的检查
                
                # 如果文件大小合理，也认为是有效的
                return os.path.getsize(file_path) > 1024  # 至少1KB
                
        except Exception as e:
            print(f"音频文件验证失败: {str(e)}")
            return False
        
    async def get_platforms(self) -> List[str]:
        """获取支持的平台列表"""
        return await self.client.get_platforms()
        
    async def get_characters(self, platform: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取指定平台的角色列表"""
        return await self.client.get_characters(platform, token)
        
    async def get_emotions(self, platform: str) -> List[str]:
        """获取指定平台的情感列表"""
        return await self.client.get_emotions(platform)
        
    def _convert_to_silk(self, input_file: str, output_file: str) -> bool:
        """将音频文件转换为silk格式
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出silk文件路径
            
        Returns:
            bool: 是否转换成功
        """
        try:
            import subprocess
            
            # 获取ffmpeg和encoder路径
            ffmpeg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'ffmpeg.exe')
            encoder_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'silk_v3_encoder.exe')
            
            # 创建临时PCM文件路径
            temp_pcm = os.path.join(self.temp_dir, 'temp.pcm')
            
            # 转换为PCM格式,重定向输出到DEVNULL
            subprocess.run([
                ffmpeg_path,
                '-y',
                '-i', input_file,
                '-f', 's16le',
                '-ar', '24000',
                '-ac', '1',
                temp_pcm
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 转换为SILK格式,重定向输出到DEVNULL
            subprocess.run([
                encoder_path,
                temp_pcm,
                output_file,
                '-rate', '24000',
                '-tencent'
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 清理临时文件
            if os.path.exists(temp_pcm):
                os.remove(temp_pcm)
                
            return os.path.exists(output_file)
            
        except Exception as e:
            print(f"SILK转换失败: {str(e)}")
            return False

    async def generate_audio(
        self,
        platform: str,
        text: str,
        voice_id: str,
        token: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成语音文件"""
        # 确保voice_id是字符串
        voice_id = str(voice_id)
        
        # 设置默认options
        if options is None:
            options = {}
        if platform == "ttson":
            options.update({
                "to_lang": "auto",
                "emotion": 1
            })

        
        try:
            audio_data = await self.client.text_to_speech(
                platform=platform,
                text=text,
                character=voice_id,
                token=token,
                options=options
            )
            
            # 生成临时音频文件
            temp_audio = os.path.join(self.temp_dir, f"{voice_id}_{hash(text)}.wav")
            with open(temp_audio, "wb") as f:
                f.write(audio_data)
                
            # 验证音频文件
            if not self._validate_audio_file(temp_audio):
                print(f"生成的音频文件无效: {text}")
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
                return ""
                
            # 转换为silk格式
            silk_path = os.path.join(self.temp_dir, f"{voice_id}_{hash(text)}.silk")
            try:
                if self._convert_to_silk(temp_audio, silk_path):
                    # 清理原始音频文件
                    if os.path.exists(temp_audio):
                        os.remove(temp_audio)
                    return silk_path
                else:
                    print(f"SILK转换失败: {text}")
                    return ""
                    
            except Exception as e:
                print(f"SILK转换失败: {str(e)}")
                return ""
                
        except Exception as e:
            print(f"音频生成失败: {str(e)}")
            return "" 
        
    async def merge_audio_files(self, audio_files: List[str], output_path: str) -> bool:
        """合并多个音频文件
        
        Args:
            audio_files: 音频文件路径列表
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            import ffmpeg
            
            # 创建一个包含所有输入文件的列表
            inputs = []
            for file in audio_files:
                inputs.append(ffmpeg.input(file))
                
            # 使用concat过滤器合并音频
            merged = ffmpeg.concat(*inputs, v=0, a=1)
            
            # 输出到目标文件
            merged.output(output_path).run(capture_stdout=True, capture_stderr=True)
            
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            
        except Exception as e:
            print(f"合并音频文件失败: {str(e)}")
            return False 