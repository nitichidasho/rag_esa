"""
進捗表示機能付きの質問応答用HTMLテンプレート
"""

PROGRESS_QA_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>進捗表示機能付きRAG質問応答システム</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .input-section {
            margin-bottom: 30px;
        }
        
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            resize: vertical;
        }
        
        textarea:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .button-row {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            align-items: center;
        }
        
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover:not(:disabled) {
            background: #2980b9;
        }
        
        button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
        }
        
        .settings {
            display: flex;
            gap: 20px;
            align-items: center;
            font-size: 14px;
        }
        
        .settings label {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        /* 進捗表示 */
        .progress-section {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        
        .progress-section.active {
            display: block;
        }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease;
            width: 0%;
        }
        
        .progress-text {
            font-size: 14px;
            color: #555;
        }
        
        .progress-details {
            font-size: 12px;
            color: #777;
            margin-top: 5px;
        }
        
        /* 結果表示 */
        .result-section {
            margin-top: 30px;
        }
        
        .answer {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            margin-bottom: 20px;
        }
        
        .sources {
            margin-top: 20px;
        }
        
        .source-item {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .source-title {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .source-meta {
            font-size: 12px;
            color: #777;
        }
        
        .error {
            background: #fee;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            border-radius: 8px;
            color: #c0392b;
        }
        
        .loading {
            display: inline-block;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 進捗表示機能付きRAG質問応答システム</h1>
        
        <div class="input-section">
            <textarea id="questionInput" placeholder="質問を入力してください...例：esaから記事を取得してRAGシステムを作るにはどうしたらよいですか？"></textarea>
            
            <div class="button-row">
                <button id="askButton" onclick="askQuestionWithProgress()">質問する（進捗表示付き）</button>
                <button id="askSimpleButton" onclick="askQuestion()">質問する（通常）</button>
                
                <div class="settings">
                    <label>
                        <input type="checkbox" id="hybridSearch" checked>
                        ハイブリッド検索
                    </label>
                    <label>
                        記事数: <input type="number" id="contextLimit" value="5" min="1" max="10" style="width: 60px;">
                    </label>
                </div>
            </div>
        </div>
        
        <div id="progressSection" class="progress-section">
            <div class="progress-header">
                <h3>処理進捗</h3>
                <span id="progressPercentage">0%</span>
            </div>
            <div class="progress-bar">
                <div id="progressFill" class="progress-fill"></div>
            </div>
            <div id="progressText" class="progress-text">待機中...</div>
            <div id="progressDetails" class="progress-details"></div>
        </div>
        
        <div id="resultSection" class="result-section"></div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let currentEventSource = null;
        
        async function askQuestionWithProgress() {
            const question = document.getElementById('questionInput').value.trim();
            if (!question) {
                alert('質問を入力してください');
                return;
            }
            
            const askButton = document.getElementById('askButton');
            const askSimpleButton = document.getElementById('askSimpleButton');
            const progressSection = document.getElementById('progressSection');
            const resultSection = document.getElementById('resultSection');
            
            // UI状態を設定
            askButton.disabled = true;
            askSimpleButton.disabled = true;
            askButton.innerHTML = '<span class="loading">⟳</span> 処理中...';
            progressSection.classList.add('active');
            resultSection.innerHTML = '';
            
            try {
                // 進捗追跡付きで質問を送信
                const response = await fetch(`${API_BASE}/api/qa/with-progress`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Basic ' + btoa('lab_member:your_secure_password')
                    },
                    body: JSON.stringify({
                        question: question,
                        context_limit: parseInt(document.getElementById('contextLimit').value),
                        use_hybrid_search: document.getElementById('hybridSearch').checked
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                const taskId = result.task_id;
                
                // 進捗をリアルタイムで監視
                monitorProgress(taskId);
                
            } catch (error) {
                console.error('Error:', error);
                showError(`エラーが発生しました: ${error.message}`);
                resetUI();
            }
        }
        
        function monitorProgress(taskId) {
            if (currentEventSource) {
                currentEventSource.close();
            }
            
            currentEventSource = new EventSource(`${API_BASE}/api/progress/stream/${taskId}`);
            
            currentEventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.status === 'stream_ended') {
                        currentEventSource.close();
                        return;
                    }
                    
                    if (data.error) {
                        showError(`エラー: ${data.error}`);
                        resetUI();
                        return;
                    }
                    
                    updateProgress(data);
                    
                    if (data.status === 'completed') {
                        handleCompletion(data);
                        resetUI();
                    } else if (data.status === 'error') {
                        showError(data.message);
                        resetUI();
                    }
                    
                } catch (e) {
                    console.error('Progress parsing error:', e);
                }
            };
            
            currentEventSource.onerror = function(event) {
                console.error('EventSource failed:', event);
                currentEventSource.close();
                resetUI();
            };
        }
        
        function updateProgress(data) {
            const progressFill = document.getElementById('progressFill');
            const progressPercentage = document.getElementById('progressPercentage');
            const progressText = document.getElementById('progressText');
            const progressDetails = document.getElementById('progressDetails');
            
            progressFill.style.width = `${data.progress}%`;
            progressPercentage.textContent = `${data.progress}%`;
            progressText.textContent = data.message;
            
            if (data.details) {
                const detailsText = Object.entries(data.details)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(', ');
                progressDetails.textContent = detailsText;
            }
        }
        
        function handleCompletion(data) {
            const resultSection = document.getElementById('resultSection');
            
            if (data.result) {
                displayResult(data.result);
            } else {
                resultSection.innerHTML = '<div class="answer">処理が完了しましたが、結果が取得できませんでした。</div>';
            }
        }
        
        async function askQuestion() {
            const question = document.getElementById('questionInput').value.trim();
            if (!question) {
                alert('質問を入力してください');
                return;
            }
            
            const askButton = document.getElementById('askButton');
            const askSimpleButton = document.getElementById('askSimpleButton');
            const resultSection = document.getElementById('resultSection');
            
            askButton.disabled = true;
            askSimpleButton.disabled = true;
            askSimpleButton.innerHTML = '<span class="loading">⟳</span> 処理中...';
            resultSection.innerHTML = '';
            
            try {
                const response = await fetch(`${API_BASE}/api/qa/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Basic ' + btoa('lab_member:your_secure_password')
                    },
                    body: JSON.stringify({
                        question: question,
                        context_limit: parseInt(document.getElementById('contextLimit').value),
                        use_hybrid_search: document.getElementById('hybridSearch').checked
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                displayResult(result);
                
            } catch (error) {
                console.error('Error:', error);
                showError(`エラーが発生しました: ${error.message}`);
            } finally {
                resetUI();
            }
        }
        
        function displayResult(result) {
            const resultSection = document.getElementById('resultSection');
            
            let html = `
                <h3>回答</h3>
                <div class="answer">
                    <p><strong>質問:</strong> ${escapeHtml(result.question)}</p>
                    <p><strong>回答:</strong></p>
                    <div>${escapeHtml(result.answer).replace(/\\n/g, '<br>')}</div>
                </div>
            `;
            
            if (result.sources && result.sources.length > 0) {
                html += `
                    <h3>参考記事 (${result.sources.length}件)</h3>
                    <div class="sources">
                `;
                
                result.sources.forEach(source => {
                    html += `
                        <div class="source-item">
                            <div class="source-title">${escapeHtml(source.name)}</div>
                            <div class="source-meta">
                                カテゴリ: ${escapeHtml(source.category || '未分類')}
                                ${source.tags && source.tags.length > 0 ? 
                                    ` | タグ: ${source.tags.map(tag => escapeHtml(tag)).join(', ')}` : ''}
                            </div>
                        </div>
                    `;
                });
                
                html += '</div>';
            }
            
            html += `
                <div style="margin-top: 20px; font-size: 12px; color: #777;">
                    信頼度: ${(result.confidence * 100).toFixed(1)}% | 
                    使用サービス: ${escapeHtml(result.service_used)}
                </div>
            `;
            
            resultSection.innerHTML = html;
        }
        
        function showError(message) {
            const resultSection = document.getElementById('resultSection');
            resultSection.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
        }
        
        function resetUI() {
            const askButton = document.getElementById('askButton');
            const askSimpleButton = document.getElementById('askSimpleButton');
            const progressSection = document.getElementById('progressSection');
            
            askButton.disabled = false;
            askSimpleButton.disabled = false;
            askButton.innerHTML = '質問する（進捗表示付き）';
            askSimpleButton.innerHTML = '質問する（通常）';
            progressSection.classList.remove('active');
            
            if (currentEventSource) {
                currentEventSource.close();
                currentEventSource = null;
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Enterキーでの送信
        document.getElementById('questionInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                askQuestionWithProgress();
            }
        });
    </script>
</body>
</html>
"""
