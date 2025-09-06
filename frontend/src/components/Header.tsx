import React from 'react';

interface HeaderProps {
    onToggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
    return (
        <header className="text-center mb-8">
            {/* Burger menu button (visible on small screens only) */}
            <button
                className="lg:hidden fixed top-4 left-4 z-[60] p-2 bg-gray-800 text-white rounded-md shadow-lg"
                onClick={onToggleSidebar}
            >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7" />
                </svg>
            </button>

            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 mb-2">
                42 hack project MCP Marketing
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Review, edit, and approve content before it goes live.
            </p>
        </header>
    );
};

export default Header;
