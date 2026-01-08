/**
 * チャット機能
 * ============
 * RAG検索を実行するチャット機能
 */

// APIベースURL（実際の実装では環境変数から読み込む）
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:7071/api';

/**
 * チャットメッセージを送信
 */
async function sendMessage(message) {
  const headers = await getAuthHeaders();
  
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'メッセージ送信に失敗しました');
  }

  return await response.json();
}

/**
 * メッセージを表示
 */
function displayMessage(message, isUser = false) {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
  
  const headerDiv = document.createElement('div');
  headerDiv.className = 'message-header';
  headerDiv.textContent = isUser ? 'あなた' : 'アシスタント';
  
  const contentDiv = document.createElement('div');
  contentDiv.textContent = message;
  
  messageDiv.appendChild(headerDiv);
  messageDiv.appendChild(contentDiv);
  messagesContainer.appendChild(messageDiv);
  
  // スクロールを最下部に
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * ソース情報を表示
 */
function displaySources(sources) {
  if (!sources || sources.length === 0) return;

  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  const sourcesDiv = document.createElement('div');
  sourcesDiv.className = 'message assistant';
  sourcesDiv.style.fontSize = '0.875rem';
  sourcesDiv.style.color = 'var(--secondary-color)';
  
  const headerDiv = document.createElement('div');
  headerDiv.className = 'message-header';
  headerDiv.textContent = '参考資料';
  
  const sourcesList = document.createElement('ul');
  sourcesList.style.marginTop = '0.5rem';
  sourcesList.style.paddingLeft = '1.5rem';
  
  sources.forEach((source, index) => {
    const li = document.createElement('li');
    li.textContent = `${source.file_name} (類似度: ${(source.similarity * 100).toFixed(1)}%)`;
    sourcesList.appendChild(li);
  });
  
  sourcesDiv.appendChild(headerDiv);
  sourcesDiv.appendChild(sourcesList);
  messagesContainer.appendChild(sourcesDiv);
  
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * エラーメッセージを表示
 */
function displayError(message) {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  const errorDiv = document.createElement('div');
  errorDiv.className = 'message assistant';
  errorDiv.style.backgroundColor = '#ffebee';
  errorDiv.style.color = '#c62828';
  
  const headerDiv = document.createElement('div');
  headerDiv.className = 'message-header';
  headerDiv.textContent = 'エラー';
  
  const contentDiv = document.createElement('div');
  contentDiv.textContent = message;
  
  errorDiv.appendChild(headerDiv);
  errorDiv.appendChild(contentDiv);
  messagesContainer.appendChild(errorDiv);
  
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * チャット初期化
 */
function initChat() {
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  
  if (!chatForm || !messageInput) return;

  chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;

    // ユーザーメッセージを表示
    displayMessage(message, true);
    messageInput.value = '';
    messageInput.disabled = true;
    
    const submitButton = chatForm.querySelector('button[type="submit"]');
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.innerHTML = '<span class="loading"></span> 送信中...';
    }

    try {
      const response = await sendMessage(message);
      
      // アシスタントの回答を表示
      displayMessage(response.answer, false);
      
      // ソース情報を表示
      if (response.sources && response.sources.length > 0) {
        displaySources(response.sources);
      }
    } catch (error) {
      displayError(error.message || 'メッセージ送信に失敗しました');
    } finally {
      messageInput.disabled = false;
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = '送信';
      }
    }
  });
}

