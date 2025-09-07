import React from 'react';
import { Post } from '../types/shared';

interface PostCardProps {
    post: Post;
    index: number;
    isLoading: boolean;
    onApprove: (id: string) => void;
    onDisapprove: (id: string) => void;
    onRephrase: (id: string) => void;
    onReadAloud: (id: string) => void;
    onContentChange: (event: React.ChangeEvent<HTMLTextAreaElement>, id: string) => void;
}

const PostCard: React.FC<PostCardProps> = ({
    post,
    index,
    isLoading,
    onApprove,
    onDisapprove,
    onRephrase,
    onReadAloud,
    onContentChange
}) => {
    const getPlatformGradient = (platform: string) => {
        switch (platform) {
            case 'LinkedIn': return 'from-blue-500 to-blue-700';
            case 'X': return 'from-gray-800 to-black';
            case 'Email': return 'from-green-500 to-green-700';
            case 'TikTok': return 'from-pink-500 to-red-500';
            default: return 'from-purple-500 to-purple-700';
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

    return (
        <div 
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
                onChange={(e) => onContentChange(e, post.id)}
                disabled={post.status !== 'pending'}
                className="w-full h-32 rounded-2xl border-0 bg-white/20 backdrop-blur-lg p-4 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/30 transition-all resize-none"
                placeholder="AI-generated content..."
            />

            {/* AI Actions */}
            <div className="mt-6 flex gap-3">
                <button
                    onClick={() => onRephrase(post.id)}
                    disabled={post.status !== 'pending' || isLoading}
                    className="modern-button flex-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold py-3 px-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isLoading ? (
                        <div className="loading-spinner mx-auto"></div>
                    ) : (
                        <>✨ Rephrase</>
                    )}
                </button>
                <button
                    onClick={() => onReadAloud(post.id)}
                    disabled={post.status !== 'pending'}
                    className="modern-button bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold py-3 px-6 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    🎧
                </button>
            </div>

            {/* Approval Actions */}
            <div className="mt-4 flex gap-3">
                <button
                    onClick={() => onApprove(post.id)}
                    disabled={post.status !== 'pending'}
                    className="modern-button flex-1 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold py-3 px-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    ✅ Approve
                </button>
                <button
                    onClick={() => onDisapprove(post.id)}
                    disabled={post.status !== 'pending'}
                    className="modern-button flex-1 bg-gradient-to-r from-red-500 to-pink-500 text-white font-semibold py-3 px-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    ❌ Reject
                </button>
            </div>
        </div>
    );
};

export default PostCard;
