"""
Marketing Agent - Evaluates campaign performance and market messaging impact.
Uses Tavily (web search) and NewsData.io (news) for real-time market intelligence.
"""
import logging
from typing import Dict, List, Any

from .base_agent import BaseAgent, AgentInsight
from services.tavily_service import TavilyService
from services.newsdata_service import NewsDataService

logger = logging.getLogger(__name__)


class MarketingAgent(BaseAgent):
    def __init__(self, db_service, llm=None):
        super().__init__(db_service, llm)
        self.tavily = TavilyService()
        self.news = NewsDataService()

    # ------------------------------------------------------------------
    # Evidence retrieval — always attempts both Tavily and NewsData
    # ------------------------------------------------------------------

    async def retrieve_evidence(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        # 1. Internal knowledge-base documents
        try:
            docs = await self.db.get_department_documents("marketing")
            if docs:
                evidence.extend(docs)
                logger.info("MarketingAgent: loaded %d internal KB documents", len(docs))
        except Exception as exc:
            logger.warning("MarketingAgent: failed to load internal KB documents: %s", exc)

        # 2. Uploaded document context (if any)
        doc_summary = context.get("document_summary")
        if doc_summary:
            evidence.append(
                {
                    "source": "uploaded_document",
                    "path": context.get("document_path", "(runtime_upload)"),
                    "department": context.get("document_department", "unknown"),
                    "summary": doc_summary,
                    "tags": context.get("document_tags", []),
                }
            )
            logger.info("MarketingAgent: uploaded document context added (len=%d)", len(doc_summary))

        # 3. Tavily web search — real-time competitor & market data
        tavily_query = query[:100]
        news_query = query[:100]

        if self._llm_client:
            try:
                prompt_q = query
                if doc_summary:
                    prompt_q += f" Context: {doc_summary[:200]}"
                
                resp = await self._llm_client.acomplete_text(
                    system_prompt="You are a marketing search expert. Output ONLY a concise 3-5 word search query for market trends, competitors, or sentiment. Do not use quotes or markdown.",
                    user_prompt=f"Business query: {prompt_q}\nGenerate 1 optimized search string.",
                    temperature=0.2,
                    max_tokens=30,
                )
                generated_query = resp.text.strip().strip('"\'')
                if generated_query and len(generated_query) > 5:
                    tavily_query = generated_query
                    news_query = generated_query
                logger.info("MarketingAgent: LLM generated search query=%r", tavily_query)
            except Exception as exc:
                logger.warning("MarketingAgent: LLM query generation failed, using fallback. %s", exc)
                if doc_summary:
                    tavily_query = f"market analysis: {doc_summary[:100]}"
                    news_query = doc_summary[:100]
                else:
                    tavily_query = f"market analysis: {query[:100]}"
                    news_query = query[:100]
        else:
            if doc_summary:
                tavily_query = f"market analysis competitors industry trends: {doc_summary[:200]}"
                news_query = doc_summary[:120]
            else:
                tavily_query = f"market analysis competitors industry trends: {query[:200]}"
                news_query = query[:120]

        logger.info("MarketingAgent: running Tavily search — query=%r", tavily_query[:80])
        try:
            web_results = await self.tavily.search(tavily_query, max_results=3)
            if web_results:
                for result in web_results:
                    evidence.append({
                        "source": "tavily_search",
                        "title": result.get("title", "Web Result"),
                        "url": result.get("url"),
                        "summary": result.get("content"),
                        "type": "competitor_data",
                    })
                logger.info("MarketingAgent: Tavily returned %d results", len(web_results))
            else:
                logger.warning("MarketingAgent: Tavily returned 0 results for query=%r", tavily_query[:80])
        except Exception as exc:
            logger.error("MarketingAgent: Tavily search failed: %s", exc, exc_info=True)
            evidence.append({
                "source": "tavily_search_error",
                "summary": f"Tavily web search failed due to an error: {str(exc)}",
                "type": "error"
            })

        # 4. NewsData.io — latest news articles
        logger.info("MarketingAgent: running NewsData search — query=%r", news_query[:80])
        try:
            news_results = await self.news.get_latest_news(news_query)
            if news_results:
                for article in news_results:
                    evidence.append({
                        "source": "newsdata_io",
                        "title": article.get("title"),
                        "url": article.get("link"),
                        "summary": article.get("description"),
                        "pub_date": article.get("pubDate"),
                        "type": "market_news",
                    })
                logger.info("MarketingAgent: NewsData returned %d articles", len(news_results))
            else:
                logger.warning("MarketingAgent: NewsData returned 0 articles for query=%r", news_query[:80])
        except Exception as exc:
            logger.error("MarketingAgent: NewsData search failed: %s", exc, exc_info=True)
            evidence.append({
                "source": "newsdata_io_error",
                "summary": f"NewsData.io search failed due to an error: {str(exc)}",
                "type": "error"
            })

        logger.info("MarketingAgent: total evidence items collected: %d", len(evidence))
        return evidence

    # ------------------------------------------------------------------
    # Rule-based core analysis (LLM-driven fallback)
    # ------------------------------------------------------------------

    def _rule_based_analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """
        Produce structured insights from available evidence.
        Avoids hardcoded keywords — classifies evidence by source type and
        constructs findings from what was actually retrieved.
        """
        findings: List[str] = []
        risks: List[str] = []

        if not evidence:
            return AgentInsight(
                agent_name="Marketing",
                findings=["No marketing evidence found — neither internal KB, Tavily, nor NewsData returned data."],
                risks=["Decision confidence is very low without market intelligence data."],
                recommendation=(
                    "Ensure TAVILY_API_KEY and NEWSDATA_API_KEY are configured and valid, "
                    "then re-run the analysis to retrieve live market and competitor data."
                ),
                confidence=0.20,
                evidence_used=[],
            )

        # Categorise evidence by source
        internal_docs = [e for e in evidence if e.get("source") == "uploaded_document"]
        kb_docs = [e for e in evidence if e.get("source") not in ("uploaded_document", "tavily_search", "newsdata_io")]
        web_results = [e for e in evidence if e.get("source") == "tavily_search"]
        news_articles = [e for e in evidence if e.get("source") == "newsdata_io"]

        # Summarise what was found
        if internal_docs:
            findings.append(f"Uploaded document context reviewed ({len(internal_docs)} document(s)).")
        if kb_docs:
            findings.append(f"Internal knowledge base yielded {len(kb_docs)} marketing document(s).")
        if web_results:
            titles = ", ".join(r.get("title", "untitled") for r in web_results[:2] if r.get("title"))
            findings.append(
                f"Tavily web search returned {len(web_results)} real-time result(s). "
                + (f"Top sources: {titles}." if titles else "")
            )
        else:
            risks.append("No live web/competitor data retrieved via Tavily — market intelligence may be incomplete.")

        if news_articles:
            article_titles = ", ".join(a.get("title", "untitled") for a in news_articles[:2] if a.get("title"))
            findings.append(
                f"NewsData.io returned {len(news_articles)} recent news article(s). "
                + (f"Headlines: {article_titles}." if article_titles else "")
            )
        else:
            risks.append("No recent news articles retrieved via NewsData.io — sentiment and trend signals missing.")

        # Combine all summaries for generic textual signals
        summaries = [str(e.get("summary", "")).strip() for e in evidence if e.get("summary")]
        combined_text = " ".join(summaries).lower()

        # Only add findings if substantive text is present
        if combined_text:
            findings.append("Evidence text retrieved and ready for LLM-powered analysis.")

        if not risks:
            risks.append("Market data retrieved but depth of analysis limited without LLM interpretation.")

        recommendation = (
            "Analyse retrieved web and news evidence with LLM to extract actionable marketing insights, "
            "benchmark against competitors, and identify positioning opportunities."
        )

        return AgentInsight(
            agent_name="Marketing",
            findings=findings,
            risks=risks,
            recommendation=recommendation,
            confidence=0.65 if (web_results or news_articles) else 0.35,
            evidence_used=evidence,
        )

    async def analyze(self, evidence: List[Dict[str, Any]], query: str) -> AgentInsight:
        """Analyze marketing evidence using rule-based logic enhanced by LLM."""
        fallback = self._rule_based_analyze(evidence, query)

        # Build compact evidence summary for LLM — include source labels for traceability
        evidence_parts: List[str] = []
        for e in evidence:
            source = e.get("source", "unknown")
            summary = (e.get("summary") or "").strip()
            title = e.get("title", "")
            if summary:
                prefix = f"[{source}]{' — ' + title if title else ''}"
                evidence_parts.append(f"{prefix}: {summary[:400]}")

        evidence_summary = "\n".join(evidence_parts) if evidence_parts else "No marketing evidence found."

        return await self._llm_analyze(
            query=query,
            evidence_summary=evidence_summary,
            domain_role="marketing performance and campaign strategy analyst",
            domain_focus=(
                "Campaign ROI, audience segmentation effectiveness, channel performance, "
                "conversion rates, brand positioning, competitor market data from web search, "
                "recent industry news trends, and budget allocation recommendations. "
                "Benchmark internal strategy against real-time Tavily web data and NewsData.io news pulses."
            ),
            fallback_insight=fallback,
        )
