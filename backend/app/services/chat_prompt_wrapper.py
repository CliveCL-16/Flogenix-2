# chat_prompt_wrapper.py

try:
    # For newer LangChain versions
    from langchain.prompts.chat import ChatPromptTemplate
except ImportError:
    # Fallback for older LangChain versions
    from langchain.prompts import ChatPromptTemplate

# Optionally, you can add an alias if you want a consistent name
# ChatPromptTemplateWrapper = ChatPromptTemplate
