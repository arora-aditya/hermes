'use client';

import { Trash } from 'lucide-react';
import { Conversation } from '@/services/api';

interface ConversationListProps {
    conversations: Conversation[];
    isLoadingConversations: boolean;
    onSelectConversation: (conversationId: string) => void;
    onDeleteConversation: (conversationId: string) => void;
    currentConversationId?: string;
}

export const ConversationList: React.FC<ConversationListProps> = ({
    conversations,
    isLoadingConversations,
    onSelectConversation,
    onDeleteConversation,
    currentConversationId,
}) => {
    if (isLoadingConversations) {
        return <div className="text-sm text-gray-500 px-4 py-2">Loading conversations...</div>;
    }

    if (conversations.length === 0) {
        return <div className="text-sm text-gray-500 px-4 py-2">No conversations yet</div>;
    }

    return (
        <div className="space-y-1">
            {conversations.map((conversation) => (
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
            ))}
        </div>
    );
}; 