"use client";

import { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';


const supabase = createClient(supabaseUrl, supabaseAnonKey);

interface Post {
    id: number;
    instagram_shortcode: string;
    category: string;
    status: string;
    created_at: string;
    content: string;
    details: any;
}

interface LogSummary {
    totalFetched: number;
    duplicateSkipped: number;
    oldSkipped: number;
    newPosts: number;
    categories: { [key: string]: number };
    status: 'idle' | 'running' | 'success' | 'error' | 'no_data';
    message: string;
}

export default function ScraperAdmin() {
    const [loading, setLoading] = useState(false);
    const [logs, setLogs] = useState<string>('');
    const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
    const [country, setCountry] = useState<string>('Toronto');
    const [posts, setPosts] = useState<Post[]>([]);
    const [logSummary, setLogSummary] = useState<LogSummary | null>(null);

    // Filter settings
    const [daysFilter, setDaysFilter] = useState<number>(14);
    const [maxPosts, setMaxPosts] = useState<number>(10);
    const [skipDuplicates, setSkipDuplicates] = useState<boolean>(true);

    const [selectedPosts, setSelectedPosts] = useState<number[]>([]);

    useEffect(() => {
        fetchPosts();
    }, []);

    const fetchPosts = async () => {
        const _supabase = createClient(supabaseUrl, supabaseAnonKey);
        const { data, error } = await _supabase
            .from('posts')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(10);

        if (error) {
            console.error('Error fetching posts:', error);
        } else {
            setPosts(data || []);
            setSelectedPosts([]); // Reset selection on fetch
        }
    };

    const toggleSelectPost = (id: number) => {
        setSelectedPosts(prev =>
            prev.includes(id) ? prev.filter(pId => pId !== id) : [...prev, id]
        );
    };

    const deleteSelectedPosts = async () => {
        if (selectedPosts.length === 0) {
            alert('削除する項目を選択してください');
            return;
        }
        if (!confirm(`${selectedPosts.length}件のデータを削除しますか？`)) return;

        setLoading(true);
        const _supabase = createClient(supabaseUrl, supabaseAnonKey);

        const { error } = await _supabase
            .from('posts')
            .delete()
            .in('id', selectedPosts);

        if (error) {
            alert('削除に失敗しました: ' + error.message);
        } else {
            // Refetch to ensure data consistency
            await fetchPosts();
        }
        setLoading(false);
    };

    // 全データ削除
    const deleteAllPosts = async () => {
        if (!confirm('⚠️ 全ての投稿データを削除しますか？\n\nこの操作は取り消せません。')) return;
        if (!confirm('本当に削除しますか？\n\n「OK」を押すと全データが削除されます。')) return;

        setLoading(true);
        const _supabase = createClient(supabaseUrl, supabaseAnonKey);

        // Delete all posts by using neq with a condition that matches all
        const { error } = await _supabase
            .from('posts')
            .delete()
            .neq('id', 0); // This matches all rows since id is always > 0

        if (error) {
            alert('削除に失敗しました: ' + error.message);
        } else {
            setPosts([]);
            setSelectedPosts([]);
            alert('全データを削除しました');
        }
        setLoading(false);
    };

    // 全選択/全解除
    const toggleSelectAll = () => {
        if (selectedPosts.length === posts.length) {
            setSelectedPosts([]);
        } else {
            setSelectedPosts(posts.map(p => p.id));
        }
    };

    // Parse log output to extract summary
    const parseLogOutput = (output: string): LogSummary => {
        const summary: LogSummary = {
            totalFetched: 0,
            duplicateSkipped: 0,
            oldSkipped: 0,
            newPosts: 0,
            categories: {},
            status: 'success',
            message: ''
        };

        // Parse numbers from log
        const fetchedMatch = output.match(/Filtering (\d+) raw posts/);
        if (fetchedMatch) summary.totalFetched = parseInt(fetchedMatch[1]);

        const dupMatch = output.match(/Skipped (\d+) duplicate/);
        if (dupMatch) summary.duplicateSkipped = parseInt(dupMatch[1]);

        const oldMatch = output.match(/Skipped (\d+) old posts/);
        if (oldMatch) summary.oldSkipped = parseInt(oldMatch[1]);

        const retainedMatch = output.match(/Retained (\d+) new posts/);
        if (retainedMatch) summary.newPosts = parseInt(retainedMatch[1]);

        // Parse categories
        const catMatch = output.match(/Category breakdown: ({[^}]+})/);
        if (catMatch) {
            try {
                summary.categories = JSON.parse(catMatch[1].replace(/'/g, '"'));
            } catch { }
        }

        // Check for no data
        if (output.includes('No posts found to process')) {
            summary.status = 'no_data';
            summary.message = '処理可能な新しい投稿がありませんでした';
        } else if (output.includes('=== Done ===')) {
            summary.status = 'success';
            summary.message = 'スクレイピング完了';
        }

        return summary;
    };

    const startScraping = async () => {
        setLoading(true);
        setStatus('running');
        setLogs('');
        setLogSummary(null);

        try {
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    country,
                    daysFilter,
                    maxPosts,
                    skipDuplicates
                }),
            });

            const data = await response.json();

            if (data.success) {
                setStatus('success');
                setLogs(data.output || '');

                // Parse and set summary
                const summary = parseLogOutput(data.output || '');
                setLogSummary(summary);

                // Refresh posts after scraping
                fetchPosts();
            } else {
                setStatus('error');
                setLogs(data.error || 'Unknown error');
                setLogSummary({
                    totalFetched: 0, duplicateSkipped: 0, oldSkipped: 0, newPosts: 0,
                    categories: {}, status: 'error', message: data.error || 'エラーが発生しました'
                });
            }

        } catch (error: any) {
            setStatus('error');
            setLogs(error.message);
            setLogSummary({
                totalFetched: 0, duplicateSkipped: 0, oldSkipped: 0, newPosts: 0,
                categories: {}, status: 'error', message: 'ネットワークエラー: ' + error.message
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
            <h1>World Info Scraping</h1>

            <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>対象国:</label>
                <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    style={{ width: '100%', padding: '10px', fontSize: '16px', marginBottom: '20px' }}
                >
                    <option value="Toronto">Toronto (Canada)</option>
                    <option value="Thailand">Thailand</option>
                    <option value="Philippines">Philippines</option>
                    <option value="UK">United Kingdom</option>
                    <option value="Australia">Australia</option>
                </select>
            </div>

            {/* Filter Settings */}
            <div style={{
                marginBottom: '1.5rem',
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
            }}>
                <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#495057' }}>フィルター設定</h4>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#666' }}>
                            📅 対象期間（日）
                        </label>
                        <input
                            type="number"
                            min="1"
                            max="365"
                            value={daysFilter}
                            onChange={(e) => setDaysFilter(parseInt(e.target.value) || 14)}
                            style={{ width: '100%', padding: '8px', fontSize: '14px', borderRadius: '4px', border: '1px solid #ced4da' }}
                        />
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#666' }}>
                            📊 取得上限
                        </label>
                        <input
                            type="number"
                            min="1"
                            max="50"
                            value={maxPosts}
                            onChange={(e) => setMaxPosts(parseInt(e.target.value) || 10)}
                            style={{ width: '100%', padding: '8px', fontSize: '14px', borderRadius: '4px', border: '1px solid #ced4da' }}
                        />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', paddingTop: '20px' }}>
                        <input
                            type="checkbox"
                            id="skipDuplicates"
                            checked={skipDuplicates}
                            onChange={(e) => setSkipDuplicates(e.target.checked)}
                            style={{ marginRight: '8px', width: '18px', height: '18px' }}
                        />
                        <label htmlFor="skipDuplicates" style={{ fontSize: '14px', color: '#666' }}>
                            🔄 重複スキップ
                        </label>
                    </div>
                </div>
            </div>

            <button
                onClick={startScraping}
                disabled={loading}
                style={{
                    padding: '10px 20px',
                    fontSize: '16px',
                    backgroundColor: loading ? '#ccc' : '#0070f3',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: loading ? 'not-allowed' : 'pointer'
                }}
            >
                {loading ? 'スクレイピング実行中...' : 'スクレイピング開始'}
            </button>

            {logSummary && (
                <div style={{ marginTop: '20px', marginBottom: '40px' }}>
                    {/* Status Banner */}
                    <div style={{
                        padding: '15px 20px',
                        borderRadius: '8px',
                        marginBottom: '20px',
                        backgroundColor: logSummary.status === 'success' ? '#d4edda' :
                            logSummary.status === 'no_data' ? '#fff3cd' :
                                logSummary.status === 'error' ? '#f8d7da' : '#e2e3e5',
                        color: logSummary.status === 'success' ? '#155724' :
                            logSummary.status === 'no_data' ? '#856404' :
                                logSummary.status === 'error' ? '#721c24' : '#383d41',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px'
                    }}>
                        <span style={{ fontSize: '24px' }}>
                            {logSummary.status === 'success' ? '✅' :
                                logSummary.status === 'no_data' ? '⚠️' :
                                    logSummary.status === 'error' ? '❌' : '⏳'}
                        </span>
                        <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                            {logSummary.message || 'スクレイピング完了'}
                        </span>
                    </div>

                    {/* Stats Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '20px' }}>
                        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
                            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0070f3' }}>{logSummary.totalFetched}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>取得投稿数</div>
                        </div>
                        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
                            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#6c757d' }}>{logSummary.duplicateSkipped}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>重複スキップ</div>
                        </div>
                        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
                            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#fd7e14' }}>{logSummary.oldSkipped}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>古い投稿</div>
                        </div>
                        <div style={{ padding: '15px', backgroundColor: '#e7f5ff', borderRadius: '8px', textAlign: 'center' }}>
                            <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0070f3' }}>{logSummary.newPosts}</div>
                            <div style={{ fontSize: '12px', color: '#666' }}>新規処理</div>
                        </div>
                    </div>

                    {/* Category Breakdown */}
                    {Object.keys(logSummary.categories).length > 0 && (
                        <div style={{ marginBottom: '20px' }}>
                            <h4 style={{ marginBottom: '10px' }}>カテゴリ内訳</h4>
                            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                {logSummary.categories.Job !== undefined && (
                                    <span style={{ padding: '8px 16px', backgroundColor: '#28a745', color: 'white', borderRadius: '20px', fontSize: '14px' }}>
                                        💼 Job: {logSummary.categories.Job}
                                    </span>
                                )}
                                {logSummary.categories.House !== undefined && (
                                    <span style={{ padding: '8px 16px', backgroundColor: '#17a2b8', color: 'white', borderRadius: '20px', fontSize: '14px' }}>
                                        🏠 House: {logSummary.categories.House}
                                    </span>
                                )}
                                {logSummary.categories.Event !== undefined && (
                                    <span style={{ padding: '8px 16px', backgroundColor: '#6f42c1', color: 'white', borderRadius: '20px', fontSize: '14px' }}>
                                        🎉 Event: {logSummary.categories.Event}
                                    </span>
                                )}
                                {logSummary.categories.Ignore !== undefined && (
                                    <span style={{ padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', borderRadius: '20px', fontSize: '14px' }}>
                                        🚫 Ignore: {logSummary.categories.Ignore}
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Collapsible Raw Log */}
                    <details style={{ marginTop: '10px' }}>
                        <summary style={{ cursor: 'pointer', color: '#666', fontSize: '14px' }}>詳細ログを表示</summary>
                        <pre style={{
                            backgroundColor: '#f4f4f4',
                            padding: '15px',
                            borderRadius: '5px',
                            overflowX: 'auto',
                            maxHeight: '200px',
                            whiteSpace: 'pre-wrap',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            marginTop: '10px'
                        }}>
                            {logs}
                        </pre>
                    </details>
                </div>
            )}

            <div style={{ marginTop: '40px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                    <h3>取得済みデータ (最新10件)</h3>
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        {selectedPosts.length > 0 && (
                            <button
                                onClick={deleteSelectedPosts}
                                disabled={loading}
                                style={{
                                    padding: '8px 16px',
                                    backgroundColor: '#ff4d4f',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '5px',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                🗑️ 選択削除 ({selectedPosts.length})
                            </button>
                        )}
                        <button
                            onClick={deleteAllPosts}
                            disabled={loading || posts.length === 0}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: posts.length === 0 ? '#ccc' : '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '5px',
                                cursor: (loading || posts.length === 0) ? 'not-allowed' : 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            ⚠️ 全データ削除
                        </button>
                        <button
                            onClick={fetchPosts}
                            style={{
                                padding: '8px 16px',
                                cursor: 'pointer',
                                backgroundColor: '#f8f9fa',
                                border: '1px solid #ddd',
                                borderRadius: '5px',
                                fontSize: '14px'
                            }}
                        >
                            🔄 更新
                        </button>
                    </div>
                </div>

                {posts.length === 0 ? (
                    <p>データがありません。</p>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                            <thead>
                                <tr style={{ backgroundColor: '#f0f0f0' }}>
                                    <th style={{ padding: '10px', border: '1px solid #ddd' }}>ID</th>
                                    <th style={{ padding: '10px', border: '1px solid #ddd' }}>カテゴリ</th>
                                    <th style={{ padding: '10px', border: '1px solid #ddd' }}>ステータス</th>
                                    <th style={{ padding: '10px', border: '1px solid #ddd' }}>内容</th>
                                    <th style={{ padding: '10px', border: '1px solid #ddd' }}>作成日時</th>
                                    <th style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>
                                        <input
                                            type="checkbox"
                                            checked={posts.length > 0 && selectedPosts.length === posts.length}
                                            onChange={toggleSelectAll}
                                            style={{ transform: 'scale(1.5)', cursor: 'pointer' }}
                                            title="全選択/全解除"
                                        />
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {posts.map((post) => (
                                    <tr key={post.id}>
                                        <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                                            <a href={`https://instagram.com/p/${post.instagram_shortcode}`} target="_blank" rel="noopener noreferrer">
                                                {post.instagram_shortcode}
                                            </a>
                                        </td>
                                        <td style={{ padding: '10px', border: '1px solid #ddd' }}>{post.category}</td>
                                        <td style={{ padding: '10px', border: '1px solid #ddd' }}>{post.status}</td>
                                        <td style={{ padding: '10px', border: '1px solid #ddd', fontSize: '0.9em' }}>
                                            {post.content || post.details?.rewritten_text || 'No description'}
                                        </td>
                                        <td style={{ padding: '10px', border: '1px solid #ddd', fontSize: '0.8em' }}>
                                            {new Date(post.created_at).toLocaleString('ja-JP')}
                                        </td>
                                        <td style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>
                                            <input
                                                type="checkbox"
                                                checked={selectedPosts.includes(post.id)}
                                                onChange={() => toggleSelectPost(post.id)}
                                                style={{ transform: 'scale(1.5)', cursor: 'pointer' }}
                                            />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
