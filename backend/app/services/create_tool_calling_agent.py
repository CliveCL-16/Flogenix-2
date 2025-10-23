from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

def create_tool_calling_agent(llm, tools):
    """Custom lightweight tool-calling agent compatible with LangChain 1.0+."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI agent."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    return AgentExecutor.from_agent_and_tools(
        agent=llm.bind_tools(tools),
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        output_parser=OpenAIToolsAgentOutputParser(),
        format_scratchpad=format_to_openai_tool_messages,
    )
