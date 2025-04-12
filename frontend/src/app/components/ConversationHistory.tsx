'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Trash, Folder, File } from 'lucide-react';
import { DirectoryTreeNode, DirectoryTreeResponse } from '@/services/api';
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
    files: DirectoryTreeResponse;
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

interface FileTreeNodeProps {
    node: DirectoryTreeNode;
    selectedFiles: Set<number>;
    toggleFileSelection: (document_id: number) => void;
    level?: number;
}

const FileTreeNode: React.FC<FileTreeNodeProps> = ({
    node,
    selectedFiles,
    toggleFileSelection,
    level = 0
}) => {
    const [isOpen, setIsOpen] = useState(true);
    // Add base indentation for all items to appear under Files section
    const baseIndent = 1;
    const paddingLeft = `${(level + baseIndent) * 1}rem`;

    // Handle directory nodes
    if (node.type === 'directory') {
        return (
            <div>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center space-x-2 px-4 py-1 w-full hover:bg-gray-100 rounded-md"
                    style={{ paddingLeft }}
                >
                    {isOpen ? (
                        <ChevronDown className="w-4 h-4" />
                    ) : (
                        <ChevronRight className="w-4 h-4" />
                    )}
                    <Folder className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium">{node.name}</span>
                </button>
                {isOpen && node.children && node.children.length > 0 && (
                    <div className="space-y-1">
                        {node.children.map((child, index) => (
                            <FileTreeNode
                                key={`${child.name}-${index}`}
                                node={child}
                                selectedFiles={selectedFiles}
                                toggleFileSelection={toggleFileSelection}
                                level={level + 1}
                            />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Handle file nodes
    if (node.type === 'file' && node.document !== undefined && node.document !== null) {
        // Calculate proper indentation based on path length, including base indent
        const fileLevel = node.path.length > 1 ? level : 0;
        const actualPaddingLeft = `${(fileLevel + baseIndent) * 1}rem`;

        return (
            <div
                className="flex items-center space-x-2 px-4 py-1 hover:bg-gray-100 rounded-md"
                style={{ paddingLeft: actualPaddingLeft }}
            >
                <Checkbox
                    checked={selectedFiles.has(node.document.id)}
                    onCheckedChange={() => toggleFileSelection(node.document.id)}
                />
                <File className="w-4 h-4 text-gray-500" />
                <span className="text-sm truncate" title={node.name}>
                    {node.name}
                </span>
            </div>
        );
    }

    return null;
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
                            {files.children.map((node, index) => (
                                <FileTreeNode
                                    key={`${node.name}-${index}`}
                                    node={node}
                                    selectedFiles={selectedFiles}
                                    toggleFileSelection={toggleFileSelection}
                                />
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