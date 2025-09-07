// Backend API integration for FastAPI + MongoDB backend
import { fetchWithExponentialBackoff } from './api';

const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL as string) || 'https://preferred-lorri-showoff-fe7be979.koyeb.app';

export interface ContentItem {
    _id: string;
    repository: string;
    event: string;
    commit_sha: string;
    branch: string;
    prompt: string;
    content: string;
    status: 'pending' | 'rephrased' | 'approved' | 'rejected' | 'published';
    created_at?: string;
    updated_at?: string;
    media?: Array<{
        url: string;
        type: 'image' | 'video';
        caption?: string;
    }>;
    platform?: 'LinkedIn' | 'X' | 'Email' | 'TikTok';
    author?: {
        name: string;
        title?: string;
        handle?: string;
        avatar: string;
    };
}

export interface GenerateContentRequest {
    repository: string;
    event: string;
    commit_sha: string;
    branch: string;
}

export interface GenerateContentResponse {
    message: string;
    content_id?: string;
    content?: string;
}

// Generate new content via backend
// export const generateContent = async (request: GenerateContentRequest): Promise<GenerateContentResponse> => {
//     const response = await fetchWithExponentialBackoff(`${BACKEND_URL}/generate-content`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(request)
//     });
//     return await response.json();
// };

// Get all content items from MongoDB
export const getContentItems = async (): Promise<ContentItem[]> => {
    try {
        const response = await fetchWithExponentialBackoff(`${BACKEND_URL}/content`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    } catch (error) {
        console.error('Error fetching content items:', error);
        // Return mock data if backend is not available
        return [];
    }
};

// Update content item status
export const updateContentStatus = async (contentId: string, status: ContentItem['status']): Promise<void> => {
    await fetchWithExponentialBackoff(`${BACKEND_URL}/content/${contentId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    });
};

// Update content text
export const updateContentText = async (contentId: string, content: string): Promise<void> => {
    await fetchWithExponentialBackoff(`${BACKEND_URL}/content/${contentId}/update`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
};

// Get content by ID
export const getContentById = async (contentId: string): Promise<ContentItem> => {
    const response = await fetchWithExponentialBackoff(`${BACKEND_URL}/content/${contentId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    });
    return await response.json();
};

// Rephrase content via backend
export const rephraseContent = async (contentId: string, tone?: number): Promise<string> => {
    console.log('rephraseContent called with:', { contentId, tone });
    
    // Convert tone to instructions for the backend
    const getInstructionsFromTone = (tone: number = 50): string => {
        if (tone < 30) {
            return "Make this content more formal and professional";
        } else if (tone > 70) {
            return "Make this content more casual, engaging, and fun with emojis";
        } else {
            return "Make this content more engaging and professional while maintaining balance";
        }
    };

    const instructions = getInstructionsFromTone(tone);
    console.log('Using instructions:', instructions);
    
    try {
        const response = await fetchWithExponentialBackoff(`${BACKEND_URL}/content/${contentId}/rephrase`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instructions })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Rephrase API response:', result);
        
        if (!result.content) {
            throw new Error('No content returned from rephrase API');
        }
        
        return result.content;
    } catch (error) {
        console.error('Error in rephraseContent:', error);
        throw error;
    }
};

// Approve content and post to social media
export const approveAndPost = async (contentId: string): Promise<void> => {
    await fetchWithExponentialBackoff(`${BACKEND_URL}/content/${contentId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
};

// Mock data for when backend is not available
export const getMockContentItems = (): ContentItem[] => [
    {
        _id: '507f1f77bcf86cd799439011',
        repository: 'user/awesome-project',
        event: 'push',
        commit_sha: 'abc123def456',
        branch: 'main',
        prompt: 'Generate a LinkedIn post announcing new features or changes.',
        content: '🚀 Thrilled to announce a new project launch! Our team has been working on a groundbreaking new feature that will streamline developer workflows and enhance collaboration. So excited to see how this impacts the community! #tech #softwaredevelopment #innovation',
        status: 'pending',
        platform: 'LinkedIn',
        author: { 
            name: 'Alex Johnson', 
            title: 'Senior Software Engineer', 
            avatar: 'https://placehold.co/100x100/A0B9E5/1D4ED8?text=AJ' 
        },
        media: [
            { url: 'https://placehold.co/600x400/D1E0E0/6B7280?text=Project+Launch', type: 'image', caption: 'Project announcement' },
            { url: 'https://placehold.co/600x400/A0B9E5/1D4ED8?text=Team+Photo', type: 'image', caption: 'Our amazing team' }
        ],
    },
    {
        _id: '507f1f77bcf86cd799439012',
        repository: 'user/ai-bot',
        event: 'push',
        commit_sha: 'def456ghi789',
        branch: 'develop',
        prompt: 'Write a concise tweet about recent code commits.',
        content: 'Just got a fresh code push from a dev! My algorithms say this is a huge step forward for the project. Let\'s see what happens next! 🤖 #ai #programming #github',
        status: 'pending',
        platform: 'X',
        author: { 
            name: 'CodeGenBot', 
            handle: '@codegenbot', 
            avatar: 'https://placehold.co/100x100/FCA5A5/DC2626?text=CB' 
        },
        media: [
            { url: 'https://placehold.co/600x400/C1C1E0/6B7280?text=Code+Diff', type: 'image', caption: 'Latest code changes' }
        ],
    },
    {
        _id: '507f1f77bcf86cd799439013',
        repository: 'company/internal-tools',
        event: 'release',
        commit_sha: 'ghi789jkl012',
        branch: 'main',
        prompt: 'Create an email notification about the latest updates to the codebase.',
        content: 'Subject: Important Update on Q4 Initiatives\n\nHi Team,\n\nI\'m writing to share a brief update on the progress of our Q4 initiatives. Please review the attached document for detailed insights and feel free to reach out with any questions.\n\nBest regards,\nMarketing Team',
        status: 'pending',
        platform: 'Email',
        author: { 
            name: 'Marketing Dept', 
            handle: 'marketing@company.com', 
            avatar: 'https://placehold.co/100x100/9CA3AF/374151?text=MD' 
        },
        media: [],
    },
    {
        _id: '507f1f77bcf86cd799439014',
        repository: 'startup/social-app',
        event: 'push',
        commit_sha: 'jkl012mno345',
        branch: 'feature/ui-update',
        prompt: 'Generate a summary of recent codebase changes in a professional tone.',
        content: '🔥 This is how we roll at DevLounge! Brainstorming sessions that are as fun as they are productive. Love the energy and the creative ideas everyone is bringing to the table! #office #worklife #teamwork',
        status: 'pending',
        platform: 'TikTok',
        author: { 
            name: 'DevLounge', 
            handle: '@devlounge', 
            avatar: 'https://placehold.co/100x100/93C5FD/1D4ED8?text=DL' 
        },
        media: [
            { url: 'https://placehold.co/600x800/93C5FD/1D4ED8?text=Office+Video', type: 'video', caption: 'Office vibes' },
            { url: 'https://placehold.co/600x400/F093FB/F5576C?text=Brainstorm', type: 'image', caption: 'Brainstorming session' }
        ],
    },
];

// Test backend connection
export const testBackendConnection = async (): Promise<boolean> => {
    try {
        const response = await fetch(`${BACKEND_URL}/health`, { 
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            const data = await response.json();
            return data.message === 'healthy';
        }
        return false;
    } catch (error) {
        console.log('Backend not available, using mock data:', error);
        return false;
    }
};
