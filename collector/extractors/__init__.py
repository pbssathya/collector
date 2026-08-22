"""Reusable source-format extractors for Collector."""

from .pdf import extract_pdf_structure, iter_pdf_lines

__all__ = ["extract_pdf_structure", "iter_pdf_lines"]
