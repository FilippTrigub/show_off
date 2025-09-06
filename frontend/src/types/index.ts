// TypeScript interfaces for data structures
export interface Author {
    name: string;
    title?: string;
    handle?: string;
    avatar: string;
}

export interface Post {
    id: string;
    platform: 'LinkedIn' | 'X' | 'Email' | 'TikTok';
    author: Author;
    content: string;
    status: 'pending' | 'approved' | 'disapproved' | 'posted';
    mediaUrl: string;
    mediaType: 'image' | 'video' | 'none';
}

export interface PushHistory {
    id: string;
    posts: Post[];
}

export interface ChatMessage {
    role: string;
    content: string;
}
