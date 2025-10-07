"""
LLMベースの高度なクエリプロセッサ
GPT/LLMを使用したキーワード抽出とクエリ最適化
"""

from typing import List, Dict, Any, Optional
import json
import asyncio
from dataclasses import dataclass
from loguru import logger

# 将来的にOpenAI APIやローカルLLMを使用するための基盤
# from openai import AsyncOpenAI
# from transformers import pipeline


@dataclass
class LLMQueryResult:
    """LLM処理結果"""
    original_query: str
    extracted_keywords: List[str]
    search_intent: str  # "factual", "procedural", "comparative", etc.
    metadata_filters: Dict[str, Any]  # 日付、カテゴリなどのフィルタ
    optimized_queries: List[str]  # 複数の最適化されたクエリ
    confidence: float


class LLMQueryProcessor:
    """
    LLMを使用した高度なクエリ処理
    
    機能:
    1. 自然言語からのキーワード抽出
    2. 検索意図の分類
    3. メタデータフィルタの推定
    4. 複数クエリの生成
    """
    
    def __init__(self, model_type: str = "local"):
        self.model_type = model_type
        self.model = None
        
        # プロンプトテンプレート
        self.keyword_extraction_prompt = """
あなたは技術文書検索の専門家です。以下の質問から、効果的な検索キーワードを抽出してください。

質問: {query}

以下の形式でJSONを返してください:
{{
    "keywords": ["キーワード1", "キーワード2", ...],
    "technical_terms": ["技術用語1", "技術用語2", ...],
    "search_intent": "factual|procedural|troubleshooting|comparison",
    "topic_category": "ubuntu|python|ros|ai|general",
    "optimized_queries": ["最適化クエリ1", "最適化クエリ2", ...],
    "confidence": 0.8
}}

重要:
- 研究室の技術文書検索に適したキーワードを抽出
- Ubuntu、Python、ROS、AI/機械学習関連の専門用語を優先
- 日本語と英語の両方を考慮
- 検索に有効な2-4個のキーワードに絞る
"""
        
        self._initialize_model()
    
    def _initialize_model(self):
        """モデルの初期化"""
        if self.model_type == "openai":
            # OpenAI GPT使用（将来実装）
            # self.client = AsyncOpenAI(api_key="your-api-key")
            logger.info("OpenAI model would be initialized here")
        elif self.model_type == "local":
            # ローカルLLM使用（将来実装）
            # self.model = pipeline("text-generation", model="elyza/ELYZA-japanese-Llama-2-7b-instruct")
            logger.info("Local LLM model would be initialized here")
        else:
            # フォールバック：ルールベース
            logger.info("Using rule-based fallback")
    
    async def process_query_with_llm(self, query: str) -> LLMQueryResult:
        """
        LLMを使用したクエリ処理（将来実装）
        """
        if self.model_type == "openai":
            return await self._process_with_openai(query)
        elif self.model_type == "local":
            return await self._process_with_local_llm(query)
        else:
            return self._process_with_rules(query)
    
    async def _process_with_openai(self, query: str) -> LLMQueryResult:
        """OpenAI GPTを使用した処理（将来実装）"""
        # 実装例（要API設定）:
        # response = await self.client.chat.completions.create(
        #     model="gpt-4-mini",
        #     messages=[
        #         {"role": "system", "content": "You are a technical search expert."},
        #         {"role": "user", "content": self.keyword_extraction_prompt.format(query=query)}
        #     ],
        #     temperature=0.3
        # )
        # 
        # result_json = json.loads(response.choices[0].message.content)
        # return LLMQueryResult(
        #     original_query=query,
        #     extracted_keywords=result_json["keywords"],
        #     search_intent=result_json["search_intent"],
        #     metadata_filters={"category": result_json["topic_category"]},
        #     optimized_queries=result_json["optimized_queries"],
        #     confidence=result_json["confidence"]
        # )
        
        logger.info("OpenAI processing not yet implemented")
        return self._process_with_rules(query)
    
    async def _process_with_local_llm(self, query: str) -> LLMQueryResult:
        """ローカルLLMを使用した処理（将来実装）"""
        # 実装例（要ローカルモデル）:
        # prompt = self.keyword_extraction_prompt.format(query=query)
        # response = self.model(prompt, max_length=500, temperature=0.3)
        # result_text = response[0]['generated_text']
        # result_json = self._parse_llm_response(result_text)
        
        logger.info("Local LLM processing not yet implemented")
        return self._process_with_rules(query)
    
    def _process_with_rules(self, query: str) -> LLMQueryResult:
        """ルールベースのフォールバック処理"""
        # 現在のQueryProcessorを活用
        from ..utils.query_processor import QueryProcessor
        
        processor = QueryProcessor()
        result = processor.process_query(query)
        
        # 検索意図の推定
        intent = self._classify_intent(query)
        
        # トピックカテゴリの推定
        category = self._classify_category(query, result['keywords'])
        
        return LLMQueryResult(
            original_query=query,
            extracted_keywords=result['keywords'],
            search_intent=intent,
            metadata_filters={"category": category},
            optimized_queries=[result['recommended_query']],
            confidence=0.7  # ルールベースは中程度の信頼度
        )
    
    def _classify_intent(self, query: str) -> str:
        """検索意図の分類"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['方法', 'やり方', 'how to', 'インストール', 'セットアップ']):
            return "procedural"
        elif any(word in query_lower for word in ['エラー', 'problem', '問題', '解決', 'troubleshoot']):
            return "troubleshooting"
        elif any(word in query_lower for word in ['違い', '比較', 'compare', 'difference']):
            return "comparison"
        else:
            return "factual"
    
    def _classify_category(self, query: str, keywords: List[str]) -> str:
        """トピックカテゴリの分類"""
        query_text = (query + " " + " ".join(keywords)).lower()
        
        if any(term in query_text for term in ['ubuntu', 'linux', 'os']):
            return "ubuntu"
        elif any(term in query_text for term in ['python', 'プログラミング', 'コード']):
            return "python"
        elif any(term in query_text for term in ['ros', 'robot', 'ロボット']):
            return "ros"
        elif any(term in query_text for term in ['ai', '機械学習', 'machine learning', 'deep learning']):
            return "ai"
        else:
            return "general"


class IterativeQueryProcessor:
    """
    IterKey手法の実装
    検索結果に基づいてクエリを反復改善
    """
    
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.llm_processor = LLMQueryProcessor()
    
    async def iterative_search(
        self, 
        initial_query: str,
        target_results: int = 5,
        quality_threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        反復的クエリ改善による検索
        
        プロセス:
        1. 初期クエリで検索
        2. 結果の品質評価
        3. 不十分な場合、クエリを改善して再検索
        4. 満足いく結果が得られるまで繰り返し
        """
        search_history = []
        current_query = initial_query
        
        for iteration in range(self.max_iterations):
            logger.info(f"IterKey iteration {iteration + 1}: '{current_query}'")
            
            # LLM処理
            llm_result = await self.llm_processor.process_query_with_llm(current_query)
            
            # 検索実行（ここでは既存のSearchServiceを使用）
            from .search_service import SearchService
            search_service = SearchService()
            
            search_results = search_service.semantic_search(
                llm_result.optimized_queries[0],
                limit=target_results * 2
            )
            
            # 品質評価
            high_quality_results = [r for r in search_results if r.score >= quality_threshold]
            
            iteration_result = {
                "iteration": iteration + 1,
                "query": current_query,
                "llm_processing": llm_result,
                "search_results": len(search_results),
                "high_quality_results": len(high_quality_results),
                "average_score": sum(r.score for r in search_results) / len(search_results) if search_results else 0
            }
            search_history.append(iteration_result)
            
            # 終了条件チェック
            if len(high_quality_results) >= target_results:
                logger.info(f"IterKey succeeded in {iteration + 1} iterations")
                break
            
            # 次のクエリ生成（改善ロジック）
            if iteration < self.max_iterations - 1:
                current_query = self._generate_improved_query(
                    initial_query, 
                    llm_result, 
                    search_results
                )
        
        return {
            "final_query": current_query,
            "total_iterations": len(search_history),
            "search_history": search_history,
            "final_results": search_results[:target_results]
        }
    
    def _generate_improved_query(
        self, 
        original_query: str, 
        llm_result: LLMQueryResult, 
        previous_results: List[Any]
    ) -> str:
        """
        検索結果に基づいてクエリを改善
        """
        # 簡単な改善ロジック（実際にはLLMを使用してより高度に）
        if not previous_results:
            # 結果がない場合：より一般的なキーワードを試す
            keywords = llm_result.extracted_keywords
            if len(keywords) > 1:
                return " ".join(keywords[:2])  # より少ないキーワードで
        
        # 結果が少ない場合：同義語展開
        if len(previous_results) < 3:
            return f"{llm_result.optimized_queries[0]} OR setup OR configuration"
        
        # デフォルト：元のクエリを返す
        return original_query


# 実装ガイドラインとTODO
"""
🚀 実装ロードマップ

Phase 1 (即座に実装可能):
- ルールベースのLLMQueryProcessor
- 既存QueryProcessorとの統合
- 基本的なIterativeQueryProcessor

Phase 2 (要ライブラリ追加):
- ローカルLLM統合（transformers使用）
- より高度なプロンプトエンジニアリング
- 検索結果の自動評価

Phase 3 (要外部API):
- OpenAI GPT統合
- Claude/Gemini統合
- 複数LLMの比較評価

実装優先度:
1. HybridSearchService (即座に効果あり)
2. LLMQueryProcessor のルールベース部分
3. 既存システムとの統合
4. IterativeQueryProcessor の基本版

"""
