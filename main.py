#!/usr/bin/env python3
"""
研究室 esa.io RAGシステム メインエントリーポイント
"""

import uvicorn
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="localhost",
        port=8000,
        reload=True
    )
