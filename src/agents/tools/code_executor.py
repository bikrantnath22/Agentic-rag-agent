"""Code execution tool (sandboxed Python execution)."""

import ast
import asyncio
import sys
from io import StringIO
from typing import Any

from ...agents.base_agent import Tool
from ...observability.logging import get_logger
from ...utils.exceptions import AgentError

logger = get_logger(__name__)


class CodeExecutorTool(Tool):
    """Tool for executing Python code in a restricted environment."""

    # Allowed built-in functions
    ALLOWED_BUILTINS = {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "filter",
        "float",
        "int",
        "len",
        "list",
        "map",
        "max",
        "min",
        "print",
        "range",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "zip",
    }

    def __init__(self):
        """Initialize code executor tool."""
        super().__init__(
            name="code_executor",
            description="Execute Python code for data processing and analysis",
        )

    async def execute(self, code: str, timeout: int = 5) -> dict[str, Any]:
        """
        Execute Python code in a restricted environment with timeout protection.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (default: 5)

        Returns:
            Dictionary with execution results

        Raises:
            AgentError: If code execution fails, times out, or is unsafe
        """
        logger.info("Executing Python code with timeout protection")

        def _execute_sync() -> dict[str, Any]:
            # Validate code syntax
            ast.parse(code)

            # Capture stdout
            stdout = StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout

            # Create restricted namespace
            namespace = {"__builtins__": {}}

            # Add allowed builtins and safe standard modules
            import builtins
            import math
            for name in self.ALLOWED_BUILTINS:
                if hasattr(builtins, name):
                    namespace["__builtins__"][name] = getattr(builtins, name)
            namespace["math"] = math

            try:
                # Execute code
                exec(code, namespace)

                # Get output
                output = stdout.getvalue()

                # Extract variables
                variables = {
                    k: v
                    for k, v in namespace.items()
                    if not k.startswith("_") and k != "__builtins__"
                }

                return {
                    "success": True,
                    "output": output,
                    "variables": str(variables),
                    "error": None,
                }

            finally:
                sys.stdout = old_stdout

        try:
            loop = asyncio.get_running_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _execute_sync),
                timeout=float(timeout),
            )
            logger.info("Code executed successfully")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Code execution timed out after {timeout} seconds")
            raise AgentError(f"Code execution timed out after {timeout} seconds")

        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            raise AgentError(
                f"Syntax error in code: {e}",
                original_error=e,
            )

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            raise AgentError(
                f"Code execution failed: {e}",
                original_error=e,
            )
