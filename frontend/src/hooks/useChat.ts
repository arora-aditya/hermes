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

    const createConversation = async () => {
        try {
            const data = await apiService.createConversation('2');
            // Update all related state in a single batch
            setMessages([]);
            setConversations(prev => [data, ...prev]);
            setConversationId(data.conversation_id);
            return data;
        } catch (error) {
            console.error('Error creating conversation:', error);
            throw error;
        }
    }


    const deleteConversation = async (conversationId: string) => {
        const data = await apiService.deleteConversation(conversationId);
        setConversations(conversations.filter(conversation => conversation.conversation_id !== conversationId));
        setConversationId(null);
        return data;
    }

    const loadConversations = async () => {
        setIsLoadingConversations(true);
        try {
            const data = await apiService.getConversations();
            setConversations(data);
            return data;
        } catch (error) {
            console.error('Failed to fetch conversations:', error);
            setConversations([]);
            return [];
        } finally {
            setIsLoadingConversations(false);
        }
    };

    useEffect(() => {
        // Load conversations on mount
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

    const setCurrentConversation = async (newConversationId: string | undefined) => {
        setConversationId(newConversationId || null);
        if (newConversationId) {
            const conversation = await apiService.getConversation(newConversationId);
            if (conversation.messages) {
                setMessages(conversation.messages);
            }
        } else {
            setMessages([]);
        }
    };

    const resetConversation = async () => {
        setMessages([]);
        setConversationId(null);
        await loadConversations();
    };

    return {
        messages,
        isLoading,
        sendMessage,
        resetConversation,
        conversationId,
        conversations,
        isLoadingConversations,
        setCurrentConversation,
        createConversation,
        deleteConversation
    };
} 