"""
CrewAI Telemetry Definitions
============================
Hooks and callbacks for monitoring CrewAI agent performance and vector retrieval metrics.
"""

def log_agent_execution(agent_name: str, task: str, duration_ms: float):
    """Logs the execution time and status of an agentic workflow stage."""
    print(f"[METRICS] Agent {agent_name} completed task '{task}' in {duration_ms}ms")

def monitor_vector_retrieval(query: str, num_results: int, latency_ms: float):
    """Monitors embedding retrieval latency from AstraDB."""
    print(f"[METRICS] Retrieved {num_results} documents for query '{query}' in {latency_ms}ms")
