import { Post, PushHistory } from '../types';

// Mock data for social media posts
export const mockPosts: Omit<Post, 'id'>[] = [
    {
        platform: 'LinkedIn',
        author: { name: 'Alex Johnson', title: 'Senior Software Engineer', avatar: 'https://placehold.co/100x100/A0B9E5/1D4ED8?text=AJ' },
        content: `🚀 Thrilled to announce a new project launch! Our team has been working on a groundbreaking new feature that will streamline developer workflows and enhance collaboration. So excited to see how this impacts the community! #tech #softwaredevelopment #innovation`,
        status: 'pending',
        mediaUrl: 'https://placehold.co/600x400/D1E0E0/6B7280?text=Placeholder+Image',
        mediaType: 'image',
    },
    {
        platform: 'X',
        author: { name: 'CodeGenBot', handle: '@codegenbot', avatar: 'https://placehold.co/100x100/FCA5A5/DC2626?text=CB' },
        content: `Just got a fresh code push from a dev! My algorithms say this is a huge step forward for the project. Let's see what happens next! 🤖 #ai #programming #github`,
        status: 'pending',
        mediaUrl: 'https://placehold.co/600x400/C1C1E0/6B7280?text=Placeholder+Image',
        mediaType: 'image',
    },
    {
        platform: 'Email',
        author: { name: 'Marketing Dept', handle: 'marketing@company.com', avatar: 'https://placehold.co/100x100/9CA3AF/374151?text=MD' },
        content: `Subject: Important Update on Q4 Initiatives

Hi Team,

I'm writing to share a brief update on the progress of our Q4 initiatives. Please review the attached document for detailed insights and feel free to reach out with any questions.

Best regards,
Marketing Team`,
        status: 'pending',
        mediaUrl: '',
        mediaType: 'none',
    },
    {
        platform: 'TikTok',
        author: { name: 'DevLounge', handle: '@devlounge', avatar: 'https://placehold.co/100x100/93C5FD/1D4ED8?text=DL' },
        content: `🔥 This is how we roll at DevLounge! Brainstorming sessions that are as fun as they are productive. Love the energy and the creative ideas everyone is bringing to the table! #office #worklife #teamwork`,
        status: 'pending',
        mediaUrl: 'https://placehold.co/600x800/93C5FD/1D4ED8?text=Placeholder+Video',
        mediaType: 'video',
    },
];

// Utility function to generate mock push history
export const generateMockPushHistory = (): PushHistory[] => {
    const today = new Date();
    const newPushes: PushHistory[] = [];

    // Generate 5 mock pushes with unique IDs and slightly varied content
    for (let i = 4; i >= 0; i--) {
        const pushId = `push-${(today.getTime() - i * 86400000).toString(16).slice(-8)}`; // Unique ID based on date
        const newPosts: Post[] = JSON.parse(JSON.stringify(mockPosts)).map((post: Omit<Post, 'id'>) => ({
            ...post,
            id: `${post.platform.toLowerCase()}-${pushId}`,
            content: post.content.includes("new project launch") ? `[${pushId}] Announcing our latest milestone! Our team just wrapped up a project that will change the game. #productlaunch #development` : post.content,
        }));
        newPushes.push({ id: pushId, posts: newPosts });
    }

    return newPushes;
};
