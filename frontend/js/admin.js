/**
 * 管理機能
 * ==========
 * ファイル管理機能（アップロード、一覧表示、削除）
 */

// APIベースURL（実際の実装では環境変数から読み込む）
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:7071/api';

/**
 * ファイル一覧を取得
 */
async function getFiles(status = null) {
  const headers = await getAuthHeaders();
  
  let url = `${API_BASE_URL}/admin/files`;
  if (status) {
    url += `?status=${status}`;
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers: headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'ファイル一覧の取得に失敗しました');
  }

  return await response.json();
}

/**
 * ファイルをアップロード
 */
async function uploadFile(file) {
  const headers = await getAuthHeaders();
  // multipart/form-dataのため、Content-Typeは設定しない
  delete headers['Content-Type'];
  
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/admin/upload`, {
    method: 'POST',
    headers: {
      'Authorization': headers['Authorization'],
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'ファイルアップロードに失敗しました');
  }

  return await response.json();
}

/**
 * ファイルを削除
 */
async function deleteFile(fileId) {
  if (!confirm('このファイルを削除しますか？')) {
    return;
  }

  const headers = await getAuthHeaders();
  
  const response = await fetch(`${API_BASE_URL}/admin/delete`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ file_id: fileId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'ファイル削除に失敗しました');
  }

  return await response.json();
}

/**
 * ファイル一覧を表示
 */
function displayFiles(files) {
  const tbody = document.getElementById('files-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  if (files.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="5" style="text-align: center;">ファイルがありません</td>';
    tbody.appendChild(tr);
    return;
  }

  files.forEach(file => {
    const tr = document.createElement('tr');
    
    const statusBadge = getStatusBadge(file.status);
    const createdAt = new Date(file.created_at).toLocaleString('ja-JP');
    
    tr.innerHTML = `
      <td>${escapeHtml(file.file_name)}</td>
      <td>${createdAt}</td>
      <td>${statusBadge}</td>
      <td>${file.chunk_count || 0} / ${file.embedding_count || 0}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="handleDeleteFile('${file.id}')">
          削除
        </button>
      </td>
    `;
    
    tbody.appendChild(tr);
  });
}

/**
 * ステータスバッジを取得
 */
function getStatusBadge(status) {
  const badges = {
    'uploaded': '<span class="badge badge-uploaded">アップロード済み</span>',
    'indexing': '<span class="badge badge-indexing">処理中</span>',
    'indexed': '<span class="badge badge-indexed">完了</span>',
    'error': '<span class="badge badge-error">エラー</span>',
  };
  return badges[status] || status;
}

/**
 * HTMLエスケープ
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * ファイル削除処理
 */
async function handleDeleteFile(fileId) {
  try {
    await deleteFile(fileId);
    await loadFiles();
    showAlert('ファイルを削除しました', 'success');
  } catch (error) {
    showAlert(error.message || 'ファイル削除に失敗しました', 'error');
  }
}

/**
 * ファイル一覧を読み込み
 */
async function loadFiles() {
  const statusFilter = document.getElementById('status-filter')?.value || '';
  
  try {
    const data = await getFiles(statusFilter || null);
    displayFiles(data.files);
  } catch (error) {
    showAlert(error.message || 'ファイル一覧の取得に失敗しました', 'error');
  }
}

/**
 * アラートを表示
 */
function showAlert(message, type = 'info') {
  const alertDiv = document.getElementById('alert-message');
  if (!alertDiv) return;

  alertDiv.className = `alert alert-${type}`;
  alertDiv.textContent = message;
  alertDiv.style.display = 'block';

  setTimeout(() => {
    alertDiv.style.display = 'none';
  }, 5000);
}

/**
 * 管理画面初期化
 */
function initAdmin() {
  // ファイル一覧読み込み
  loadFiles();
  
  // ステータスフィルタ変更時
  const statusFilter = document.getElementById('status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', loadFiles);
  }
  
  // ファイルアップロード
  const fileInput = document.getElementById('file-input');
  const uploadArea = document.getElementById('upload-area');
  const uploadButton = document.getElementById('upload-button');
  
  if (fileInput && uploadArea && uploadButton) {
    // ファイル選択
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async function(e) {
      const file = e.target.files[0];
      if (!file) return;
      
      uploadButton.disabled = true;
      uploadButton.textContent = 'アップロード中...';
      
      try {
        await uploadFile(file);
        showAlert('ファイルをアップロードしました', 'success');
        await loadFiles();
        fileInput.value = '';
      } catch (error) {
        showAlert(error.message || 'ファイルアップロードに失敗しました', 'error');
      } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = 'アップロード';
      }
    });
    
    // ドラッグ&ドロップ
    uploadArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      this.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function() {
      this.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', async function(e) {
      e.preventDefault();
      this.classList.remove('dragover');
      
      const file = e.dataTransfer.files[0];
      if (!file) return;
      
      uploadButton.disabled = true;
      uploadButton.textContent = 'アップロード中...';
      
      try {
        await uploadFile(file);
        showAlert('ファイルをアップロードしました', 'success');
        await loadFiles();
      } catch (error) {
        showAlert(error.message || 'ファイルアップロードに失敗しました', 'error');
      } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = 'アップロード';
      }
    });
  }
}

