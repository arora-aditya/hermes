'use client';

import { useState } from 'react';
import { DirectoryTreeResponse, Conversation } from '@/services/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CollapsibleSection } from './conversation-history/collapsible-section';
import { ConversationList } from './conversation-history/conversation-list';
import { FileList } from './conversation-history/file-list';

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
    moveFile: (documentId: number, newPath: string) => Promise<void>;
    deleteFile: (documentId: number) => Promise<void>;
}

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
    moveFile,
    deleteFile,
}) => {
    const [isConversationsOpen, setIsConversationsOpen] = useState(true);
    const [isFilesOpen, setIsFilesOpen] = useState(true);

    return (
        <div className="w-72 min-w-72 border-r h-screen bg-gray-50">
            <ScrollArea className="h-full px-4 py-4">
                <CollapsibleSection
                    title="Conversations"
                    isOpen={isConversationsOpen}
                    onToggle={() => setIsConversationsOpen(!isConversationsOpen)}
                >
                    <ConversationList
                        conversations={conversations}
                        isLoadingConversations={isLoadingConversations}
                        onSelectConversation={onSelectConversation}
                        onDeleteConversation={onDeleteConversation}
                        currentConversationId={currentConversationId}
                    />
                </CollapsibleSection>

                <CollapsibleSection
                    title="Files"
                    isOpen={isFilesOpen}
                    onToggle={() => setIsFilesOpen(!isFilesOpen)}
                >
                    <FileList
                        files={files}
                        selectedFiles={selectedFiles}
                        loading={loading}
                        toggleFileSelection={toggleFileSelection}
                        handleIndex={handleIndex}
                        moveFile={moveFile}
                        deleteFile={deleteFile}
                    />
                </CollapsibleSection>
            </ScrollArea>
        </div>
    );
}; 