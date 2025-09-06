import React from 'react';
import { Post } from '../types';

interface PostCardProps {
    post: Post;
    onApprove: (id: string) => void;
    onDisapprove: (id: string) => void;
    onRephrase: (id: string) => void;
    onReadAloud: (id: string) => void;
    onContentChange: (event: React.ChangeEvent<HTMLTextAreaElement>, id: string) => void;
}

const PostCard: React.FC<PostCardProps> = ({
    post,
    onApprove,
    onDisapprove,
    onRephrase,
    onReadAloud,
    onContentChange
}) => {
    // Renders the media content based on post data
    const renderMedia = (post: Post) => {
        if (post.mediaType === 'image') {
            return <img src={post.mediaUrl} alt="Post Media" className="w-full h-auto object-cover" />;
        } else if (post.mediaType === 'video') {
            return <video src={post.mediaUrl} className="w-full h-auto object-cover" controls autoPlay muted loop></video>;
        }
        return <div className="bg-gray-200 h-48 flex items-center justify-center text-gray-400 font-medium">No Media</div>;
    };

    return (
        <div
            className={`post-card-container bg-white p-6 rounded-2xl shadow-md transition-all ease-in-out duration-300 transform ${post.status === 'approved' ? 'border-4 border-green-500' : post.status === 'disapproved' ? 'border-4 border-red-500 opacity-70' : ''}`}
        >
            <h3 className="text-xl font-bold mb-4 text-gray-700">{post.platform} Post</h3>
            <div className="flex items-center mb-4">
                <img src={post.author.avatar} alt={`${post.author.name}'s Avatar`} className="h-10 w-10 rounded-full mr-2" />
                <span className="font-bold text-gray-800">{post.author.name}</span>
            </div>

            {/* Media Section */}
            <div className="rounded-xl overflow-hidden mb-4">
                {renderMedia(post)}
            </div>

            <textarea
                value={post.content}
                onChange={(e) => onContentChange(e, post.id)}
                disabled={post.status !== 'pending'}
                className={`w-full h-40 rounded-lg border border-gray-200 bg-gray-50 p-4 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors`}
            />

            {/* LLM-powered Action Buttons */}
            <div className="mt-4 flex gap-2">
                <button
                    onClick={() => onRephrase(post.id)}
                    disabled={post.status !== 'pending'}
                    className="flex items-center justify-center px-4 py-2 rounded-full text-blue-600 font-medium bg-blue-100 hover:bg-blue-200 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Rephrase ✨
                </button>
                <button
                    onClick={() => onReadAloud(post.id)}
                    disabled={post.platform === 'TikTok' || post.status !== 'pending'}
                    className="flex items-center justify-center px-4 py-2 rounded-full text-purple-600 font-medium bg-purple-100 hover:bg-purple-200 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Read Aloud 🎧
                </button>
            </div>

            {/* Approval Action Buttons */}
            <div className="mt-6 flex gap-4">
                <button
                    onClick={() => onApprove(post.id)}
                    disabled={post.status !== 'pending'}
                    className="flex items-center justify-center px-4 py-2 rounded-full text-white font-medium bg-green-500 hover:bg-green-600 transition-colors shadow-md w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    Approve
                </button>
                <button
                    onClick={() => onDisapprove(post.id)}
                    disabled={post.status !== 'pending'}
                    className="flex items-center justify-center px-4 py-2 rounded-full text-white font-medium bg-red-500 hover:bg-red-600 transition-colors shadow-md w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                    Disapprove
                </button>
            </div>
        </div>
    );
};

export default PostCard;
