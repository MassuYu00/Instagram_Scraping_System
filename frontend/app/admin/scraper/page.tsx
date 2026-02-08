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
    analysis_result: any;
}

export default function ScraperAdmin() {
    const [loading, setLoading] = useState(false);
    const [logs, setLogs] = useState<string>('');
    const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');
    const [targets, setTargets] = useState<string>('');
    const [country, setCountry] = useState<string>('Toronto');
    const [posts, setPosts] = useState<Post[]>([]);

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
            // Optimistic update or refetch
            setPosts(prev => prev.filter(post => !selectedPosts.includes(post.id)));
            setSelectedPosts([]);
        }
        setLoading(false);
    };

    const startScraping = async () => {
        setLoading(true);
        setStatus('running');
        setLogs('Starting scraper...\n');

        try {
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ targets, country }),
            });

            const data = await response.json();

            if (data.success) {
                setStatus('success');
                setLogs((prev) => prev + "--- STDOUT ---\n" + data.output + "\n");
                if (data.error) {
                    setLogs((prev) => prev + "--- STDERR ---\n" + data.error + "\n");
                }
                // Refresh posts after scraping
                fetchPosts();
            } else {
                setStatus('error');
                setLogs((prev) => prev + "Error: " + data.error + "\n");
            }

        } catch (error: any) {
            setStatus('error');
            setLogs((prev) => prev + "Network/Server Error: " + error.message + "\n");
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

                <p>ターゲット（ハッシュタグまたはアカウント名）をカンマ区切りで入力してください。空欄の場合はデフォルト設定が使用されます。</p>
                <input
                    type="text"
                    placeholder="例: #torontojobs, @blogto"
                    value={targets}
                    onChange={(e) => setTargets(e.target.value)}
                    style={{ width: '100%', padding: '10px', fontSize: '16px', marginBottom: '10px' }}
                />
                <p><strong>デフォルト設定:</strong> #torontojobs, #torontorentals, @blogto, @torontolife</p>
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

            {status !== 'idle' && (
                <div style={{ marginTop: '20px', marginBottom: '40px' }}>
                    <h3>実行ログ:</h3>
                    <pre style={{
                        backgroundColor: '#f4f4f4',
                        padding: '15px',
                        borderRadius: '5px',
                        overflowX: 'auto',
                        maxHeight: '300px',
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace'
                    }}>
                        {logs}
                    </pre>
                </div>
            )}

            <div style={{ marginTop: '40px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3>取得済みデータ (最新10件)</h3>
                    <div>
                        {selectedPosts.length > 0 && (
                            <button
                                onClick={deleteSelectedPosts}
                                disabled={loading}
                                style={{
                                    marginRight: '10px',
                                    padding: '5px 15px',
                                    backgroundColor: '#ff4d4f',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '5px',
                                    cursor: 'pointer'
                                }}
                            >
                                選択した項目を削除 ({selectedPosts.length})
                            </button>
                        )}
                        <button
                            onClick={fetchPosts}
                            style={{ padding: '5px 10px', cursor: 'pointer' }}
                        >
                            データを更新
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
                                    <th style={{ padding: '10px', border: '1px solid #ddd', textAlign: 'center' }}>削除</th>
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
                                            {post.analysis_result?.data?.rewritten_text || 'No description'}
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
