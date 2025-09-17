import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
import argparse
from mcp_use import MCPAgent, MCPClient
from azure.identity import AzureCliCredential, get_bearer_token_provider
from langchain_openai import AzureChatOpenAI, ChatOpenAI

async def analyze_user(username: str) -> str:
    load_dotenv()
    client = MCPClient.from_config_file("x_mcp.json")
    llm = get_azure_openai_llm_gpt_4_1()
    agent = MCPAgent(llm=llm, client=client, max_steps=10, memory_enabled=False)
    try:
        await agent.initialize()
        result = await agent.run(
            f"获取用户 @{username} 最近发表的 tweets 信息, 并总结这些 tweets 的主要内容, 分析这个人的兴趣爱好和关注点"
        )
        return str(result)
    finally:
        await client.close_all_sessions()

async def main():
    parser = argparse.ArgumentParser(description="Run an agent to fetch and analyze tweets")
    parser.add_argument(
        "username",
        nargs="?",
        default="elonmusk",
        help="The username of the tweet author (without @) to analyze.",
    )
    args = parser.parse_args()
    result = await analyze_user(args.username)
    print(f"\nResult: {result}")

def get_azure_openai_llm_gpt_4_1() -> Optional[AzureChatOpenAI]:
    token_provider = get_bearer_token_provider(
        AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
    )
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        temperature=0,
        max_retries=3,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
    )
    return llm
if __name__ == "__main__":
    asyncio.run(main())