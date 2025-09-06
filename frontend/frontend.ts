import React, { useState, useEffect, useRef } from 'react';

// Define TypeScript interfaces for data structures
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
    mediaUrl: string;
    mediaType: 'image' | 'video' | 'none';
}

interface PushHistory {
    id: string;
    posts: Post[];
}

// Mock data for social media posts
const mockPosts: Omit<Post, 'id'>[] = [
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

const generationModel = "gemini-2.5-flash-preview-05-20";
const ttsModel = "gemini-2.5-flash-preview-tts";

const App: React.FC = () => {
    const [posts, setPosts] = useState<Post[]>([]);
    const [postHistory, setPostHistory] = useState<PushHistory[]>([]);
    const [currentPushId, setCurrentPushId] = useState<string | null>(null);
    const [tone, setTone] = useState<number>(50);
    const [message, setMessage] = useState<string>('');
    const [showMessage, setShowMessage] = useState<boolean>(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

    const messageTimeoutRef = useRef<number | null>(null);

    // --- Core App Functions ---

    // Initializes the app on component mount
    useEffect(() => {
        // Generates and sets up the initial mock history
        const today = new Date();
        const newPushes: PushHistory[] = [];

        // Generate 5 mock pushes with unique IDs and slightly varied content
        for (let i = 4; i >= 0; i--) {
            const pushId = `push-${(today.getTime() - i * 86400000).toString(16).slice(-8)}`; // Unique ID based on date
            const newPosts: Post[] = JSON.parse(JSON.stringify(mockPosts)).map((post: Omit<Post, 'id'>, index: number) => ({
                ...post,
                id: `${post.platform.toLowerCase()}-${pushId}`,
                content: post.content.includes("new project launch") ? `[${pushId}] Announcing our latest milestone! Our team just wrapped up a project that will change the game. #productlaunch #development` : post.content,
            }));
            newPushes.push({ id: pushId, posts: newPosts });
        }
        setPostHistory(newPushes);
    }, []);

    // Effect to load the latest push after postHistory has been set
    useEffect(() => {
        if (postHistory.length > 0 && currentPushId === null) {
            const latestPush = postHistory[postHistory.length - 1];
            loadPush(latestPush.id);
        }
    }, [postHistory]);

    // Toggles the sidebar visibility
    const toggleSidebar = () => {
        setIsSidebarOpen(prev => !prev);
    };

    // Loads a specific push's posts into the main view
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

    // Function to show a temporary notification
    const showNotification = (msg: string) => {
        if (messageTimeoutRef.current) {
            clearTimeout(messageTimeoutRef.current);
        }
        setMessage(msg);
        setShowMessage(true);
        messageTimeoutRef.current = setTimeout(() => {
            setShowMessage(false);
        }, 3000);
    };

    // Handles approval of a post
    const handleApprove = (id: string) => {
        const updatedPosts = posts.map(p => p.id === id ? { ...p, status: 'approved' } : p);
        setPosts(updatedPosts);
        showNotification(`Post for ${posts.find(p => p.id === id)?.platform} Approved!`);
    };

    // Handles disapproval of a post
    const handleDisapprove = (id: string) => {
        const updatedPosts = posts.map(p => p.id === id ? { ...p, status: 'disapproved' } : p);
        setPosts(updatedPosts);
        showNotification(`Post for ${posts.find(p => p.id === id)?.platform} Disapproved.`);
    };

    // Checks if all posts are approved
    const allPostsApproved = posts.every(post => post.status === 'approved' || post.status === 'posted');

    // Simulates posting all approved content
    const handlePostAll = () => {
        if (allPostsApproved) {
            console.log("Posting all approved content:", posts);
            showNotification("All approved content is now being posted!");
            setPosts(posts.map(p => ({ ...p, status: 'posted' })));
        } else {
            showNotification("Cannot post. All posts must be approved first.");
        }
    };

    // Renders the media content based on post data
    const renderMedia = (post: Post) => {
        if (post.mediaType === 'image') {
            return <img src={post.mediaUrl} alt="Post Media" className="w-full h-auto object-cover" />;
        } else if (post.mediaType === 'video') {
            return <video src={post.mediaUrl} className="w-full h-auto object-cover" controls autoPlay muted loop></video>;
        }
        return <div className="bg-gray-200 h-48 flex items-center justify-center text-gray-400 font-medium">No Media</div>;
    };

    // Handles local media file upload and preview
    const handleMediaUpload = (event: React.ChangeEvent<HTMLInputElement>, id: string) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const result = e.target?.result as string;
            setPosts(prevPosts =>
                prevPosts.map(p =>
                    p.id === id
                        ? { ...p, mediaUrl: result, mediaType: file.type.startsWith('image') ? 'image' : 'video' }
                        : p
                )
            );
        };
        reader.readAsDataURL(file);
    };

    // Updates the content of a post
    const handleContentChange = (event: React.ChangeEvent<HTMLTextAreaElement>, id: string) => {
        const { value } = event.target;
        setPosts(prevPosts =>
            prevPosts.map(p =>
                p.id === id ? { ...p, content: value } : p
            )
        );
    };

    // --- Gemini API Integrations ---

    const apiKey = "";

    // Function to handle exponential backoff for API calls
    const fetchWithExponentialBackoff = async (url: string, options: RequestInit, retries = 3, delay = 1000): Promise<Response> => {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`API call failed with status: ${response.status}`);
            }
            return response;
        } catch (error) {
            if (retries > 0) {
                console.log(`Retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                return fetchWithExponentialBackoff(url, options, retries - 1, delay * 2);
            } else {
                throw error;
            }
        }
    };

    // Converts base64 to an array buffer
    const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
        const binaryString = atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    };

    // Converts PCM audio data to a playable WAV file blob
    const pcmToWav = (pcmData: Int16Array, sampleRate: number): Blob => {
        const wavBuffer = new ArrayBuffer(44 + pcmData.length * 2);
        const view = new DataView(wavBuffer);

        let offset = 0;
        const writeString = (str: string) => {
            for (let i = 0; i < str.length; i++) {
                view.setUint8(offset++, str.charCodeAt(i));
            }
        };

        writeString('RIFF');
        view.setUint32(offset, 36 + pcmData.length * 2, true);
        offset += 4;
        writeString('WAVE');
        writeString('fmt ');
        view.setUint32(offset, 16, true);
        offset += 4;
        view.setUint16(offset, 1, true); // Audio format (PCM)
        offset += 2;
        view.setUint16(offset, 1, true); // Num channels
        offset += 2;
        view.setUint32(offset, sampleRate, true);
        offset += 4;
        view.setUint32(offset, sampleRate * 2, true); // Byte rate
        offset += 4;
        view.setUint16(offset, 2, true); // Block align
        offset += 2;
        view.setUint16(offset, 16, true); // Bits per sample
        offset += 2;
        writeString('data');
        view.setUint32(offset, pcmData.length * 2, true);
        offset += 4;

        for (let i = 0; i < pcmData.length; i++) {
            view.setInt16(offset, pcmData[i], true);
            offset += 2;
        }

        return new Blob([wavBuffer], { type: 'audio/wav' });
    };

    // Handles the rephrasing of a post using Gemini
    const rephrasePost = async (id: string) => {
        const post = posts.find(p => p.id === id);
        if (!post) return;

        const originalContent = post.content;
        const updatedPosts = posts.map(p => p.id === id ? { ...p, content: 'Rephrasing, please wait...' } : p);
        setPosts(updatedPosts);

        let tonePrompt = "neutral and professional";
        if (tone < 30) {
            tonePrompt = "very formal and serious";
        } else if (tone < 70) {
            tonePrompt = "friendly and professional";
        } else {
            tonePrompt = "fun and creative";
        }

        try {
            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${generationModel}:generateContent?key=${apiKey}`;
            const systemPrompt = `You are an expert social media manager. Your task is to rewrite the provided text to be more ${tonePrompt}. Do not add any new information, just rephrase the existing content. Do not output anything other than the new text.`;
            const userQuery = `Original Text: "${originalContent}"`;

            const payload = {
                contents: [{ parts: [{ text: userQuery }] }],
                systemInstruction: { parts: [{ text: systemPrompt }] },
            };

            const response = await fetchWithExponentialBackoff(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            const newText = result.candidates?.[0]?.content?.parts?.[0]?.text;

            if (newText) {
                setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: newText.trim() } : p));
                showNotification("Post rephrased successfully! ✨");
            } else {
                setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: originalContent } : p));
                showNotification("Failed to rephrase post.");
            }

        } catch (error) {
            console.error('Error rephrasing post:', error);
            setPosts(prevPosts => prevPosts.map(p => p.id === id ? { ...p, content: originalContent } : p));
            showNotification("An error occurred during rephrasing.");
        }
    };

    // Handles the Text-to-Speech functionality
    const readAloud = async (id: string) => {
        const post = posts.find(p => p.id === id);
        if (!post) return;

        try {
            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${ttsModel}:generateContent?key=${apiKey}`;

            const payload = {
                contents: [{ parts: [{ text: post.content }] }],
                generationConfig: {
                    responseModalities: ["AUDIO"],
                    speechConfig: {
                        voiceConfig: {
                            prebuiltVoiceConfig: { voiceName: "Puck" }
                        }
                    }
                },
            };

            const response = await fetchWithExponentialBackoff(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            const audioData = result?.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
            const mimeType = result?.candidates?.[0]?.content?.parts?.[0]?.inlineData?.mimeType;

            if (audioData && mimeType && mimeType.startsWith("audio/")) {
                const sampleRate = parseInt(mimeType.match(/rate=(\d+)/)?.[1] || '16000', 10);
                const pcmData = new Int16Array(base64ToArrayBuffer(audioData));
                const wavBlob = pcmToWav(pcmData, sampleRate);
                const audioUrl = URL.createObjectURL(wavBlob);
                const audio = new Audio(audioUrl);
                audio.play();
                showNotification("Playing audio... 🎧");
            } else {
                showNotification("Failed to generate audio.");
            }
        } catch (error) {
            console.error('Error generating TTS:', error);
            showNotification("An error occurred during audio generation.");
        }
    };

    return (
        <div className="bg-gray-100 flex flex-row min-h-screen">
            {/* Custom Styles for a single file */}
            <style>{`
                body {
                    font-family: 'Inter', sans-serif;
                    background-color: #f3f4f6;
                    color: #374151;
                    padding: 0;
                    margin: 0;
                    display: flex;
                    min-height: 100vh;
                }
                .knob-container input[type="range"] {
                    -webkit-appearance: none;
                    width: 100%;
                    height: 8px;
                    background: linear-gradient(to right, #6EE7B7, #3B82F6);
                    outline: none;
                    border-radius: 9999px;
                    cursor: pointer;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .knob-container input[type="range"]::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 24px;
                    height: 24px;
                    background: #fff;
                    border: 2px solid #1D4ED8;
                    border-radius: 50%;
                    cursor: pointer;
                    transition: background 0.2s, transform 0.2s;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
                }
                .knob-container input[type="range"]::-moz-range-thumb {
                    width: 24px;
                    height: 24px;
                    background: #fff;
                    border: 2px solid #1D4ED8;
                    border-radius: 50%;
                    cursor: pointer;
                    transition: background 0.2s, transform 0.2s;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
                }
                .knob-container input[type="range"]:hover::-webkit-slider-thumb {
                    background: #BFDBFE;
                    transform: scale(1.1);
                }
                .knob-container input[type="range"]:hover::-moz-range-thumb {
                    background: #BFDBFE;
                    transform: scale(1.1);
                }
                .post-card-container {
                    transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
                }
                .post-card-container:hover {
                    transform: translateY(-5px);
                }
                .message-box {
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    z-index: 1000;
                    background-color: #10B981;
                    color: white;
                    padding: 1rem 2rem;
                    border-radius: 9999px;
                    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
                    opacity: 0;
                    visibility: hidden;
                    transition: opacity 0.5s ease-in-out, visibility 0.5s ease-in-out;
                    pointer-events: none;
                }
                .message-box.show {
                    opacity: 1;
                    visibility: visible;
                }
                .loading-spinner {
                    border: 4px solid rgba(255, 255, 255, 0.3);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    width: 24px;
                    height: 24px;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .sidebar {
                    width: 280px;
                    background-color: #2c3e50;
                    padding: 2rem;
                    color: #ecf0f1;
                    box-shadow: 4px 0 15px rgba(0, 0, 0, 0.2);
                    display: flex;
                    flex-direction: column;
                    position: fixed;
                    top: 0;
                    left: -280px;
                    height: 100%;
                    transition: left 0.3s ease-in-out;
                    z-index: 50;
                }
                .sidebar.open {
                    left: 0;
                }
                @media (min-width: 1024px) {
                    .sidebar {
                        position: static;
                        left: 0;
                    }
                }
                .sidebar-item {
                    padding: 0.75rem 1rem;
                    margin-bottom: 0.5rem;
                    background-color: #34495e;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                .sidebar-item:hover {
                    background-color: #3b506b;
                }
                .sidebar-item.active {
                    background-color: #1abc9c;
                    font-weight: bold;
                }
                .overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    z-index: 40;
                    visibility: hidden;
                    opacity: 0;
                    transition: opacity 0.3s ease-in-out, visibility 0.3s ease-in-out;
                }
                .overlay.visible {
                    visibility: visible;
                    opacity: 1;
                }
            `}</style>

            {/* Overlay for the sidebar on mobile */}
            <div className={`overlay ${isSidebarOpen ? 'visible' : ''}`} onClick={toggleSidebar}></div>

            {/* Sidebar for Push History */}
            <nav className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
                <h2 className="text-2xl font-bold mb-6 text-white">Past Pushes</h2>
                <ul className="flex-grow overflow-y-auto">
                    {postHistory.map(push => (
                        <li
                            key={push.id}
                            className={`sidebar-item cursor-pointer text-sm truncate ${push.id === currentPushId ? 'active' : ''}`}
                            onClick={() => loadPush(push.id)}
                        >
                            Push ID: {push.id}
                        </li>
                    ))}
                </ul>
            </nav>

            {/* Main Content Area */}
            <main className="flex-grow p-4 sm:p-8 overflow-y-auto">
                {/* Burger menu button (visible on small screens only) */}
                <button
                    className="lg:hidden fixed top-4 left-4 z-[60] p-2 bg-gray-800 text-white rounded-md shadow-lg"
                    onClick={toggleSidebar}
                >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
                    </svg>
                </button>

                <header className="text-center mb-8">
                    <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-2">
                        42 hack project MCP Marketing
                    </h1>
                    <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                        Review, edit, and approve content before it goes live.
                    </p>
                </header>

                {/* Post Visualization Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {posts.map(post => (
                        <div
                            key={post.id}
                            className={`post-card-container bg-white p-6 rounded-2xl shadow-md transition-all ease-in-out duration-300 transform ${post.status === 'approved' ? 'border-4 border-green-500' : post.status === 'disapproved' ? 'border-4 border-red-500 opacity-70' : ''}`}
                        >
                            <h3 className="text-xl font-bold mb-4 text-gray-700">{post.platform} Post</h3>
                            <div className="flex items-center mb-4">
                                <img src={post.author.avatar} alt={`${post.author.name}'s Avatar`} className="h-10 w-10 rounded-full mr-2" />
                                <span className="font-bold text-gray-800">{post.author.name}</span>
                            </div>

                            {/* Media Section */}
                            <div className="rounded-xl overflow-hidden mb-4 relative">
                                {renderMedia(post)}
                                <label htmlFor={`media-upload-${post.id}`} className="absolute inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer text-white text-lg font-bold">
                                    <span className="flex items-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                        </svg>
                                        Edit Media
                                    </span>
                                </label>
                                <input
                                    type="file"
                                    id={`media-upload-${post.id}`}
                                    className="hidden"
                                    accept="image/*,video/*"
                                    onChange={(e) => handleMediaUpload(e, post.id)}
                                />
                            </div>

                            <textarea
                                value={post.content}
                                onChange={(e) => handleContentChange(e, post.id)}
                                disabled={post.status !== 'pending'}
                                className={`w-full h-40 rounded-lg border border-gray-200 bg-gray-50 p-4 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors`}
                            />

                            {/* LLM-powered Action Buttons */}
                            <div className="mt-4 flex gap-2">
                                <button
                                    onClick={() => rephrasePost(post.id)}
                                    disabled={post.status !== 'pending'}
                                    className="flex items-center justify-center px-4 py-2 rounded-full text-blue-600 font-medium bg-blue-100 hover:bg-blue-200 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Rephrase ✨
                                </button>
                                <button
                                    onClick={() => readAloud(post.id)}
                                    disabled={post.platform === 'TikTok' || post.status !== 'pending'}
                                    className="flex items-center justify-center px-4 py-2 rounded-full text-purple-600 font-medium bg-purple-100 hover:bg-purple-200 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Read Aloud 🎧
                                </button>
                            </div>

                            {/* Approval Action Buttons */}
                            <div className="mt-6 flex gap-4">
                                <button
                                    onClick={() => handleApprove(post.id)}
                                    disabled={post.status !== 'pending'}
                                    className="flex items-center justify-center px-4 py-2 rounded-full text-white font-medium bg-green-500 hover:bg-green-600 transition-colors shadow-md w-full disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                                    Approve
                                </button>
                                <button
                                    onClick={() => handleDisapprove(post.id)}
                                    disabled={post.status !== 'pending'}
                                    className="flex items-center justify-center px-4 py-2 rounded-full text-white font-medium bg-red-500 hover:bg-red-600 transition-colors shadow-md w-full disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                                    Disapprove
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Global Action Section */}
                <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-xl mt-12 flex flex-col sm:flex-row items-center justify-between gap-6">
                    <button
                        onClick={handlePostAll}
                        disabled={!allPostsApproved}
                        className={`px-6 py-3 rounded-full font-bold transition-colors shadow-md w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed ${allPostsApproved ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-400 text-white'}`}
                    >
                        Post All Approved Content
                    </button>

                    {/* Tone Control Section */}
                    <div className="flex-grow flex items-center justify-between w-full sm:w-auto">
                        <span className="text-gray-500 font-medium whitespace-nowrap mr-4">Serious</span>
                        <div className="flex-grow knob-container relative mx-4 w-full">
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={tone}
                                onChange={(e) => setTone(parseInt(e.target.value, 10))}
                                className="w-full"
                            />
                        </div>
                        <span className="text-gray-500 font-medium whitespace-nowrap ml-4">Fun</span>
                    </div>
                </div>

                {/* Notification Message Box */}
                <div className={`message-box ${showMessage ? 'show' : ''}`}>
                    {message}
                </div>
            </main
        </div>
    );
};

export default App;
