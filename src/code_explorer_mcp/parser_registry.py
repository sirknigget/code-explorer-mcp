from __future__ import annotations

from code_explorer_mcp.parsing.base import ParserRegistry
from code_explorer_mcp.parsing.python_parser import PythonParser
from code_explorer_mcp.parsing.typescript_parser import TypeScriptParser

DEFAULT_PARSER_REGISTRY = ParserRegistry([PythonParser(), TypeScriptParser()])
