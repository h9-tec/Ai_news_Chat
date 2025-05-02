from __future__ import annotations
import os
import logging
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama
from .tool_search import search_tools

logger = logging.getLogger(__name__)

class FuturepediaSearchTool(BaseTool):
    name: str = "futurepedia_search"
    description: str = "Search Futurepedia.io for AI tools related to a topic and return the top-k results."
    
    def _run(self, query: str, k: Optional[str] = None) -> str:
        try:
            # If k is None or 'All', return all results
            if k is None or k == "All":
                results = search_tools(query, None)
            else:
                results = search_tools(query, int(k))
            if not results:
                return "No tools found for this query."
            
            # Format the results in a clear, structured way
            formatted_results = []
            for t in results:
                formatted_results.append(f"Tool: {t['name']}")
                formatted_results.append(f"URL: {t['url']}")
                formatted_results.append(f"Description: {t['blurb']}")
                # Extract pricing from tags if present
                pricing = ''
                if t['tags']:
                    # Try to find a tag that matches known pricing types
                    pricing_types = [
                        'Free', 'Freemium', 'Free Trial', 'Paid', 'Contact for Pricing'
                    ]
                    pricing = next((tag for tag in t['tags'] if tag in pricing_types), '')
                formatted_results.append(f"Pricing: {pricing if pricing else 'Unknown'}")
                if t['tags']:
                    formatted_results.append(f"Tags: {', '.join(t['tags'])}")
                formatted_results.append("")  # Add empty line between tools
            
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error in Futurepedia search: {str(e)}")
            return f"Error searching tools: {str(e)}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented.")

def create_tool_agent(backend: str = "ollama", model: Optional[str] = None):
    """Create a tool search agent with the specified backend."""
    # Initialize tools
    tools = [FuturepediaSearchTool()]
    
    # Initialize LLM based on backend
    if backend == "groq":
        llm = ChatGroq(
            model=model or os.getenv("DEFAULT_GROQ_MODEL", "llama3-70b-8192"),
            temperature=0.2,
            max_tokens=512
        )
    else:  # ollama
        llm = Ollama(
            model=model or os.getenv("DEFAULT_OLLAMA_MODEL", "aya:8b"),
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            temperature=0.2,
            num_predict=512
        )
    
    # Create agent with optimized prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI tool search expert. Your job is to find relevant AI tools based on user queries.

Available tools:
{tools}

Tool names:
{tool_names}

You must use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: You must output ALL found tools, not just a summary or a subset. List EVERY tool found, with all available details (name, url, description, pricing, tags, etc). Do NOT summarize or limit the number of results. If there are many, output them all in the same format.

Begin!

Previous steps:
{agent_scratchpad}"""),
        ("user", "{input}")
    ])
    
    # Create and return the agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,  # Increased from 3 to 5
        handle_parsing_errors=True,
        early_stopping_method="generate",
        timeout=60,  # Add a 60-second timeout
        verbose=True
    )

# Create agent instances for reuse
GROQ_AGENT = create_tool_agent("groq")
OLLAMA_AGENT = create_tool_agent("ollama")

def search_with_agent(query: str, backend: str = "ollama", k: Optional[str] = None) -> str:
    """Always use direct tool search for all queries, bypassing the agent."""
    try:
        # Always use direct search_tools for all k
        if k is None or k == "All":
            results = search_tools(query, None)
        else:
            results = search_tools(query, int(k))
        if not results:
            return "No tools found for this query."
        formatted_results = []
        for t in results:
            formatted_results.append(f"Tool: {t['name']}")
            formatted_results.append(f"URL: {t['url']}")
            formatted_results.append(f"Description: {t['blurb']}")
            pricing = ''
            if t['tags']:
                pricing_types = [
                    'Free', 'Freemium', 'Free Trial', 'Paid', 'Contact for Pricing'
                ]
                pricing = next((tag for tag in t['tags'] if tag in pricing_types), '')
            formatted_results.append(f"Pricing: {pricing if pricing else 'Unknown'}")
            if t['tags']:
                formatted_results.append(f"Tags: {', '.join(t['tags'])}")
            formatted_results.append("")
        return "\n".join(formatted_results)
    except Exception as e:
        logger.error(f"Error in direct tool search: {str(e)}")
        return f"Sorry, there was an error processing your request. Please try again with a different query." 