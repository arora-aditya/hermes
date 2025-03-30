import { useState, useEffect } from 'react';
import { Message, apiService, ChatResponse, Conversation } from '../services/api';

export const useChat = (initialConversationId?: string) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(initialConversationId || null);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoadingConversations, setIsLoadingConversations] = useState(false);

    useEffect(() => {
        // Only load initial conversation if conversationId is provided
        if (initialConversationId) {
            const loadConversation = async () => {
                setIsLoading(true);
                try {
                    const conversation = await apiService.getConversation(initialConversationId);
                    if (conversation.messages) {
                        setMessages(conversation.messages);
                    }
                } catch (error) {
                    console.error('Error loading conversation:', error);
                } finally {
                    setIsLoading(false);
                }
            };

            loadConversation();
        }
    }, [initialConversationId]);

    useEffect(() => {
        // Load conversations on mount
        const loadConversations = async () => {
            setIsLoadingConversations(true);
            try {
                const data = await apiService.getConversations();
                setConversations(data);
            } catch (error) {
                console.error('Failed to fetch conversations:', error);
                setConversations([]);
            } finally {
                setIsLoadingConversations(false);
            }
        };

        loadConversations();
    }, []);

    const sendMessage = async (content: string) => {
        setIsLoading(true);
        try {
            const newMessage: Message = {
                message_id: Date.now(), // Temporary ID until server response
                conversation_id: conversationId || '',
                content,
                role: 'user',
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, newMessage]);

            const response = await apiService.sendChatMessage({
                message: content,
                conversation_id: conversationId,
                user_id: '2' // TODO: Replace with actual user ID
            });

            // If this is the first message, set the conversation ID
            if (!conversationId) {
                setConversationId(response.conversation_id);
            }

            const assistantMessage: Message = {
                message_id: Date.now() + 1, // Temporary ID until server response
                conversation_id: response.conversation_id,
                content: response.message,
                role: 'assistant',
                created_at: new Date().toISOString()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Failed to send message:', error);
        } finally {
            setIsLoading(false);
        }
    };


    const resetConversation = () => {
        setMessages([]);
        setConversationId(null);
    };

    return {
        messages,
        isLoading,
        sendMessage,
        resetConversation,
        conversationId,
        conversations,
        isLoadingConversations
    };
} 