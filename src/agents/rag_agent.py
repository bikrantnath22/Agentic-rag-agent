"""Main RAG agent with LangGraph workflow and multi-tool routing."""

import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

from ..agents.base_agent import BaseAgent
from ..agents.tools.calculator import CalculatorTool
from ..agents.tools.code_executor import CodeExecutorTool
from ..agents.tools.retriever import RetrieverTool
from ..agents.tools.web_search import WebSearchTool
from ..agents.workflows.planning import PlanningWorkflow
from ..agents.workflows.reflection import ReflectionWorkflow
from ..generation.llm_client import LLMClient, get_llm_client
from ..generation.prompt_templates import PromptTemplates
from ..observability.logging import get_logger
from ..retrieval.reranker import get_reranker
from ..retrieval.vector_store import VectorStoreRetriever
from ..utils.config import get_settings
from ..utils.exceptions import AgentError

logger = get_logger(__name__)


class GraphState(TypedDict):
    """LangGraph state dictionary."""

    query: str
    retrieved_documents: list[dict[str, Any]]
    answer: str
    plan: list[str]
    current_step: int
    reflection: dict[str, Any]
    should_continue: bool
    iterations: int
    selected_tool: str
    tool_results: dict[str, Any]


class RAGAgent(BaseAgent):
    """RAG Agent with LangGraph workflow orchestration and multi-tool routing."""

    def __init__(
        self,
        retriever: VectorStoreRetriever,
        llm_client: LLMClient | None = None,
        use_hybrid_search: bool = True,
        use_reflection: bool = True,
    ):
        """
        Initialize RAG agent.

        Args:
            retriever: Vector store retriever
            llm_client: LLM client (defaults to global instance)
            use_hybrid_search: Whether to use hybrid search
            use_reflection: Whether to use reflection loop
        """
        super().__init__(name="rag_agent")

        self.retriever = retriever
        self.llm_client = llm_client or get_llm_client()
        self.settings = get_settings()
        self.use_reflection = use_reflection

        # Initialize all 4 tools
        self.tools = {
            "retriever": RetrieverTool(
                retriever=retriever,
                top_k=self.settings.retrieval_top_k,
            ),
            "calculator": CalculatorTool(),
            "web_search": WebSearchTool(),
            "code_executor": CodeExecutorTool(),
        }

        # Initialize workflows
        self.planning = PlanningWorkflow(llm_client=self.llm_client)
        self.reflection_workflow = ReflectionWorkflow(llm_client=self.llm_client)

        # Initialize re-ranker
        self.reranker = get_reranker(strategy="combined")

        # Build LangGraph workflow with full multi-tool routing
        self.graph = self._build_graph()

        logger.info("RAG Agent initialized with multi-tool LangGraph workflow")

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine with routing to all 4 tools."""
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("route", self._router_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("rerank", self._rerank_node)
        workflow.add_node("calculator", self._calculator_node)
        workflow.add_node("code_executor", self._code_executor_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("generate", self._generate_node)

        if self.use_reflection:
            workflow.add_node("reflect", self._reflect_node)

        # Set entry point to router
        workflow.set_entry_point("route")

        # Dynamic routing based on intent
        workflow.add_conditional_edges(
            "route",
            lambda state: state.get("selected_tool", "retrieve"),
            {
                "retrieve": "retrieve",
                "calculator": "calculator",
                "code_executor": "code_executor",
                "web_search": "web_search",
            },
        )

        # Edges leading to generation
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "generate")
        workflow.add_edge("calculator", "generate")
        workflow.add_edge("code_executor", "generate")
        workflow.add_edge("web_search", "generate")

        # Reflection loop
        if self.use_reflection:
            workflow.add_edge("generate", "reflect")
            workflow.add_conditional_edges(
                "reflect",
                self._should_retry,
                {
                    "retry": "generate",
                    "finish": END,
                },
            )
        else:
            workflow.add_edge("generate", END)

        return workflow.compile()

    async def _router_node(self, state: GraphState) -> GraphState:
        """Route user query to appropriate tool."""
        query = state["query"].strip()
        query_lower = query.lower()
        logger.info(f"Routing query: {query}")

        selected_tool = "retrieve"

        # Heuristic 1: Python Code Execution Check
        if any(
            phrase in query_lower
            for phrase in ["run code", "execute code", "run python", "execute python", "```python"]
        ) or query_lower.startswith(("def ", "import ", "for i in ")):
            selected_tool = "code_executor"

        # Heuristic 2: Live Web Search Check
        elif any(
            phrase in query_lower
            for phrase in ["search web", "google", "search internet", "search online", "latest news"]
        ):
            selected_tool = "web_search"

        # Heuristic 3: Pure Math / Calculator Check (only for pure math expressions)
        elif (
            bool(re.search(r"^\s*[\d\.\(\)\s\+\-\*\/\^%]+\s*$", query))
            or (
                any(query_lower.startswith(p) for p in ["calculate ", "compute ", "evaluate "])
                and not any(k in query_lower for k in ["table", "volume", "section", "clause", "handbook", "policy", "sla", "matrix", "tier", "quota", "vcpu", "bill", "cost", "parameter"])
                and bool(re.search(r"\d+\s*[\+\-\*\/\^%]\s*\d+", query))
            )
        ):
            selected_tool = "calculator"

        # Default: Knowledge Base Retrieval
        else:
            selected_tool = "retrieve"

        state["selected_tool"] = selected_tool
        logger.info(f"Query routed to tool: {selected_tool}")
        return state

    async def _retrieve_node(self, state: GraphState) -> GraphState:
        """Retrieval node."""
        logger.info("Executing retrieval node")
        query = state["query"]

        results = await self.retriever.similarity_search(
            query=query,
            top_k=self.settings.retrieval_top_k,
        )

        documents = [
            {
                "id": doc_id,
                "score": score,
                "content": text,
            }
            for doc_id, score, text in results
        ]

        state["retrieved_documents"] = documents
        logger.info(f"Retrieved {len(documents)} documents")
        return state

    async def _rerank_node(self, state: GraphState) -> GraphState:
        """Re-ranking node."""
        logger.info("Executing re-ranking node")
        query = state["query"]
        documents = state["retrieved_documents"]

        if not documents:
            return state

        docs_for_rerank = [
            (doc["id"], doc["score"], doc["content"]) for doc in documents
        ]

        reranked = await self.reranker.rerank(
            query=query,
            documents=docs_for_rerank,
            top_k=self.settings.rerank_top_k,
        )

        state["retrieved_documents"] = [
            {
                "id": doc_id,
                "score": score,
                "content": text,
            }
            for doc_id, score, text in reranked
        ]

        logger.info(f"Re-ranked to top {len(state['retrieved_documents'])} documents")
        return state

    async def _calculator_node(self, state: GraphState) -> GraphState:
        """Execute calculator tool."""
        query = state["query"]
        logger.info(f"Executing calculator node for: {query}")

        try:
            # Clean expression by keeping only numbers, arithmetic operators, parentheses, and spaces
            cleaned_expr = re.sub(r"[^0-9\+\-\*\/\(\)\.\s\^]", "", query).strip()
            if not cleaned_expr:
                cleaned_expr = query

            calc_tool = self.tools["calculator"]
            result = await calc_tool.execute(cleaned_expr)

            state["tool_results"]["calculator"] = f"Calculation Expression: {cleaned_expr}\nComputed Result: {result}"
            logger.info(f"Calculator result: {result}")

        except Exception as e:
            logger.warning(f"Calculator execution error: {e}")
            state["tool_results"]["calculator"] = f"Calculation failed: {str(e)}"

        return state

    async def _code_executor_node(self, state: GraphState) -> GraphState:
        """Execute Python code executor tool."""
        query = state["query"]
        logger.info("Executing code executor node")

        try:
            code = query
            # Extract code block if wrapped in markdown
            if "```python" in query:
                code = query.split("```python")[1].split("```")[0].strip()
            elif "```" in query:
                code = query.split("```")[1].split("```")[0].strip()
            else:
                code = re.sub(r"(?i)^(run python|execute python|run code|execute code|python|run):\s*", "", query).strip()

            executor_tool = self.tools["code_executor"]
            exec_result = await executor_tool.execute(code)

            output_text = exec_result.get("output", "")
            vars_text = exec_result.get("variables", "")
            state["tool_results"]["code_executor"] = f"Code Output:\n{output_text}\nVariables: {vars_text}"
            logger.info("Code executor finished successfully")

        except Exception as e:
            logger.warning(f"Code executor error: {e}")
            state["tool_results"]["code_executor"] = f"Code execution failed: {str(e)}"

        return state

    async def _web_search_node(self, state: GraphState) -> GraphState:
        """Execute live web search tool."""
        query = state["query"]
        logger.info(f"Executing web search node for: {query}")

        try:
            # Clean search query
            clean_q = re.sub(r"(?i)^(search web for|search online for|google|search internet for)\s*", "", query).strip()
            web_tool = self.tools["web_search"]
            search_results = await web_tool.execute(clean_q, num_results=3)

            snippets = []
            web_docs = []
            for i, r in enumerate(search_results):
                snippet_text = f"Title: {r.get('title', '')}\nSnippet: {r.get('snippet', '')}\nURL: {r.get('url', '')}"
                snippets.append(snippet_text)
                web_docs.append({
                    "id": f"web_{i}",
                    "score": 1.0,
                    "content": snippet_text,
                })

            state["retrieved_documents"] = web_docs
            state["tool_results"]["web_search"] = "\n\n".join(snippets)
            logger.info(f"Web search retrieved {len(search_results)} results")

        except Exception as e:
            logger.warning(f"Web search error: {e}")
            state["tool_results"]["web_search"] = f"Web search failed: {str(e)}"

        return state

    async def _generate_node(self, state: GraphState) -> GraphState:
        """Answer generation node synthesizing document context and tool outputs."""
        logger.info("Executing generation node")

        query = state["query"]
        documents = state.get("retrieved_documents", [])
        tool_results = state.get("tool_results", {})

        # Build comprehensive context
        context = [doc["content"] for doc in documents]

        for tool_name, output in tool_results.items():
            context.append(f"Tool Output ({tool_name.upper()}):\n{output}")

        # If no documents and no tool output, provide a general prompt
        if not context:
            prompt = f"Please answer the question accurately:\nQuestion: {query}\nAnswer:"
        else:
            prompt = PromptTemplates.rag_prompt(query=query, context=context)

        system_prompt = PromptTemplates.system_prompt()

        answer = await self.llm_client.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
        )

        state["answer"] = answer
        logger.info("Generated answer successfully")
        return state

    async def _reflect_node(self, state: GraphState) -> GraphState:
        """Reflection node."""
        logger.info("Executing reflection node")

        query = state["query"]
        answer = state["answer"]
        documents = state.get("retrieved_documents", [])
        tool_results = state.get("tool_results", {})

        context = [doc["content"] for doc in documents]
        for tool_name, output in tool_results.items():
            context.append(f"Tool ({tool_name}): {output}")

        # Reflect on answer quality
        reflection = await self.reflection_workflow.reflect_on_answer(
            query=query,
            answer=answer,
            context=context,
        )

        state["reflection"] = reflection
        state["iterations"] = state.get("iterations", 0) + 1

        logger.info(f"Reflection score: {reflection['score']}/10")
        return state

    def _should_retry(self, state: GraphState) -> str:
        """Determine if answer should be regenerated."""
        reflection = state.get("reflection", {})
        iterations = state.get("iterations", 0)

        if iterations >= 2:  # Max 2 retries
            return "finish"

        if reflection.get("score", 10) < 6.0:
            logger.info("Low reflection score, retrying generation")
            return "retry"

        return "finish"

    @traceable(name="rag_agent")
    async def run(
        self,
        query: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute RAG agent workflow.

        Args:
            query: User query
            **kwargs: Additional parameters

        Returns:
            Agent execution results with answer and metadata
        """
        logger.info(f"Running RAG agent for query: {query}")

        try:
            initial_state: GraphState = {
                "query": query,
                "retrieved_documents": [],
                "answer": "",
                "plan": [],
                "current_step": 0,
                "reflection": {},
                "should_continue": True,
                "iterations": 0,
                "selected_tool": "retrieve",
                "tool_results": {},
            }

            final_state = await self.graph.ainvoke(initial_state)

            result = {
                "query": query,
                "answer": final_state["answer"],
                "documents": final_state.get("retrieved_documents", []),
                "reflection": final_state.get("reflection", {}),
                "selected_tool": final_state.get("selected_tool", "retrieve"),
                "tool_results": final_state.get("tool_results", {}),
                "metadata": {
                    "iterations": final_state.get("iterations", 0),
                    "num_documents": len(final_state.get("retrieved_documents", [])),
                    "tool_used": final_state.get("selected_tool", "retrieve"),
                },
            }

            logger.info("RAG agent execution complete")
            return result

        except Exception as e:
            logger.error(f"RAG agent execution failed: {e}")
            raise AgentError(
                "RAG agent execution failed",
                details={"query": query},
                original_error=e,
            )

    async def stream(
        self,
        query: str,
        **kwargs,
    ):
        """Stream RAG agent execution."""
        logger.info(f"Streaming RAG agent for query: {query}")

        initial_state: GraphState = {
            "query": query,
            "retrieved_documents": [],
            "answer": "",
            "plan": [],
            "current_step": 0,
            "reflection": {},
            "should_continue": True,
            "iterations": 0,
            "selected_tool": "retrieve",
            "tool_results": {},
        }

        async for event in self.graph.astream(initial_state):
            yield event


# Factory function
async def create_rag_agent(
    retriever: VectorStoreRetriever,
    use_reflection: bool = True,
) -> RAGAgent:
    """Create and initialize RAG agent."""
    agent = RAGAgent(
        retriever=retriever,
        use_reflection=use_reflection,
    )
    logger.info("RAG agent created successfully")
    return agent
