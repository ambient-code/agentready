"""LLM prompt templates loaded from package resources."""

import importlib.resources

from .loader import load_prompt

__all__ = ["load_prompt"]
