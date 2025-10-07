"""
LangChainベースの質問応答サービス
Zennサイトの実装を参考にしたRAGシステム
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from loguru import logger

from ..config.settings import settings
from ..models.qa import QAResult
from ..models.esa_models import Article
from .search_service import SearchService
from ..utils.query_processor import QueryProcessor


class LangChainQAService:
    """LangChainスタイルの質問応答サービス"""
    
    def __init__(self):
        # 利用可能なモデルを試行順で定義（QA用途に最適化）
        self.model_candidates = [
            "weblab-GENIAC/Tanuki-8B-dpo-v1.0",  # 日本語特化高性能モデル
            "google/flan-t5-base",  # QA用途に最適
            "google/flan-t5-large", # より高性能
            "microsoft/GODEL-v1_1-large-seq2seq",  # 対話型だがQA可能
            "facebook/blenderbot-400M-distill",  # フォールバック
            "microsoft/DialoGPT-large"  # 最後の手段
        ]
        
        self.model_name = None
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.search_service = SearchService()
        self.query_processor = QueryProcessor()
        self._load_model()
    
    def _load_model(self):
        """利用可能なモデルを読み込み（GPU対応）"""
        # GPU環境の詳細情報をログ出力
        self._log_device_info()
        
        for model_name in self.model_candidates:
            try:
                logger.info(f"Trying to load model: {model_name}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                # パディングトークンを設定
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                # GPU対応のデバイス設定
                device_config = self._get_optimal_device_config()
                
                # モデルタイプに応じて異なる読み込み方法
                if "flan-t5" in model_name:
                    from transformers import T5ForConditionalGeneration
                    self.model = T5ForConditionalGeneration.from_pretrained(
                        model_name,
                        torch_dtype=device_config["dtype"],
                        device_map=device_config["device_map"]
                    )
                    self.pipeline = pipeline(
                        "text2text-generation",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        torch_dtype=torch.float16 if device_config["device_type"].startswith("GPU") else torch.float32,
                        device_map="auto",  # accelerateに任せる
                        max_length=500,  # デフォルトの最大長を大幅に増加
                        do_sample=True,
                        temperature=0.7
                    )
                else:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=device_config["dtype"],
                        device_map=device_config["device_map"],
                        low_cpu_mem_usage=True  # メモリ効率化
                    )
                    # accelerate使用時はdevice引数を削除
                    self.pipeline = pipeline(
                        "text-generation",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        torch_dtype=torch.float16 if device_config["device_type"].startswith("GPU") else torch.float32,
                        device_map="auto",  # accelerateに任せる
                        max_length=512,
                        do_sample=True,
                        temperature=0.7,
                        return_full_text=False
                    )
                
                self.model_name = model_name
                self.device_info = device_config
                logger.info(f"Successfully loaded model: {model_name} on {device_config['device_type']}")
                break
                
            except Exception as e:
                logger.warning(f"Failed to load model {model_name}: {e}")
                continue
        
    def _log_device_info(self):
        """デバイス情報をログ出力"""
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            logger.info(f"CUDA device count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"GPU {i}: {device_name} ({memory_total:.1f}GB)")
        else:
            logger.info("Running on CPU")
    
    def _get_optimal_device_config(self):
        """最適なデバイス設定を返す"""
        if torch.cuda.is_available():
            # GPU利用可能な場合
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            if gpu_memory >= 12:  # 12GB以上のGPU
                return {
                    "device_type": "GPU (High Memory)",
                    "device_map": "auto",
                    "dtype": torch.float16,
                    "pipeline_device": 0,
                    "batch_size": 8
                }
            elif gpu_memory >= 6:  # 6GB以上のGPU
                return {
                    "device_type": "GPU (Medium Memory)",
                    "device_map": "auto",
                    "dtype": torch.float16,
                    "pipeline_device": 0,
                    "batch_size": 4
                }
            else:  # 6GB未満のGPU
                return {
                    "device_type": "GPU (Low Memory)",
                    "device_map": "auto",
                    "dtype": torch.float16,
                    "pipeline_device": 0,
                    "batch_size": 2
                }
        else:
            # CPU利用の場合
            return {
                "device_type": "CPU",
                "device_map": None,
                "dtype": torch.float32,
                "pipeline_device": -1,
                "batch_size": 1
            }
    
    def answer_question(self, question: str, context_limit: int = 5) -> QAResult:
        """質問に対する回答を生成（LangChainスタイル）"""
        try:
            logger.info(f"Processing question: {question[:50]}...")
            
            # Step 0: クエリ前処理 - 自然言語質問から効果的なキーワードを抽出
            query_result = self.query_processor.process_query(question)
            optimized_query = query_result['recommended_query']
            
            logger.info(f"クエリ前処理結果:")
            logger.info(f"  元の質問: {question}")
            logger.info(f"  最適化クエリ: {optimized_query}")
            logger.info(f"  抽出キーワード: {query_result['keywords']}")
            logger.info(f"  技術用語: {query_result['technical_terms']}")
            
            # Step 1: 検索フェーズ - 最適化されたクエリで検索
            extended_limit = max(context_limit * 2, 10)
            logger.info(f"LangChain検索実行: 最適化クエリ='{optimized_query}', 取得件数={extended_limit}")
            
            # まず最適化クエリで検索
            search_results = self.search_service.semantic_search(
                query=optimized_query,
                limit=extended_limit,
                debug_mode=True
            )
            
            logger.info(f"最適化クエリ検索結果: {len(search_results)}件")
            
            # 最適化クエリで結果が少ない場合、元の質問でも検索
            if len(search_results) < 3 and optimized_query != question:
                logger.info(f"フォールバック検索実行: 元の質問='{question}'")
                fallback_results = self.search_service.semantic_search(
                    query=question,
                    limit=extended_limit,
                    debug_mode=True
                )
                
                # 結果をマージ（重複除去）
                seen_articles = set()
                merged_results = []
                
                # 最適化クエリの結果を優先
                for result in search_results:
                    if result.article.number not in seen_articles:
                        merged_results.append(result)
                        seen_articles.add(result.article.number)
                
                # フォールバック結果を追加
                for result in fallback_results:
                    if result.article.number not in seen_articles and len(merged_results) < extended_limit:
                        merged_results.append(result)
                        seen_articles.add(result.article.number)
                
                search_results = merged_results
                logger.info(f"マージ後検索結果: {len(search_results)}件")
            
            logger.info(f"LangChain検索結果: {len(search_results)}件の記事が見つかりました")
            
            # 検索結果の品質チェック（QAServiceと同じロジック）
            high_quality_results = []
            for result in search_results:
                # タイトルマッチまたは高スコアの記事を優先
                if result.score >= 1.5:  # タイトルマッチ（スコア2.0）や高品質な結果
                    high_quality_results.append(result)
                    logger.info(f"LangChain高品質結果: {result.article.name} (スコア: {result.score:.3f})")
            
            # 最終的に使用する記事を決定
            final_results = high_quality_results[:context_limit] if high_quality_results else search_results[:context_limit]
            
            if not final_results:
                logger.warning(f"LangChain検索で関連記事が見つかりませんでした: '{question}'")
                return QAResult(
                    question=question,
                    answer="申し訳ございませんが、ご質問の内容は川合研究室のデータベースに含まれていないようです。\n\nこのシステムは川合研究室の研究活動、プロジェクト、技術的な取り組みに関する情報を提供するものです。 一般的な技術情報については、公式ドキュメントやオンラインガイドをご参照ください。\n\n川合研究室に関するご質問でしたら、お気軽にお聞かせください。",
                    source_articles=[],
                    confidence=0.0,
                    generated_at=datetime.now()
                )
            
            logger.info(f"LangChain回答生成用記事: {len(final_results)}件を使用")
            for i, result in enumerate(final_results):
                logger.info(f"  {i+1}. {result.article.name} (スコア: {result.score:.3f})")
            
            # Step 2: コンテキスト構築
            context = self._build_context(final_results)
            logger.info(f"Built context with {len(final_results)} articles")
            
            # Step 3: 生成フェーズ - プロンプト設計とLLM呼び出し
            answer = self._generate_answer_with_prompt(question, context)
            
            # Step 4: 信頼度計算
            confidence = self._calculate_confidence(final_results)
            
            logger.info(f"Generated answer with confidence: {confidence:.2f}")
            
            return QAResult(
                question=question,
                answer=answer,
                source_articles=[result.article for result in final_results],
                confidence=confidence,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return QAResult(
                question=question,
                answer="エラーが発生しました。しばらく後にもう一度お試しください。",
                source_articles=[],
                confidence=0.0,
                generated_at=datetime.now()
            )
    
    def _build_context(self, search_results: List) -> str:
        """検索結果からコンテキストを構築（改善版）"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            article = result.article
            
            # 記事の基本情報
            context_part = f"### 記事{i}\n"
            context_part += f"タイトル: {article.name}\n"
            
            if article.category:
                context_part += f"分野: {article.category}\n"
            
            if article.tags:
                relevant_tags = [tag for tag in article.tags if tag.strip()][:3]  # 最大3つのタグ
                if relevant_tags:
                    context_part += f"キーワード: {', '.join(relevant_tags)}\n"
            
            # より関連性の高いテキスト内容を使用
            content = ""
            if hasattr(result, 'matched_text') and result.matched_text:
                content = result.matched_text
            elif hasattr(article, 'processed_text') and article.processed_text:
                # 重要な文を抽出
                content = self._extract_key_sentences(article.processed_text, 3)
            elif article.body_md:
                # マークダウン記号を除去して重要部分を抽出
                clean_text = self._clean_markdown(article.body_md)
                content = self._extract_key_sentences(clean_text, 3)
            
            if content:
                context_part += f"内容:\n{content}\n"
            
            context_part += f"関連度: {result.score:.2f}\n\n"
            context_parts.append(context_part)
        
        return "".join(context_parts)
    
    def _extract_key_sentences(self, text: str, num_sentences: int = 3) -> str:
        """テキストから重要な文を抽出"""
        try:
            sentences = [s.strip() for s in text.split('。') if len(s.strip()) > 10]
            
            if len(sentences) <= num_sentences:
                return '。'.join(sentences) + '。'
            
            # 長さと情報量でスコアリング
            scored_sentences = []
            for sentence in sentences:
                score = len(sentence)  # 基本スコア：文の長さ
                
                # 研究室関連キーワードボーナス
                research_keywords = ['研究', '開発', '技術', '学習', '実験', '分析', '成果', 'AI', '機械学習']
                for keyword in research_keywords:
                    if keyword in sentence:
                        score += 50
                
                scored_sentences.append((sentence, score))
            
            # スコア順でソートして上位を選択
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            selected = [s[0] for s in scored_sentences[:num_sentences]]
            
            return '。'.join(selected) + '。'
            
        except Exception:
            return text[:300] + "..." if len(text) > 300 else text
    
    def _clean_markdown(self, text: str) -> str:
        """マークダウン記号を除去してクリーンなテキストを生成"""
        import re
        
        # マークダウン記号を除去
        text = re.sub(r'#{1,6}\s*', '', text)  # ヘッダー
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # 強調
        text = re.sub(r'`([^`]+)`', r'\1', text)  # インラインコード
        text = re.sub(r'```[\s\S]*?```', '', text)  # コードブロック
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # リンク
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)  # 画像
        text = re.sub(r'\n{3,}', '\n\n', text)  # 余分な改行
        
        return text.strip()
    
    def _generate_answer_with_prompt(self, question: str, context: str) -> str:
        """Zennサイトのプロンプト設計を参考にした回答生成"""
        
        # Zennサイトのプロンプトテンプレートを参考
        template = """あなたは与えられた文書の内容に基づいて質問に答える専門家です。
質問に対して、文書の情報のみを使用して詳細かつ正確に回答してください。
文書に関連する情報がない場合は、「申し訳ありませんが、この文書にはその情報が含まれていません」と答えてください。

文脈情報:
{context}

質問: {question}

回答:"""
        
        # プロンプトを構築
        prompt = template.format(context=context, question=question)
        
        try:
            # モデルタイプに応じた生成
            if "flan-t5" in self.model_name:
                # T5の場合 - 自然な会話形式の日本語回答を促進
                try:
                    # 質問の種類を判定
                    question_type = self._analyze_question_type(question)
                    
                    # より単純で効果的なプロンプト作成
                    simple_prompt = f"""以下の情報を参考に、質問に丁寧な日本語で詳しく答えてください。

参考情報：
{context[:800]}

質問：{question}
回答："""
                    
                    response = self.pipeline(
                        simple_prompt,
                        max_length=400,  # 十分な長さを確保して完全な回答を生成
                        min_length=30,   # 最小長を増やして意味のある回答を確保
                        num_beams=2,     # ビーム数を増やして品質向上
                        no_repeat_ngram_size=3,  # 繰り返し防止を適度に設定
                        do_sample=False,  # サンプリングを無効化して安定性向上
                        early_stopping=True,
                        repetition_penalty=1.2,  # ペナルティを適度に調整
                        length_penalty=1.0,  # 長さペナルティを追加
                        pad_token_id=self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id
                    )
                    if response and len(response) > 0:
                        raw_answer = response[0]['generated_text']
                        logger.info(f"T5 raw output length: {len(raw_answer)}")
                        logger.info(f"T5 raw output: '{raw_answer}'")  # 全文をログ出力
                        
                        # 入力プロンプトを除去
                        if "回答:" in raw_answer:
                            answer = raw_answer.split("回答:")[-1].strip()
                            logger.info(f"Answer after '回答:' split: '{answer}'")
                        elif "答え:" in raw_answer:
                            answer = raw_answer.split("答え:")[-1].strip()
                            logger.info(f"Answer after '答え:' split: '{answer}'")
                        else:
                            # プロンプト全体を除去
                            if len(raw_answer) > len(simple_prompt):
                                answer = raw_answer[len(simple_prompt):].strip()
                                logger.info(f"Answer after prompt removal: '{answer}'")
                            else:
                                answer = raw_answer.strip()
                                logger.info(f"Answer as-is (shorter than prompt): '{answer}'")
                        
                        logger.info(f"T5 processed answer length: {len(answer)}")
                        logger.info(f"T5 processed answer: '{answer}'")
                        
                        # 自然な会話形式に調整
                        answer = self._make_conversational(answer, question_type)
                        logger.info(f"T5 conversational answer: '{answer}'")
                    else:
                        answer = "回答を生成できませんでした。"
                        logger.warning("T5 generated empty response")
                except Exception as t5_error:
                    logger.error(f"T5 generation error: {t5_error}")
                    answer = self._create_fallback_answer(question, context)
            else:
                # DialoGPTなどの生成系モデルの場合
                try:
                    # プロンプトを短縮してトークン制限内に収める
                    short_prompt = self._create_short_prompt(question, context)
                    logger.info(f"Generation prompt: {short_prompt[:200]}...")
                    
                    response = self.pipeline(
                        short_prompt,
                        max_new_tokens=200,  # トークン数を増やして十分な回答を生成
                        do_sample=True,
                        temperature=0.7,  # 温度を適度に設定
                        top_p=0.9,
                        repetition_penalty=1.2,
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        return_full_text=False  # プロンプトを含まない
                    )
                    
                    logger.info(f"Pipeline response: {response}")
                    
                    if response and len(response) > 0:
                        generated_text = response[0]['generated_text']
                        logger.info(f"Generated text: '{generated_text}'")
                        
                        # プロンプト部分を除去
                        if "回答:" in generated_text:
                            answer = generated_text.split("回答:")[-1].strip()
                        elif "答え:" in generated_text:
                            answer = generated_text.split("答え:")[-1].strip()
                        else:
                            answer = generated_text.strip()
                        
                        logger.info(f"Processed answer: '{answer}'")
                    else:
                        logger.warning("Pipeline returned empty response")
                        answer = "回答を生成できませんでした。"
                        
                except Exception as gen_error:
                    logger.error(f"Generation error: {gen_error}")
                    # フォールバック：シンプルな要約を作成
                    answer = self._create_fallback_answer(question, context)
            
            # 後処理：余分な文字を除去
            answer = self._post_process_answer(answer)
            logger.info(f"Final processed answer: '{answer[:100]}...'")
            
            # 不適切な回答の場合はフォールバックに切り替え（条件を厳格化）
            if ("適切な回答を生成できませんでした" in answer and "フォールバック" in answer):
                logger.info("Using fallback answer due to processing failure")
                answer = self._create_fallback_answer(question, context)
            
            return answer if answer else self._create_fallback_answer(question, context)
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return self._create_fallback_answer(question, context)
    
    def _post_process_answer(self, answer: str) -> str:
        """回答の後処理"""
        original_answer = answer
        logger.info(f"Post-processing answer: '{answer}'")  # 全文をログ出力
        
        # 改行を整理
        answer = answer.replace('\n\n', '\n').strip()
        
        # 特殊文字の処理
        answer = answer.replace('</s>', '').replace('<s>', '')
        answer = answer.replace('<pad>', '').replace('<unk>', '')
        
        # DialoGPT特有の問題文字列を除去
        problematic_phrases = ['ILY', 'I love you', 'lol', 'haha', ':)', ':(', 'XD']
        for phrase in problematic_phrases:
            answer = answer.replace(phrase, '')
        
        # 明らかに問題のある絵文字のみ検出（条件を大幅に緩和）
        if '😀' in answer or '😂' in answer or ':smiling_face' in answer.lower():
            logger.warning(f"Detected obvious problematic emojis: '{answer}'")
            return "適切な回答を生成できませんでした。フォールバック回答を使用します。"
        
        # 空の回答をチェック（最優先）
        if not answer or len(answer.strip()) < 3:
            logger.warning(f"Empty or too short answer: '{answer}'")
            return "適切な回答を生成できませんでした。"
        
        # 短すぎる回答の基準をさらに緩和（15文字以上なら許可）
        if len(answer.strip()) < 15:
            logger.warning(f"Answer too short: '{answer}' (length: {len(answer.strip())})")
            return "適切な回答を生成できませんでした。フォールバック回答を使用します。"
        
        # 意味のない回答をチェック
        if answer.strip().lower() in ['yes', 'no', 'ok', 'sure']:
            logger.warning(f"Meaningless answer: '{answer}'")
            return "適切な回答を生成できませんでした。フォールバック回答を使用します。"
        
        # 数字のみの回答を検出
        if answer.strip().replace(' ', '').replace(':', '').replace('###', '').isdigit():
            logger.warning(f"Detected numeric-only output: '{answer}'")
            return "適切な回答を生成できませんでした。フォールバック回答を使用します。"
        
        # URLのみの回答を検出
        if answer.strip().startswith('http') and ' ' not in answer.strip():
            logger.warning(f"URL-only answer detected: '{answer}'")
            return "適切な回答を生成できませんでした。フォールバック回答を使用します。"
        
        logger.info(f"Answer passed post-processing: '{answer}'")
        return answer.strip()
    
    def _analyze_question_type(self, question: str) -> str:
        """質問のタイプを分析"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['どのような', 'どんな', 'なんの', '何の']):
            return 'descriptive'  # 説明的な質問
        elif any(word in question_lower for word in ['いつ', 'when', '時期']):
            return 'temporal'     # 時間関連の質問
        elif any(word in question_lower for word in ['どこ', 'where', '場所']):
            return 'location'     # 場所関連の質問
        elif any(word in question_lower for word in ['なぜ', 'why', '理由']):
            return 'causal'       # 原因・理由の質問
        elif any(word in question_lower for word in ['教えて', '知りたい', '動向', '状況']):
            return 'informational'  # 情報取得の質問
        else:
            return 'general'      # 一般的な質問
    
    def _create_conversational_prompt(self, question: str, context: str, question_type: str) -> str:
        """質問タイプに応じた自然な会話形式のプロンプトを作成"""
        
        # コンテキストを適切な長さに調整
        trimmed_context = context[:1000]
        
        if question_type == 'informational':
            return f"""あなたは研究室の活動について詳しい専門家です。以下の情報を基に、質問に対して丁寧で分かりやすい日本語で回答してください。

研究室情報:
{trimmed_context}

質問: {question}

回答: 川合研究室の動向についてお答えします。"""
        
        elif question_type == 'descriptive':
            return f"""以下の情報を参考に、質問について具体的で詳細な説明をしてください。

情報:
{trimmed_context}

質問: {question}

回答:"""
        
        else:
            return f"""以下の研究室に関する情報を基に、質問に対して自然で分かりやすい日本語で回答してください。

情報:
{trimmed_context}

質問: {question}

回答:"""
    
    def _make_conversational(self, answer: str, question_type: str) -> str:
        """回答をより自然な会話形式に調整"""
        if not answer or len(answer.strip()) < 10:
            return answer
        
        # 既に適切な回答の場合はそのまま返す
        if answer.startswith(('川合研究室', 'こちら', 'この', '研究室')):
            return answer
        
        # 質問タイプに応じて自然な導入部を追加
        if question_type == 'informational':
            if not answer.startswith(('川合研究室', '検索結果')):
                answer = f"川合研究室の動向について、{answer}"
        
        # 文末の調整
        if not answer.endswith(('.', '。', 'す', 'ます', 'した', 'でした')):
            if 'です' not in answer and 'ます' not in answer:
                answer += "。"
        
        return answer
    
    def _create_short_prompt(self, question: str, context: str) -> str:
        """短縮プロンプトを作成（トークン制限対応）"""
        # コンテキストを適切な長さに調整
        short_context = context[:600]  # Tanuki-8B用に少し長めに設定
        
        # モデルタイプに応じたプロンプト
        if "flan-t5" in self.model_name:
            # T5用のプロンプト
            short_prompt = f"""以下の文書に基づいて質問に回答してください。

文書: {short_context}

質問: {question}"""
        elif "Tanuki" in self.model_name:
            # Tanuki-8B用の最適化されたプロンプト
            short_prompt = f"""以下は川合研究室に関する文書です。この情報を参考にして、質問に詳しく回答してください。

【参考文書】
{short_context}

【質問】
{question}

【回答】
"""
        else:
            # その他の生成系モデル用のプロンプト
            short_prompt = f"""文書を参考に質問に答えてください。

文書: {short_context}

質問: {question}
回答:"""
        return short_prompt
    
    def _create_fallback_answer(self, question: str, context: str) -> str:
        """改善されたフォールバック回答を作成"""
        # コンテキストから重要な情報を抽出
        lines = context.split('\n')
        titles = [line for line in lines if line.startswith('タイトル:')]
        contents = [line for line in lines if line.startswith('内容:')]
        
        # Ubuntu環境構築に関する特別処理
        if 'ubuntu' in question.lower() and ('環境構築' in question or '機械学習' in question):
            answer = "Ubuntu環境での機械学習環境構築について、関連する情報をお伝えします。\n\n"
            
            # タイトルから関連する情報を抽出
            relevant_info = []
            for title in titles:
                clean_title = title.replace('タイトル:', '').strip()
                if any(keyword in clean_title for keyword in ['AI', '機械学習', 'Python', 'セミナー', 'ロボット']):
                    relevant_info.append(clean_title)
            
            if relevant_info:
                answer += "【関連する学習リソース】\n"
                for info in relevant_info[:3]:
                    answer += f"• {info}\n"
                answer += "\n"
            
            answer += "【一般的な環境構築手順】\n"
            answer += "1. Python環境のセットアップ (Anaconda/Miniconda推奨)\n"
            answer += "2. 必要なライブラリのインストール (numpy, pandas, scikit-learn等)\n"
            answer += "3. GPU利用時はCUDA/cuDNNの設定\n"
            answer += "4. Jupyter Notebookの環境構築\n\n"
            answer += "川合研究室では、AI・機械学習分野の研究を行っており、関連する技術情報を提供しています。"
            
            return answer
        
        # esaでRAGを作るに関する特別処理（より詳細化）
        if 'esaでRAGを作る' in ''.join(titles) or 'esa' in question.lower() and 'rag' in question.lower():
            answer = "esaから記事を取得してRAGシステムを構築する手順について説明いたします。\n\n"
            
            # 具体的な手順を提供
            answer += "【主要な手順】\n"
            answer += "1. ESA APIを使用した記事データの取得\n"
            answer += "2. 記事内容の前処理とベクトル化\n" 
            answer += "3. ベクトルデータベースへの格納\n"
            answer += "4. 質問応答システムの構築\n\n"
            
            # 記事の具体的内容があれば追加
            for content_line in contents:
                content = content_line.replace('内容:', '').strip()
                if content:
                    # 技術的な詳細を抽出
                    if any(keyword in content for keyword in ['API', 'システム', '手順', '方法', 'データ']):
                        sentences = [s.strip() for s in content.split('。') if len(s.strip()) > 15][:2]
                        if sentences:
                            answer += "【技術的詳細】\n"
                            answer += '。'.join(sentences) + '。\n\n'
                            break
            
            answer += "川合研究室では、これらの技術を活用してQAシステムの構築を進めています。"
            
            return answer
        
        # 一般的なフォールバック処理
        if titles:
            answer = "川合研究室の最新動向について、以下の情報をお伝えします：\n\n"
            
            # より自然な表現でタイトルと概要を組み合わせ
            for i, title in enumerate(titles[:2]):  # 最大2件に制限
                clean_title = title.replace('タイトル:', '').strip()
                answer += f"• {clean_title}\n"
                
                # 対応する内容があれば要約を追加
                if i < len(contents):
                    content = contents[i].replace('内容:', '').strip()
                    summary = self._create_natural_summary(content, max_length=80)
                    if summary:
                        answer += f"  {summary}\n"
            
            answer += "\n詳細な情報については、各記事をご参照ください。"
        else:
            answer = "申し訳ございません。現在システムの処理に問題が発生しており、詳細な回答を生成できませんでした。\n"
            answer += "より具体的なキーワードで再度検索していただけますでしょうか。"
        
        return answer
    
    def _create_natural_summary(self, content: str, max_length: int = 120) -> str:
        """自然な要約を作成"""
        if len(content) <= max_length:
            return content
        
        # 文で分割して重要な部分を選択
        sentences = [s.strip() + '。' for s in content.split('。') if len(s.strip()) > 5]
        
        if not sentences:
            return content[:max_length] + "..."
        
        # 最初の文を基本とする
        summary = sentences[0]
        
        # 重要キーワードを含む文を探して追加
        important_keywords = ['研究', '開発', '技術', 'AI', '機械学習', '成果', '活動']
        for sentence in sentences[1:]:
            if len(summary) + len(sentence) > max_length:
                break
            if any(keyword in sentence for keyword in important_keywords):
                summary += sentence
                break
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def _calculate_confidence(self, search_results: List) -> float:
        """信頼度計算（Zennサイトの検証結果を参考）"""
        if not search_results:
            return 0.0
        
        # 検索結果のスコアと記事数に基づく信頼度
        scores = [result.score for result in search_results]
        avg_score = sum(scores) / len(scores)
        
        # 記事数による補正（より多くの記事があると信頼度向上）
        article_count_bonus = min(len(search_results) / 10.0, 0.2)
        
        # 最高スコアが高い場合の補正
        max_score = max(scores)
        high_score_bonus = 0.1 if max_score > 0.8 else 0.0
        
        confidence = min(avg_score + article_count_bonus + high_score_bonus, 1.0)
        
        return confidence
    
    def get_model_info(self) -> Dict[str, Any]:
        """現在使用中のモデル情報を返す"""
        base_info = {
            "model_name": self.model_name,
            "model_type": "LangChain-style RAG",
            "capabilities": [
                "Document-based QA",
                "Context-aware responses", 
                "Multi-article synthesis"
            ],
            "implementation_based_on": "Zenn RAG tutorial"
        }
        
        # デバイス情報を追加
        if hasattr(self, 'device_info'):
            base_info["device_config"] = self.device_info
            base_info["gpu_optimized"] = self.device_info["device_type"].startswith("GPU")
        
        return base_info
    
    def _log_device_info(self):
        """デバイス情報をログ出力"""
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            logger.info(f"CUDA device count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"GPU {i}: {device_name} ({memory_total:.1f}GB)")
        else:
            logger.info("Running on CPU")
    
    def _get_optimal_device_config(self):
        """最適なデバイス設定を返す"""
        # 設定による強制CPU使用チェック
        from ..config.settings import settings
        if settings.force_cpu:
            logger.info("Forced to use CPU by configuration")
            return {
                "device_type": "CPU (Forced)",
                "device_map": None,
                "dtype": torch.float32,
                "pipeline_device": -1,
                "batch_size": 1,
                "memory_gb": 0
            }
        
        if torch.cuda.is_available() and settings.enable_gpu:
            # GPU利用可能な場合
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            usable_memory = gpu_memory * settings.gpu_memory_fraction
            
            if usable_memory >= 10:  # 12GB以上のGPU (RTX 3080 Ti以上)
                return {
                    "device_type": "GPU (High Memory)",
                    "device_map": "auto",
                    "dtype": torch.float16,
                    "pipeline_device": 0,
                    "batch_size": 8,
                    "memory_gb": gpu_memory,
                    "usable_memory_gb": usable_memory
                }
            elif usable_memory >= 5:  # 6GB以上のGPU (RTX 3060以上)
                return {
                    "device_type": "GPU (Medium Memory)", 
                    "device_map": "auto",
                    "dtype": torch.float16,
                    "pipeline_device": 0,
                    "batch_size": 4,
                    "memory_gb": gpu_memory,
                    "usable_memory_gb": usable_memory
                }
            else:  # 6GB未満のGPU
                return {
                    "device_type": "GPU (Low Memory)",
                    "device_map": "auto",
                    "dtype": torch.float16,
                    "pipeline_device": 0,
                    "batch_size": 2,
                    "memory_gb": gpu_memory,
                    "usable_memory_gb": usable_memory
                }
        else:
            # CPU利用の場合
            return {
                "device_type": "CPU",
                "device_map": None,
                "dtype": torch.float32,
                "pipeline_device": -1,
                "batch_size": 1,
                "memory_gb": 0
            }

    def answer_question_with_context(self, question: str, contexts: List, progress_tracker=None, **kwargs) -> QAResult:
        """
        与えられたコンテキストを使用して質問に答える
        ハイブリッド検索結果を受け取って回答を生成
        """
        try:
            logger.info(f"Processing question with provided context: {question[:50]}...")
            logger.info(f"Number of contexts provided: {len(contexts)}")
            
            # 進捗更新: 開始
            if progress_tracker:
                progress_tracker.update(10, "質問の解析を開始しています...", {"question": question[:50]})
            
            # コンテキストからのArticle形式変換
            articles = []
            for ctx in contexts:
                # HybridSearchResultからArticleへの変換
                if hasattr(ctx, 'article_id') and hasattr(ctx, 'title'):
                    # 簡易Articleオブジェクト作成
                    from ..models.esa_models import Article
                    
                    article = Article(
                        number=ctx.article_id,
                        name=ctx.title,
                        full_name=ctx.title,
                        wip=False,
                        body_md=ctx.content if hasattr(ctx, 'content') else '',
                        body_html='',
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        tags=[],
                        category='',
                        url='',
                        created_by_id=0,
                        updated_by_id=0,
                        processed_text=ctx.content if hasattr(ctx, 'content') else ''
                    )
                    articles.append(article)
                elif hasattr(ctx, 'article'):
                    # 既にArticle形式の場合
                    articles.append(ctx.article)
            
            # 進捗更新: コンテキスト処理
            if progress_tracker:
                progress_tracker.update(25, f"コンテキストを処理中... ({len(articles)}件の記事)", 
                                      {"articles_count": len(articles)})
            
            if not articles:
                logger.warning("No valid articles found in provided contexts")
                if progress_tracker:
                    progress_tracker.error("有効な記事が見つかりませんでした")
                return QAResult(
                    question=question,
                    answer="申し訳ございませんが、提供されたコンテキストから回答を生成できませんでした。",
                    source_articles=[],
                    confidence=0.0,
                    generated_at=datetime.now()
                )
            
            # 進捗更新: コンテキスト構築
            if progress_tracker:
                progress_tracker.update(40, "コンテキストを構築中...", 
                                      {"processing_articles": len(articles)})
            
            # コンテキスト文字列を構築
            context_parts = []
            sources = []
            
            for i, article in enumerate(articles[:kwargs.get('context_limit', 5)], 1):
                context_part = f"【記事{i}: {article.name}】\n"
                
                if article.category:
                    context_part += f"分野: {article.category}\n"
                
                if article.tags:
                    relevant_tags = [tag for tag in article.tags if tag.strip()][:3]
                    if relevant_tags:
                        context_part += f"キーワード: {', '.join(relevant_tags)}\n"
                
                # 記事内容を追加
                content = ""
                if hasattr(article, 'processed_text') and article.processed_text:
                    content = self._extract_key_sentences(article.processed_text, 3)
                elif article.body_md:
                    clean_text = self._clean_markdown(article.body_md)
                    content = self._extract_key_sentences(clean_text, 3)
                
                if content:
                    context_part += f"内容: {content}\n"
                
                context_parts.append(context_part)
                
                # ソース情報を追加
                sources.append({
                    "article_number": article.number,
                    "title": article.name,
                    "category": article.category or "未分類",
                    "url": article.url or ""
                })
            
            combined_context = "\n".join(context_parts)
            logger.info(f"コンテキスト長: {len(combined_context)}文字")
            
            # 進捗更新: 質問分析
            if progress_tracker:
                progress_tracker.update(60, "質問タイプを分析中...", 
                                      {"context_length": len(combined_context)})
            
            # 質問タイプを分析
            question_type = self._analyze_question_type(question)
            
            # 進捗更新: プロンプト構築
            if progress_tracker:
                progress_tracker.update(70, "AIモデル用のプロンプトを構築中...", 
                                      {"question_type": question_type})
            
            # LLMプロンプト構築
            prompt = self._create_conversational_prompt(question, combined_context, question_type)
            logger.info(f"プロンプト長: {len(prompt)}文字")
            
            # 進捗更新: LLM推論開始
            if progress_tracker:
                progress_tracker.update(80, "AIモデルによる回答生成中...", 
                                      {"prompt_length": len(prompt)})
            
            # LLM推論実行
            response_text = self._generate_answer_with_prompt(question, combined_context)
            
            # 進捗更新: 品質チェック
            if progress_tracker:
                progress_tracker.update(95, "回答の品質をチェック中...", 
                                      {"response_length": len(response_text)})
            
            # 品質チェック - 簡易的な信頼度計算
            confidence = 0.8 if len(articles) >= 3 else 0.6
            
            result = QAResult(
                question=question,
                answer=response_text,
                source_articles=articles[:kwargs.get('context_limit', 5)],
                confidence=confidence,
                generated_at=datetime.now()
            )
            
            # 進捗更新: 完了
            if progress_tracker:
                progress_tracker.complete("回答生成が完了しました", {
                    "confidence": confidence,
                    "articles_used": len(articles),
                    "response_length": len(response_text)
                })
            
            logger.info(f"回答生成完了 - 信頼度: {confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"QA処理エラー: {e}", exc_info=True)
            
            # 進捗更新: エラー
            if progress_tracker:
                progress_tracker.error(str(e))
                
            return QAResult(
                question=question,
                answer=f"申し訳ございませんが、回答の生成中にエラーが発生しました: {str(e)}",
                source_articles=[],
                confidence=0.0,
                generated_at=datetime.now()
            )
