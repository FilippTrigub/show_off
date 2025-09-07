import React, { useState, useEffect, useRef } from 'react';
import './styles/index.css';
import { getContentItems, updateContentStatus, updateContentText, testBackendConnection, rephraseContent, approveAndPost, ContentItem } from './utils/backendApi';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import PostCard from './components/PostCard';
import { Post, PushHistory } from './types/shared';

// Convert ContentItem to Post format for UI compatibility
const convertContentItemToPost = (item: ContentItem): Post => ({
    id: item._id,
    platform: (item.platform as 'LinkedIn' | 'X' | 'Email' | 'TikTok') || 'LinkedIn',
    author: item.author || { 
        name: 'System', 
        avatar: 'https://placehold.co/100x100/667eea/ffffff?text=SYS' 
    },
    content: item.content || '',
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
                setBackendConnected(!!isBackendAvailable);
                
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
                console.error('Error loading content from backend:', error);
                setBackendConnected(false);
                showNotification("Error connecting to backend - using mock data");
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

    // Convert tone from 0-100 range to 0-1 range for backend
    const normalizedTone = tone / 100;

    const showNotification = (msg: string) => {
        if (messageTimeoutRef.current) {
            clearTimeout(messageTimeoutRef.current);
        }
        setNotification(msg);
        messageTimeoutRef.current = window.setTimeout(() => {
            setNotification('');
        }, 3000);
    };

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

    const updatePostStatus = async (postId: string, newStatus: Post['status']) => {
        try {
            // Update backend
            const backendStatus = newStatus === 'disapproved' ? 'rejected' : 
                                 newStatus === 'posted' ? 'published' : newStatus;
            await updateContentStatus(postId, backendStatus as any);
            
            // Update local state
            setPosts(prevPosts => 
                prevPosts.map(post => 
                    post.id === postId ? { ...post, status: newStatus } : post
                )
            );
            
            // Update post history
            setPostHistory(prevHistory => 
                prevHistory.map(pushHistory => ({
                    ...pushHistory,
                    posts: pushHistory.posts.map(post => 
                        post.id === postId ? { ...post, status: newStatus } : post
                    )
                }))
            );
            
            showNotification(`Post ${newStatus}`);
        } catch (error) {
            console.error('Error updating post status:', error);
            showNotification('Error updating post status');
        }
    };

    const rephrasePost = async (postId: string) => {
        setIsLoading(prev => ({ ...prev, [postId]: true }));
        try {
            if (backendConnected) {
                // Use backend rephraseContent API
                await rephraseContent(postId, normalizedTone);
                
                // Reload content to get updated text
                const contentItems = await getContentItems();
                const updatedPost = contentItems.find(item => item._id === postId);
                
                if (updatedPost) {
                    const convertedPost = convertContentItemToPost(updatedPost);
                    
                    // Update posts if it exists there
                    setPosts(prevPosts => 
                        prevPosts.map(post => 
                            post.id === postId ? convertedPost : post
                        )
                    );
                    
                    // Update post history
                    setPostHistory(prevHistory => 
                        prevHistory.map(pushHistory => ({
                            ...pushHistory,
                            posts: pushHistory.posts.map(post => 
                                post.id === postId ? convertedPost : post
                            )
                        }))
                    );
                }
                showNotification('Post rephrased successfully');
            } else {
                // Fallback to direct MCP call if backend is unavailable
                const { rephraseWithMCP } = await import('./utils/mcpApi');
                const currentPost = posts.find(p => p.id === postId);
                if (currentPost) {
                    const newContent = await rephraseWithMCP(currentPost.content, normalizedTone);
                    
                    // Update local state
                    setPosts(prevPosts => 
                        prevPosts.map(post => 
                            post.id === postId ? { ...post, content: newContent } : post
                        )
                    );
                    
                    // Update post history
                    setPostHistory(prevHistory => 
                        prevHistory.map(pushHistory => ({
                            ...pushHistory,
                            posts: pushHistory.posts.map(post => 
                                post.id === postId ? { ...post, content: newContent } : post
                            )
                        }))
                    );
                    
                    showNotification('Post rephrased successfully (via MCP fallback)');
                }
            }
        } catch (error) {
            console.error('Error rephrasing post:', error);
            showNotification('Error rephrasing post');
        } finally {
            setIsLoading(prev => ({ ...prev, [postId]: false }));
        }
    };

    const handleApprove = async (postId: string) => {
        try {
            // Use approveAndPost API instead of just status update
            await approveAndPost(postId);
            
            // Update local state to "posted" status
            setPosts(prevPosts => 
                prevPosts.map(post => 
                    post.id === postId ? { ...post, status: 'posted' } : post
                )
            );
            
            // Update post history
            setPostHistory(prevHistory => 
                prevHistory.map(pushHistory => ({
                    ...pushHistory,
                    posts: pushHistory.posts.map(post => 
                        post.id === postId ? { ...post, status: 'posted' } : post
                    )
                }))
            );
            
            showNotification('Approved & Posted! ✅');
        } catch (error) {
            console.error('Error approving and posting:', error);
            showNotification('Error approving and posting');
        }
    };

    const getCurrentPush = () => {
        return postHistory.find(p => p.id === currentPushId);
    };

    const currentPosts = getCurrentPush()?.posts || posts;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative">
            <Header 
                tone={tone}
                onToneChange={setTone}
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
            />
            
            <Sidebar 
                postHistory={postHistory}
                currentPushId={currentPushId}
                onLoadPush={loadPush}
                isOpen={isSidebarOpen}
                backendConnected={backendConnected}
                onOverlayClick={() => setIsSidebarOpen(false)}
            />

            {/* Main Content */}
            <main className="pt-20 px-4 pb-8">
                <div className="max-w-2xl mx-auto space-y-6">
                    {currentPosts.length > 0 ? (
                        currentPosts.map((post, index) => (
                            <PostCard 
                                key={post.id}
                                post={post}
                                index={index}
                                isLoading={isLoading[post.id] || false}
                                onContentChange={async (event: React.ChangeEvent<HTMLTextAreaElement>, id: string) => {
                                    const newContent = event.target.value;
                                    try {
                                        await updateContentText(id, newContent);
                                        setPosts(prevPosts => 
                                            prevPosts.map(p => 
                                                p.id === id ? { ...p, content: newContent } : p
                                            )
                                        );
                                    } catch (error) {
                                        console.error('Error updating content:', error);
                                    }
                                }}
                                onRephrase={(id: string) => rephrasePost(id)}
                                onApprove={(id: string) => handleApprove(id)}
                                onDisapprove={(id: string) => updatePostStatus(id, 'disapproved')}
                                onReadAloud={(_id: string) => {
                                    showNotification('Read aloud feature coming soon');
                                }}
                            />
                        ))
                    ) : (
                        <div className="text-center text-white/60 py-12">
                            <p>No content available. Check your backend connection.</p>
                        </div>
                    )}
                </div>
            </main>

            {/* Notification */}
            {notification && (
                <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50">
                    {notification}
                </div>
            )}
        </div>
    );
};

export default App;
