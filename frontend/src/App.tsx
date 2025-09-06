import React, { useState, useEffect, useRef } from 'react';
import './styles/index.css';
import { getContentItems, updateContentStatus, updateContentText, testBackendConnection, rephraseContent, approveAndPost, ContentItem } from './utils/backendApi';

// TypeScript interfaces
interface Author {
    name: string;
    title?: string;
    handle?: string;
    avatar: string;
}

interface Post {
    id: string;
    platform: 'LinkedIn' | 'X' | 'Email' | 'TikTok';
    author: Author;
    content: string;
    status: 'pending' | 'approved' | 'disapproved' | 'posted';
    media: Array<{
        url: string;
        type: 'image' | 'video';
        caption?: string;
    }>;
    repository?: string;
    commit_sha?: string;
    branch?: string;
}

interface PushHistory {
    id: string;
    posts: Post[];
}

// Convert ContentItem to Post format for UI compatibility
const convertContentItemToPost = (item: ContentItem): Post => ({
    id: item._id,
    platform: item.platform || 'LinkedIn',
    author: item.author || { 
        name: 'System', 
        avatar: 'https://placehold.co/100x100/667eea/ffffff?text=SYS' 
    },
    content: item.content,
    status: item.status === 'pending_validation' ? 'pending' : 
           item.status === 'approved' ? 'approved' : 
           item.status === 'rejected' ? 'disapproved' : 'posted',
    media: item.media || [],
    repository: item.repository,
    commit_sha: item.commit_sha,
    branch: item.branch
});

const App: React.FC = () => {
    const [posts, setPosts] = useState<Post[]>([]);
    const [postHistory, setPostHistory] = useState<PushHistory[]>([]);
    const [currentPushId, setCurrentPushId] = useState<string | null>(null);
    const [tone, setTone] = useState<number>(50);
    const [notification, setNotification] = useState<string>('');
    const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<{ [key: string]: boolean }>({});
    const [backendConnected, setBackendConnected] = useState<boolean>(false);

    const messageTimeoutRef = useRef<number | null>(null);

    // Initialize app - load content from backend
    useEffect(() => {
        const loadContentFromBackend = async () => {
            try {
                const isBackendAvailable = await testBackendConnection();
                setBackendConnected(isBackendAvailable);
                
                const contentItems = await getContentItems();
                
                // Convert backend content to posts
                const backendPosts = contentItems.map(convertContentItemToPost);
                
                // Group posts by repository/branch for history
                const groupedPosts = backendPosts.reduce((acc, post) => {
                    const key = `${post.repository || 'unknown'}-${post.branch || 'main'}`;
                    if (!acc[key]) {
                        acc[key] = [];
                    }
                    acc[key].push(post);
                    return acc;
                }, {} as Record<string, Post[]>);

                // Create push history from grouped posts
                const newPushes: PushHistory[] = Object.entries(groupedPosts).map(([key, posts]) => ({
                    id: key,
                    posts
                }));

                setPostHistory(newPushes);
                
                if (!isBackendAvailable) {
                    showNotification("Backend unavailable - using mock data");
                }
            } catch (error) {
                console.error('Error loading content:', error);
                showNotification("Failed to load content from backend");
            }
        };

        loadContentFromBackend();
    }, []);

    // Load latest push
    useEffect(() => {
        if (postHistory.length > 0 && currentPushId === null) {
            const latestPush = postHistory[postHistory.length - 1];
            loadPush(latestPush.id);
        }
    }, [postHistory, currentPushId]);

    const loadPush = (pushId: string) => {
        const push = postHistory.find(p => p.id === pushId);
        if (push) {
            setPosts(push.posts);
            setCurrentPushId(pushId);
            if (window.innerWidth < 1024) {
                setIsSidebarOpen(false);
            }
        }
    };

    const showNotification = (msg: string) => {
        if (messageTimeoutRef.current) {
            clearTimeout(messageTimeoutRef.current);
        }
        setNotification(msg);
        messageTimeoutRef.current = window.setTimeout(() => {
            setNotification('');
        }, 3000);
    };

    const handleApprove = async (id: string) => {
        try {
            if (backendConnected) {
                await approveAndPost(id);
            }
            const updatedPosts = posts.map(p => p.id === id ? { ...p, status: 'posted' as const } : p);
            setPosts(updatedPosts);
            showNotification(`Post for ${posts.find(p => p.id === id)?.platform} Approved & Posted! ✅`);
        } catch (error) {
            console.error('Error approving and posting:', error);
            showNotification('Failed to approve and post content');
        }
    };

    const handleDisapprove = async (id: string) => {
        try {
            if (backendConnected) {
                await updateContentStatus(id, 'rejected');
            }
            const updatedPosts = posts.map(p => p.id === id ? { ...p, status: 'disapproved' as const } : p);
            setPosts(updatedPosts);
            showNotification(`Post for ${posts.find(p => p.id === id)?.platform} Disapproved ❌`);
        } catch (error) {
            console.error('Error disapproving post:', error);
            showNotification('Failed to disapprove post');
        }
    };

    const handleContentChange = async (event: React.ChangeEvent<HTMLTextAreaElement>, id: string) => {
        const { value } = event.target;
        
        // Update UI immediately
        setPosts(prevPosts =>
            prevPosts.map(p =>
                p.id === id ? { ...p, content: value } : p
            )
        );

        // Backend update if connected
        if (backendConnected) {
            try {
                await updateContentText(id, value);
            } catch (error) {
                console.error('Error updating content:', error);
            }
        }
    };


    const rephrasePost = async (id: string) => {
        const post = posts.find(p => p.id === id);
        if (!post) return;

        setIsLoading(prev => ({ ...prev, [id]: true }));
        const originalContent = post.content;
        setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: 'Rephrasing with AI... ✨' } : p));

        try {
            if (backendConnected) {
                const newContent = await rephraseContent(id, tone);
                setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: newContent } : p));
                showNotification("Post rephrased successfully! ✨");
            } else {
                // Fallback to direct MCP call if backend not available
                const { rephraseWithMCP } = await import('./utils/mcpApi');
                const newContent = await rephraseWithMCP(originalContent, tone);
                setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: newContent } : p));
                
                if (backendConnected) {
                    await updateContentText(id, newContent);
                }
                showNotification("Post rephrased successfully! ✨");
            }
        } catch (error) {
            console.error('Error rephrasing post:', error);
            setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: originalContent } : p));
            showNotification("Rephrasing failed - using original content");
        } finally {
            setIsLoading(prev => ({ ...prev, [id]: false }));
        }
    };

    const readAloud = async (id: string) => {
        const post = posts.find(p => p.id === id);
        if (!post) return;

        try {
            const { generateTTSWithMCP } = await import('./utils/mcpApi');
            const audioUrl = await generateTTSWithMCP(post.content);
            const audio = new Audio(audioUrl);
            audio.play();
            showNotification("Playing audio... 🎧");
        } catch (error) {
            console.error('Error generating TTS:', error);
            showNotification("TTS not available - check backend connection 🎧");
        }
    };

    const renderMedia = (post: Post) => {
        if (post.media.length === 0) {
            return (
                <div className="w-full h-48 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center">
                    <div className="text-gray-400 text-center">
                        <div className="text-4xl mb-2">📄</div>
                        <div className="font-medium">No Media</div>
                    </div>
                </div>
            );
        }

        if (post.media.length === 1) {
            const media = post.media[0];
            return (
                <div className="relative">
                    {media.type === 'image' ? (
                        <img src={media.url} alt={media.caption || "Post Media"} className="w-full h-48 object-cover rounded-2xl" />
                    ) : (
                        <video src={media.url} className="w-full h-48 object-cover rounded-2xl" controls muted loop></video>
                    )}
                    {media.caption && (
                        <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded-lg">
                            {media.caption}
                        </div>
                    )}
                </div>
            );
        }

        // Multiple media items - show as carousel/grid
        return (
            <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                    {post.media.slice(0, 4).map((media, index) => (
                        <div key={index} className="relative">
                            {media.type === 'image' ? (
                                <img src={media.url} alt={media.caption || `Media ${index + 1}`} className="w-full h-24 object-cover rounded-xl" />
                            ) : (
                                <video src={media.url} className="w-full h-24 object-cover rounded-xl" muted></video>
                            )}
                            {media.caption && (
                                <div className="absolute bottom-1 left-1 bg-black/70 text-white text-xs px-1 py-0.5 rounded">
                                    {media.caption}
                                </div>
                            )}
                            {index === 3 && post.media.length > 4 && (
                                <div className="absolute inset-0 bg-black/50 rounded-xl flex items-center justify-center text-white font-bold">
                                    +{post.media.length - 4}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
                <div className="text-xs text-white/70 text-center">
                    {post.media.length} media items from database
                </div>
            </div>
        );
    };

    const getPlatformGradient = (platform: string) => {
        switch (platform) {
            case 'LinkedIn': return 'from-blue-500 to-blue-700';
            case 'X': return 'from-gray-800 to-black';
            case 'Email': return 'from-green-500 to-green-700';
            case 'TikTok': return 'from-pink-500 to-red-500';
            default: return 'from-purple-500 to-purple-700';
        }
    };

    return (
        <div className="flex min-h-screen relative">
            {/* Mobile Overlay */}
            <div 
                className={`overlay ${isSidebarOpen ? 'visible' : ''} lg:hidden`}
                onClick={() => setIsSidebarOpen(false)}
            />

            {/* Glassmorphism Sidebar */}
            <nav className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
                <div className="floating">
                    <h2 className="text-3xl font-bold mb-8 text-white bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
                        Content History
                    </h2>
                    <div className={`text-xs px-3 py-1 rounded-full mb-4 ${backendConnected ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                        {backendConnected ? '🟢 Backend Connected' : '🔴 Mock Data'}
                    </div>
                </div>
                <ul className="flex-grow overflow-y-auto space-y-3">
                    {postHistory.map(push => (
                        <li
                            key={push.id}
                            className={`sidebar-item cursor-pointer ${push.id === currentPushId ? 'active' : ''}`}
                            onClick={() => loadPush(push.id)}
                        >
                            <div className="font-semibold">{push.id.split('-')[0]}</div>
                            <div className="text-sm opacity-75">{push.posts.length} posts • {push.id.split('-')[1] || 'main'}</div>
                        </li>
                    ))}
                </ul>

            </nav>

            {/* Main Content */}
            <div className="flex-1 flex flex-col lg:ml-0">
                {/* Modern Header */}
                <header className="relative p-8 text-center">
                    <button
                        className="lg:hidden fixed top-6 left-6 z-[60] p-3 modern-button bg-white/20 backdrop-blur-lg rounded-2xl shadow-lg border border-white/30"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    >
                        <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
                        </svg>
                    </button>

                    <div className="floating">
                        <h1 className="text-6xl font-bold text-white mb-4 bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
                            AI Content Manager
                        </h1>
                        <p className="text-xl text-white/80 font-medium max-w-2xl mx-auto">
                            Review and manage AI-generated social media content from your repositories
                        </p>
                    </div>

                    {/* Tone Control */}
                    <div className="mt-8 max-w-md mx-auto">
                        <div className="backdrop-filter backdrop-blur-lg bg-white/10 rounded-3xl p-6 border border-white/20">
                            <label className="block text-white font-semibold mb-3">Content Tone</label>
                            <div className="knob-container">
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={tone}
                                    onChange={(e) => setTone(Number(e.target.value))}
                                    className="w-full"
                                />
                            </div>
                            <div className="flex justify-between text-sm text-white/70 mt-2">
                                <span>Professional</span>
                                <span>Casual</span>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Posts Grid */}
                <main className="flex-1 p-8 overflow-y-auto">
                    <div className="max-w-7xl mx-auto">
                        {posts.length === 0 ? (
                            <div className="text-center py-20">
                                <div className="floating">
                                    <div className="text-8xl mb-6">📱</div>
                                    <h3 className="text-3xl font-bold text-white mb-4">No content yet</h3>
                                    <p className="text-white/70 text-xl">Generate new content or select a repository from the sidebar!</p>
                                </div>
                            </div>
                        ) : (
                            <div className="grid gap-8 md:grid-cols-2 xl:grid-cols-3">
                                {posts.map((post, index) => (
                                    <div 
                                        key={post.id} 
                                        className="post-card-container rounded-3xl p-8 transform transition-all duration-500"
                                        style={{ animationDelay: `${index * 0.1}s` }}
                                    >
                                        {/* Platform Header */}
                                        <div className={`bg-gradient-to-r ${getPlatformGradient(post.platform)} rounded-2xl p-4 mb-6 text-white`}>
                                            <div className="flex items-center justify-between">
                                                <h3 className="text-xl font-bold">{post.platform}</h3>
                                                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                                    post.status === 'approved' ? 'bg-green-500' :
                                                    post.status === 'disapproved' ? 'bg-red-500' :
                                                    'bg-yellow-500'
                                                }`}>
                                                    {post.status.toUpperCase()}
                                                </div>
                                            </div>
                                            <div className="flex items-center mt-2">
                                                <img src={post.author.avatar} alt={post.author.name} className="h-8 w-8 rounded-full mr-3" />
                                                <div>
                                                    <div className="font-semibold text-sm">{post.author.name}</div>
                                                    {post.author.title && <div className="text-xs opacity-75">{post.author.title}</div>}
                                                </div>
                                            </div>
                                            {/* Repository Info */}
                                            {post.repository && (
                                                <div className="mt-2 text-xs opacity-75">
                                                    📦 {post.repository} • {post.branch} • {post.commit_sha?.slice(0, 7)}
                                                </div>
                                            )}
                                        </div>

                                        {/* Media from Database */}
                                        <div className="mb-6">
                                            {renderMedia(post)}
                                        </div>

                                        {/* Content */}
                                        <textarea
                                            value={post.content}
                                            onChange={(e) => handleContentChange(e, post.id)}
                                            disabled={post.status !== 'pending'}
                                            className="w-full h-32 rounded-2xl border-0 bg-white/20 backdrop-blur-lg p-4 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30 transition-all resize-none"
                                            placeholder="AI-generated content..."
                                        />

                                        {/* AI Actions */}
                                        <div className="mt-6 flex gap-3">
                                            <button
                                                onClick={() => rephrasePost(post.id)}
                                                disabled={post.status !== 'pending' || isLoading[post.id]}
                                                className="modern-button flex-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold py-3 px-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                {isLoading[post.id] ? (
                                                    <div className="loading-spinner mx-auto"></div>
                                                ) : (
                                                    <>✨ Rephrase</>
                                                )}
                                            </button>
                                            <button
                                                onClick={() => readAloud(post.id)}
                                                disabled={post.status !== 'pending'}
                                                className="modern-button bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold py-3 px-6 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                🎧
                                            </button>
                                        </div>

                                        {/* Approval Actions */}
                                        <div className="mt-4 flex gap-3">
                                            <button
                                                onClick={() => handleApprove(post.id)}
                                                disabled={post.status !== 'pending'}
                                                className="modern-button flex-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold py-3 px-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                ✅ Approve
                                            </button>
                                            <button
                                                onClick={() => handleDisapprove(post.id)}
                                                disabled={post.status !== 'pending'}
                                                className="modern-button flex-1 bg-gradient-to-r from-red-500 to-pink-500 text-white font-semibold py-3 px-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                ❌ Reject
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </main>
            </div>

            {/* Notification */}
            <div className={`message-box ${notification ? 'show' : ''}`}>
                {notification}
            </div>
        </div>
    );
};

export default App;
