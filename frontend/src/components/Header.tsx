import React from 'react';

interface HeaderProps {
    tone: number;
    onToneChange: (tone: number) => void;
    onToggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ tone, onToneChange, onToggleSidebar }) => {
    return (
        <header className="relative p-8 text-center">
            <button
                className="lg:hidden fixed top-6 left-6 z-[60] p-3 modern-button bg-white/20 backdrop-blur-lg rounded-2xl shadow-lg border border-white/30"
                onClick={onToggleSidebar}
            >
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
                </svg>
            </button>

            <div className="floating">
                <h1 className="text-6xl font-bold text-white mb-4 bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
                    AI Content Manager
                </h1>
                <p className="text-xl text-white/80 font-medium max-w-2xl mx-auto">
                    Review and manage AI-generated social media content from your repositories
                </p>
            </div>

            {/* Tone Control */}
            <div className="mt-8 max-w-md mx-auto">
                <div className="backdrop-filter backdrop-blur-lg bg-white/10 rounded-3xl p-6 border border-white/20">
                    <label className="block text-white font-semibold mb-3">Content Tone</label>
                    <div className="knob-container">
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={tone}
                            onChange={(e) => onToneChange(Number(e.target.value))}
                            className="w-full"
                        />
                    </div>
                    <div className="flex justify-between text-sm text-white/70 mt-2">
                        <span>Professional</span>
                        <span>Casual</span>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
