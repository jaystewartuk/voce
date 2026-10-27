"""Markdown into blocks of plain text with styled spans: see blocks.py for the shape and inline.py for styles."""

from voce.markdown.blocks import Block, is_navigation, parse
from voce.markdown.inline import Link, Span, inline, linked, plain

__all__ = ["Block", "Link", "Span", "inline", "is_navigation", "linked", "parse", "plain"]
