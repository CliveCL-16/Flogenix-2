from typing import List, Any

class ToolExecutor:
    """A simple helper class to help with calling tools."""
    
    def __init__(self, tools: List[Any]):
        """
        Initialize the ToolExecutor with a list of tool instances.

        Args:
            tools (List[Any]): A list of tool instances to be executed.
        """
        # Use the tool's 'name' attribute instead of __name__
        self.tools = {tool.name: tool for tool in tools}

    def invoke(self, tool_name: str, tool_input: Any) -> Any:
        """
        Invoke a tool by its name with the provided input.

        Args:
            tool_name (str): The name of the tool to execute.
            tool_input (Any): The input to pass to the tool.

        Returns:
            Any: The result of the tool execution.

        Raises:
            ValueError: If the tool name is not recognized.
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        # If the tool is a StructuredTool, call its run() method
        tool = self.tools[tool_name]
        if hasattr(tool, "run"):
            return tool.run(tool_input)
        else:
            # Fallback if the tool is a plain callable
            return tool(tool_input)
