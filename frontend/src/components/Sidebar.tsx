import React from 'react';
import { PushHistory } from '../types';

interface SidebarProps {
    postHistory: PushHistory[];
    currentPushId: string | null;
    onLoadPush: (pushId: string) => void;
    isOpen: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
    postHistory,
    currentPushId,
    onLoadPush,
    isOpen
}) => {
    return (
        <>
            {/* Overlay for the sidebar on mobile */}
            <div className={`overlay ${isOpen ? 'visible' : ''}`}></div>

            {/* Sidebar for Push History */}
            <nav className={`sidebar ${isOpen ? 'open' : ''}`}>
                <h2 className="text-2xl font-bold mb-6 text-white">Past Pushes</h2>
                <ul className="flex-grow overflow-y-auto">
                    {postHistory.map(push => (
                        <li
                            key={push.id}
                            className={`sidebar-item cursor-pointer text-sm truncate ${push.id === currentPushId ? 'active' : ''}`}
                            onClick={() => onLoadPush(push.id)}
                        >
                            Push ID: {push.id}
                        </li>
                    ))}
                </ul>
            </nav>
        </>
    );
};

export default Sidebar;
