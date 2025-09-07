// Shared TypeScript interfaces for the application

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
    media: Array<{
        url: string;
        type: 'image' | 'video';
        caption?: string;
    }>;
    repository?: string;
    commit_sha?: string;
    branch?: string;
}

export interface PushHistory {
    id: string;
    posts: Post[];
}
