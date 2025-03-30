'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Trash } from 'lucide-react';
import { FileInfo } from '@/services/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { useChat } from '@/hooks/useChat';
import { Conversation } from '@/services/api';

interface ConversationHistoryProps {
    conversations: Conversation[];
    isLoadingConversations: boolean;
    onSelectConversation: (conversationId: string) => void;
    onDeleteConversation: (conversationId: string) => void;
    currentConversationId?: string;
    files: FileInfo[];
    selectedFiles: Set<number>;
    loading: boolean;
    toggleFileSelection: (document_id: number) => void;
    handleIndex: () => Promise<void>;
}

interface CollapsibleSectionProps {
    title: string;
    isOpen: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
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

export const ConversationHistory: React.FC<ConversationHistoryProps> = ({
    conversations,
    isLoadingConversations,
    onSelectConversation,
    onDeleteConversation,
    currentConversationId,
    files,
    selectedFiles,
    loading,
    toggleFileSelection,
    handleIndex,
}) => {
    const [isConversationsOpen, setIsConversationsOpen] = useState(true);
    const [isFilesOpen, setIsFilesOpen] = useState(true);

    return (
        <div className="w-64 min-w-64 border-r h-screen bg-gray-50">
            <ScrollArea className="h-full px-4 py-4">
                <CollapsibleSection
                    title="Conversations"
                    isOpen={isConversationsOpen}
                    onToggle={() => setIsConversationsOpen(!isConversationsOpen)}
                >
                    <div className="space-y-1">
                        {isLoadingConversations ? (
                            <div className="text-sm text-gray-500 px-4 py-2">Loading conversations...</div>
                        ) : conversations.length === 0 ? (
                            <div className="text-sm text-gray-500 px-4 py-2">No conversations yet</div>
                        ) : (
                            conversations.map((conversation) => (
                                <div className="flex items-center justify-between"
                                    key={conversation.conversation_id}>
                                    <button
                                        onClick={() => onSelectConversation(conversation.conversation_id)}
                                        className={`w-full text-left px-4 py-2 text-sm rounded-lg transition-colors ${currentConversationId === conversation.conversation_id
                                            ? 'bg-gray-200 text-gray-900'
                                            : 'text-gray-700 hover:bg-gray-100'
                                            }`}
                                    >
                                        Conversation {new Date(conversation.created_at).toLocaleDateString()}
                                    </button>
                                    <button
                                        onClick={() => onDeleteConversation(conversation.conversation_id)}
                                    >
                                        <Trash className="w-4 h-4" />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </CollapsibleSection>

                <CollapsibleSection
                    title="Files"
                    isOpen={isFilesOpen}
                    onToggle={() => setIsFilesOpen(!isFilesOpen)}
                >
                    {loading ? (
                        <div className="text-sm text-gray-500 px-4 py-2">Loading files...</div>
                    ) : (
                        <div className="space-y-2">
                            {files.map((file) => (
                                <div key={file.id} className="flex items-center space-x-2 px-4">
                                    <Checkbox
                                        checked={selectedFiles.has(file.id)}
                                        onCheckedChange={() => toggleFileSelection(file.id)}
                                    />
                                    <span className="text-sm truncate" title={file.filename}>
                                        {file.filename}
                                    </span>
                                </div>
                            ))}
                            <button
                                onClick={handleIndex}
                                disabled={selectedFiles.size === 0}
                                className={`w-full mt-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${selectedFiles.size === 0
                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    : 'text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                                    }`}
                            >
                                Index Files
                            </button>
                        </div>
                    )}
                </CollapsibleSection>
            </ScrollArea>
        </div>
    );
}; 