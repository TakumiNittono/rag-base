/**
 * 認証機能
 * ==========
 * Supabase Authを使用した認証処理
 */

// Supabase設定（環境変数から読み込む必要があるが、ここでは直接設定）
// 実際の実装では、環境変数や設定ファイルから読み込む
const SUPABASE_URL = window.SUPABASE_URL || '';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || '';

let supabaseClient = null;

/**
 * Supabaseクライアントを初期化
 */
function initSupabase() {
  if (typeof supabase === 'undefined') {
    console.error('Supabaseクライアントが読み込まれていません');
    return null;
  }

  if (!supabaseClient) {
    supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return supabaseClient;
}

/**
 * 現在のユーザーを取得
 */
async function getCurrentUser() {
  const client = initSupabase();
  if (!client) return null;

  const { data: { user }, error } = await client.auth.getUser();
  if (error) {
    console.error('ユーザー取得エラー:', error);
    return null;
  }
  return user;
}

/**
 * ログイン
 */
async function login(email, password) {
  const client = initSupabase();
  if (!client) {
    throw new Error('Supabaseクライアントが初期化されていません');
  }

  const { data, error } = await client.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw new Error(error.message);
  }

  return data;
}

/**
 * ログアウト
 */
async function logout() {
  const client = initSupabase();
  if (!client) return;

  const { error } = await client.auth.signOut();
  if (error) {
    console.error('ログアウトエラー:', error);
    throw new Error(error.message);
  }
}

/**
 * 認証トークンを取得
 */
async function getAuthToken() {
  const client = initSupabase();
  if (!client) return null;

  const { data: { session }, error } = await client.auth.getSession();
  if (error || !session) {
    return null;
  }

  return session.access_token;
}

/**
 * 認証状態をチェック
 */
async function checkAuth() {
  const user = await getCurrentUser();
  return user !== null;
}

/**
 * 認証が必要なページでリダイレクト
 */
async function requireAuth() {
  const isAuthenticated = await checkAuth();
  if (!isAuthenticated) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

/**
 * 管理者かどうかをチェック（簡易版）
 * 実際の実装では、APIから管理者情報を取得する必要がある
 */
async function isAdmin() {
  const user = await getCurrentUser();
  if (!user) return false;

  // 管理者メールアドレスのリスト（実際は環境変数やAPIから取得）
  const adminEmails = window.ADMIN_EMAILS ? window.ADMIN_EMAILS.split(',') : [];
  return adminEmails.includes(user.email);
}

/**
 * APIリクエスト用のヘッダーを取得
 */
async function getAuthHeaders() {
  const token = await getAuthToken();
  if (!token) {
    throw new Error('認証トークンが取得できませんでした');
  }

  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

