from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser

def create_agent(llm, tools):
    """创建OpenAI Tools Agent"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_message}"),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 绑定工具
    llm_with_tools = llm.bind_tools(tools)
    
    # 定义Agent管道
    agent = (
        {
            "system_message": lambda x: x["messages"][0][1] if x["messages"] and x["messages"][0][0] == "system" else "",
            "messages": lambda x: [m for m in x["messages"] if m[0] != "system"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )
    
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
