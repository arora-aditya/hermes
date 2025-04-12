'use client';

import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleSectionProps {
    title: string;
    isOpen: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}

export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
    title,
    isOpen,
    onToggle,
    children,
}) => {
    return (
        <div className="mb-4">
            <button
                onClick={onToggle}
                className="flex items-center w-full p-2 text-sm font-semibold text-gray-700 hover:bg-gray-100 rounded-lg"
            >
                {isOpen ? (
                    <ChevronDown className="w-4 h-4 mr-2" />
                ) : (
                    <ChevronRight className="w-4 h-4 mr-2" />
                )}
                {title}
            </button>
            {isOpen && <div className="mt-2">{children}</div>}
        </div>
    );
}; 