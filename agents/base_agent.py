from abc import ABC, abstractmethod
from langchain.agents import AgentExecutor
from config.llm_config import get_llm
from typing import Dict, Any, List

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.llm = get_llm()
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def _format_prompt(self, template: str, **kwargs) -> str:
        return template.format(**kwargs)