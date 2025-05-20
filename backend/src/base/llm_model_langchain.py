import os
from typing import Any, Dict, List, Mapping, Optional, Union
from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

import requests

load_dotenv()

class OpenRouterChat(BaseChatModel):
    """
    LangChain wrapper for the OpenRouter API using the chat completion interface.
    """
    
    api_key: str
    model_name: str = "mistralai/mistral-7b-instruct"
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    base_url: str = "https://openrouter.ai/api/v1"

    streaming: bool = False
    timeout: Optional[int] = 60
    
    def __init__(
        self,
        model_name: str = "mistralai/mistral-7b-instruct",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 1.0,
        **kwargs
    ):
        """Initialize OpenRouter Chat model."""
        if api_key is None:
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if api_key is None:
                raise ValueError("API key not provided and not found in OPENROUTER_API_KEY environment variable")

        streaming = kwargs.pop("streaming", False)
        timeout = kwargs.pop("timeout", 60)
        base_url = kwargs.pop("base_url", "https://openrouter.ai/api/v1")
        
        super().__init__(
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            streaming=streaming,
            timeout=timeout,
            base_url=base_url,
            **kwargs
        )
        
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "openrouter-chat"
    
    def _convert_messages_to_openrouter_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenRouter format."""
        openrouter_messages = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                openrouter_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openrouter_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                openrouter_messages.append({"role": "system", "content": message.content})
            else:
                openrouter_messages.append({"role": "user", "content": str(message.content)})
                
        return openrouter_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> ChatResult:
        """Generate response using OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://watatek.com/",  
            "X-Title": "ChatBotAI"  
        }
        

        openrouter_messages = self._convert_messages_to_openrouter_format(messages)
        
        params = {
            "model": self.model_name,
            "messages": openrouter_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        
        if stop:
            params["stop"] = stop
            
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            response_data = response.json()
            
            if not response_data or 'choices' not in response_data or not response_data['choices']:
                raise ValueError(f"No results found in response: {response_data}")
            
            content = response_data["choices"][0]["message"]["content"]
            
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            raise ValueError(f"Error calling OpenRouter API: {str(e)}")
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async implementation - not implemented yet."""
        raise NotImplementedError("Async generation not implemented yet")


def create_openrouter_chat(
    model_name: str = "mistralai/mistral-7b-instruct",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    **kwargs
) -> OpenRouterChat:
    """
    Create an OpenRouterChat model instance
    
    Args:
        model_name: Name of the model on OpenRouter
        api_key: API key for OpenRouter (defaults to environment variable)
        temperature: Temperature parameter (0-1)
        max_tokens: Maximum number of tokens for the response
        **kwargs: Additional parameters for the API
        
    Returns:
        OpenRouterChat: Configured chat model
    """
    return OpenRouterChat(
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


# Example usage to demonstrate how to use this implementation
# if __name__ == "__main__":
#     # Create a chat model
#     chat = create_openrouter_chat("google/gemma-3-27b-it:free")
    
#     # Simple question-answer example
#     messages = [
#         SystemMessage(content="Bạn là một trợ lý AI thông minh và hữu ích."),
#         HumanMessage(content="Bài hát mới nhất của Sơn Tùng?.")
#     ]
#     import time
#     start_time = time.perf_counter()
#     response = chat.invoke(messages)
#     end_time = time.perf_counter()

#     print(f"Response: {response.content}")
#     print("⏱️ Thời gian phản hồi:", round(end_time - start_time, 2), "giây")

    