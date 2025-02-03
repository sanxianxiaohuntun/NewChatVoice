import requests
import json
from typing import Optional

class BaiduTranslateService:
    """百度翻译服务"""
    
    def __init__(self, app_id: str, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self._access_token = None
        
    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        try:
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key
            }
            response = requests.post(url, params=params)
            result = response.json()
            return result.get("access_token")
        except Exception as e:
            print(f"获取access_token失败: {str(e)}")
            return None
            
    async def translate(self, text: str, from_lang: str = "zh", to_lang: str = "jp") -> Optional[str]:
        """翻译文本
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言，默认中文
            to_lang: 目标语言，默认日语
            
        Returns:
            翻译后的文本，失败返回None
        """
        try:
            # 确保有访问令牌
            if not self._access_token:
                self._access_token = self._get_access_token()
                if not self._access_token:
                    return None
                    
            url = f"https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1?access_token={self._access_token}"
            
            payload = json.dumps({
                "from": from_lang,
                "to": to_lang,
                "q": text
            }, ensure_ascii=False)
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
            result = response.json()
            
            if "result" in result and "trans_result" in result["result"]:
                # 直接返回翻译后的文本列表
                return result["result"]["trans_result"]
            else:
                print(f"翻译失败: {result.get('error_msg', '未知错误')}")
                # 如果是token过期,尝试重新获取
                if result.get("error_code") in [110, 111]:
                    self._access_token = None
                return None
                
        except Exception as e:
            print(f"翻译请求失败: {str(e)}")
            return None 