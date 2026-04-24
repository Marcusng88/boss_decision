"""
Marketing Agent - Evaluates campaign performance and market messaging impact.
Uses LangChain with Tavily (web search) and NewsData.io (news) for real-time market intelligence.
"""
import logging
import os
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight
from services.marketing_tools import TavilySearchTool, NewsDataTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

class MarketingAgent(BaseAgent):
    def __init__(self, db_service, llm=None):
        super().__init__(db_service, llm)
        self.tools = [TavilySearchTool(), NewsDataTool()]
        
        # Initialize LangChain LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please check your .env file.")
            
        self.lc_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.3
        )
        
        # Setup Agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a proactive Marketing Performance Analyst. "
                       "Your goal is to provide actionable intelligence even with limited internal data. \n\n"
                       "1. ALWAYS review the 'Internal Context' provided in the input. \n"
                       "2. If the user query refers to a plan (like 'Q3 Expansion') not fully detailed in the docs, "
                       "analyze the EXISTING marketing reports and use your SEARCH TOOLS to benchmark "
                       "competitors and trends related to those specific campaigns (e.g., search for TikTok marketing ROI or competitor sentiment). \n"
                       "3. Do not just say 'I need more info'. Synthesize a perspective based on what you HAVE and what you FIND online."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(self.lc_llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        In LangChain mode, tools are called during the agent run.
        We still pull internal KB documents as initial context.
        """
        evidence: List[Dict[str, Any]] = []

        # 1. Internal knowledge-base documents
        try:
            docs = await self.db.get_department_documents("marketing")
            if docs:
                evidence.extend(docs)
                logger.info("MarketingAgent: loaded %d internal KB documents", len(docs))
        except Exception as exc:
            logger.warning("MarketingAgent: failed to load internal KB documents: %s", exc)

        # 2. Uploaded document context
        doc_summary = context.get("document_summary")
        if doc_summary:
            evidence.append({
                "source": "uploaded_document",
                "summary": doc_summary,
                "department": context.get("document_department", "unknown"),
            })
        
        return evidence

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """
        Run the LangChain agent to get insights using tools.
        """
        # Build initial context from evidence
        context_str = "\n".join([f"[{e.get('source')}]: {e.get('summary')}" for e in evidence])
        
        full_input = f"Query: {query}\n\nInternal Context:\n{context_str}\n\nPlease analyze and provide marketing insights."
        
        logger.info("\n[MarketingAgent] Executing LangChain agent for query: %s", query)
        try:
            # Note: LangChain's ainvoke is used for async execution
            response = await self.agent_executor.ainvoke({"input": full_input})
            output = response.get("output", "No output from agent.")
            logger.info("[MarketingAgent] LangChain execution completed.")
        except Exception as exc:
            logger.error(f"MarketingAgent LangChain execution failed: {exc}")
            output = f"Analysis failed: {str(exc)}"
            logger.error(f"[MarketingAgent] LangChain execution failed: {exc}")

        # We still need to return an AgentInsight object
        # We'll use our _llm_client to structure the final output from the LangChain agent's result
        
        return await self._llm_analyze(
            query=query,
            evidence_summary=output,
            domain_role="marketing performance and campaign strategy analyst",
            domain_focus="Campaign ROI, audience segmentation, competitor benchmarking, and market trends.",
            fallback_insight=AgentInsight(
                agent_name="Marketing",
                findings=[output[:200]] if output else ["No findings."],
                risks=["Analysis limited by execution error"] if not output else ["Risk identified during search."],
                recommendation="Review terminal logs for details" if not output else "Proceed with recommended strategy.",
                confidence=0.5,
                evidence_used=evidence
            )
        )
