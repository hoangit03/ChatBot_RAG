from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from src.rag.prompt_templates import get_wata_tech_rag_prompt
import re
from typing import Dict, Any
from pathlib import Path
class Str_OutputParser(StrOutputParser):
    def parse(self, text: str) -> str:
        return self.extract_answer(text)

    def extract_answer(self, text_response: str, pattern: str = r'Answer:\s*(.*)') -> str:
        match = re.search(pattern, text_response, re.DOTALL)
        return match.group(1).strip() if match else text_response

class Offline_RAG:
    def __init__(self, llm) -> None:
        self.llm = llm
        self.prompt = get_wata_tech_rag_prompt()
        self.str_parser = Str_OutputParser()
        self.chat_history = ChatMessageHistory()

    def get_chain(self, retriever):
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)


        def get_chat_history(inputs):
            return self.chat_history.messages    
    
        # Chain cơ bản
        rag_chain = (
            {
                "context": retriever | format_docs, 
                "question": RunnableLambda(lambda x: x),
                "chat_history": RunnableLambda(get_chat_history)
            }
            | self.prompt
            | self.llm
            | self.str_parser
        )

        def wrapped_chain(question: str) -> Dict[str, Any]:

            self.chat_history.add_user_message(question)

            answer = rag_chain.invoke(question)
            
            self.chat_history.add_ai_message(answer)

            source_docs = retriever.invoke(question)
            sources = [
                {
                    "url": doc.metadata.get("source", "#"),
                    "title": Path(doc.metadata.get("source", "Untitled")).stem
                }
                for doc in source_docs
                if hasattr(doc, "metadata")
            ]

            return {
                "reply": answer,
                "sources": sources[:1]
            }

        return RunnableLambda(wrapped_chain)