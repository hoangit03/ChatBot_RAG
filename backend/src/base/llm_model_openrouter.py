import requests
import json
import os
from typing import Dict, List, Optional, Any, Union
from langchain_core.runnables import Runnable
from langchain_core.documents import Document
from dotenv import load_dotenv
import time
load_dotenv()
from langchain_core.messages import HumanMessage, SystemMessage


class OpenRouterClient:
    """
    Client để tương tác với OpenRouter API
    """
    def __init__(self, api_keys: List[str], base_url: str = "https://openrouter.ai/api/v1"):
        """
        Khởi tạo OpenRouter 
        
        Args:
            api_keys: Danh sách API key của OpenRouter
            base_url: URL cơ sở cho API của OpenRouter
        """
        self.api_keys = api_keys
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://watatek.com/", 
            "X-Title": "ChatBotAI" 
        }
        self.current_key_index = 0  # Lưu trữ chỉ số key hiện tại

    def get_current_api_key(self):
        """
        Lấy API key hiện tại
        """
        return self.api_keys[self.current_key_index]

    def switch_to_next_key(self):
        """
        Chuyển sang API key tiếp theo trong danh sách
        """
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

    def generate(self, 
            model: str,
            prompt: Union[str, List[Dict[str, str]], Document, List[Document]],
            max_tokens: int = 1024,
            timeout: int = 60,
            **kwargs) -> Dict[str, Any]:
        
        if isinstance(prompt, Document):
            messages = [{"role": "user","content":prompt.page_content}]
        elif isinstance(prompt, list) and all(isinstance(p, Document) for p in prompt):
            messages = [{"role": "user","content":"\n\n".join(p.page_content for p in prompt)}]
        elif isinstance(prompt, str):
            messages = [{"role": "user","content":prompt}]
        elif isinstance(prompt, list) and all(isinstance(p, dict) for p in prompt):
            messages = prompt
        else:
            raise ValueError("Prompt phải là chuỗi, danh sách messages, Document hoặc danh sách Document")

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            **kwargs
        }

        full_url = f"{self.base_url}/chat/completions"
        
        while True:
            try:
                # Sử dụng API key hiện tại
                self.headers["Authorization"] = f"Bearer {self.get_current_api_key()}"

                response = requests.post(
                    full_url,
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()
            
            except Exception as e:
                print(f"Error with API key {self.get_current_api_key()}: {str(e)}")
                self.switch_to_next_key()  # Chuyển sang key tiếp theo
                if self.current_key_index == 0:
                    # Nếu đã quay lại key đầu tiên, dừng lại
                    raise Exception("All API keys failed. Please check your keys and try again.")



class OpenRouterRunnable(Runnable):
    def __init__(self, client: OpenRouterClient, model: str, max_tokens: int = 1024, **kwargs):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.kwargs = kwargs

    def invoke(self, input: Any, config: Optional[Dict] = None) -> str:
        try:
            # Nếu input là ChatPromptValue, convert sang messages
            if hasattr(input, "to_messages"):
                messages_obj = input.to_messages()
                messages = [
                    {
                        "role": "system" if isinstance(msg, SystemMessage) else "user",
                        "content": msg.content
                    }
                    for msg in messages_obj
                ]
            elif isinstance(input, list) and all(isinstance(msg, dict) for msg in input):
                messages = input  # Đã là định dạng đúng
            elif isinstance(input, str):
                messages = [{"role": "user", "content": input}]
            else:
                raise ValueError("Invalid input format - expected ChatPromptValue with .to_messages() method")

            response = self.client.generate(
                model=self.model,
                prompt=messages,
                max_tokens=self.max_tokens,
                **self.kwargs
            )
            
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            raise ValueError(f"API call failed: {str(e)}")


def get_openrouter_llm(model_name: str = "google/gemma-3-27b-it:free", 
                    api_keys: Optional[List[str]] = None,
                    max_tokens: int = 1024,
                    **kwargs) -> OpenRouterRunnable:
    """
    Tạo một client OpenRouter để sử dụng LLM
    
    Args:
        model_name: Tên mô hình trên OpenRouter
        api_keys: Danh sách API keys cho OpenRouter (mặc định lấy từ biến môi trường)
        max_tokens: Số lượng token tối đa cho phản hồi
        **kwargs: Các tham số bổ sung cho API
        
    Returns:
        OpenRouterClient: Client đã cấu hình cho mô hình được chỉ định
    """
    if api_keys is None:
        api_keys = os.getenv("OPENROUTER_API_KEY")
        # Đọc từ biến môi trường nếu không truyền tham số
        if api_keys is None:
            raise ValueError("API keys không được cung cấp và không tìm thấy trong biến môi trường OPENROUTER_KEYS")
        
        # Chuyển đổi chuỗi thành danh sách các key
        api_keys = api_keys.split(",")

    client = OpenRouterClient(api_keys=api_keys)
    
    # Gắn thông tin mô hình đã chọn vào client để dễ sử dụng sau này
    client.default_model = model_name
    client.default_max_tokens = max_tokens
    client.default_kwargs = kwargs
    
    return OpenRouterRunnable(client, model=model_name, max_tokens=max_tokens, **kwargs)
