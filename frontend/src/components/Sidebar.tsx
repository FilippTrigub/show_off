import React from 'react';
import { PushHistory } from '../types/shared';

interface SidebarProps {
    postHistory: PushHistory[];
    currentPushId: string | null;
    onLoadPush: (pushId: string) => void;
    isOpen: boolean;
    backendConnected: boolean;
    onOverlayClick: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    postHistory,
    currentPushId,
    onLoadPush,
    isOpen,
    backendConnected,
    onOverlayClick
}) => {
    return (
        <>
            {/* Mobile Overlay */}
            <div 
                className={`overlay ${isOpen ? 'visible' : ''} lg:hidden`}
                onClick={onOverlayClick}
            />

            {/* Glassmorphism Sidebar */}
            <nav className={`sidebar ${isOpen ? 'open' : ''}`}>
                <div className="floating" style={{ marginTop: '0.5rem', marginBottom: '1rem' }}>
                    <h2 className="text-2xl font-bold mb-3 text-white bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">
                        Content History
                    </h2>
                    <div className={`text-xs px-3 py-1 rounded-full ${backendConnected ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                        {backendConnected ? '🟢 Backend Connected' : '🔴 Mock Data'}
                    </div>
                </div>
                <ul className="flex-grow overflow-y-auto space-y-3" style={{ paddingTop: '0' }}>
                    {postHistory.map(push => (
                        <li
                            key={push.id}
                            className={`sidebar-item cursor-pointer ${push.id === currentPushId ? 'active' : ''}`}
                            onClick={() => onLoadPush(push.id)}
                        >
                            <div className="font-semibold">{push.id.split('-')[0]}</div>
                            <div className="text-sm opacity-75">{push.posts.length} posts • {push.id.split('-')[1] || 'main'}</div>
                        </li>
                    ))}
                </ul>
            </nav>
        </>
    );
};

export default Sidebar;
