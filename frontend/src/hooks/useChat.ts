import { useState, useEffect, useRef } from 'react';
import { Message, apiService, ChatResponse, Conversation } from '../services/api';

type StreamingStatus = {
    isSearching: boolean;
    isThinking: boolean;
    isStreaming: boolean;
    searchResultCount?: number;
};

export const useChat = (userId: number) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoadingConversations, setIsLoadingConversations] = useState(false);
    const [streamingStatus, setStreamingStatus] = useState<StreamingStatus>({
        isSearching: false,
        isThinking: false,
        isStreaming: false,
        searchResultCount: undefined
    });

    // Use ref to track the latest message content to prevent race conditions
    const latestMessageRef = useRef<string>('');

    // Derive currentStreamingMessage from the messages array
    const currentStreamingMessage = messages.length > 0 && messages[messages.length - 1].role === 'assistant'
        ? messages[messages.length - 1].content
        : '';

    const createConversation = async () => {
        try {
            const data = await apiService.createConversation(userId);
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

    const sendStreamingMessage = async (content: string) => {
        setIsLoading(true);
        try {
            // Add user message immediately
            const newMessage: Message = {
                message_id: Date.now(),
                conversation_id: conversationId || '',
                content,
                role: 'user',
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, newMessage]);

            // Reset streaming states to initial state
            setStreamingStatus({
                isSearching: false,
                isThinking: false,
                isStreaming: false,
                searchResultCount: undefined
            });
            latestMessageRef.current = '';

            // Create response placeholder
            const responseMessage: Message = {
                message_id: Date.now() + 1,
                conversation_id: conversationId || '',
                content: '',
                role: 'assistant',
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, responseMessage]);

            await apiService.streamChat(
                {
                    message: content,
                    user_id: userId.toString(),
                    conversation_id: conversationId || undefined
                },
                {
                    onSearchStart: () => {
                        setStreamingStatus({
                            isSearching: true,
                            isThinking: false,
                            isStreaming: false,
                            searchResultCount: undefined
                        });
                    },
                    onSearchComplete: (metadata) => {
                        setStreamingStatus(prev => ({
                            isSearching: false,
                            isThinking: true,
                            isStreaming: false,
                            searchResultCount: metadata?.count
                        }));
                    },
                    onThinkingStart: () => {
                        setStreamingStatus(prev => ({
                            isSearching: false,
                            isThinking: true,
                            isStreaming: false,
                            searchResultCount: prev.searchResultCount
                        }));
                    },
                    onThinkingComplete: () => {
                        setStreamingStatus(prev => ({
                            isSearching: false,
                            isThinking: false,
                            isStreaming: true,
                            searchResultCount: prev.searchResultCount
                        }));
                        latestMessageRef.current = '';
                        setMessages(prev => {
                            const newMessages = [...prev];
                            if (newMessages.length > 0) {
                                newMessages[newMessages.length - 1].content = '';
                            }
                            return newMessages;
                        });
                    },
                    onToken: (token) => {
                        // Update ref first
                        latestMessageRef.current = latestMessageRef.current + token;

                        // Then update state with the ref value
                        setMessages(prev => {
                            const newMessages = [...prev];
                            if (newMessages.length > 0) {
                                const lastMessage = newMessages[newMessages.length - 1];
                                // Only update if the content would change
                                if (lastMessage.content !== latestMessageRef.current) {
                                    lastMessage.content = latestMessageRef.current;
                                    return newMessages;
                                }
                            }
                            return prev;
                        });
                    },
                    onComplete: () => {
                        setStreamingStatus({
                            isSearching: false,
                            isThinking: false,
                            isStreaming: false,
                            searchResultCount: undefined
                        });
                    },
                    onError: (error) => {
                        console.error('Streaming error:', error);
                        // Reset status on error
                        setStreamingStatus({
                            isSearching: false,
                            isThinking: false,
                            isStreaming: false,
                            searchResultCount: undefined
                        });
                    }
                }
            );
        } catch (error) {
            console.error('Failed to stream message:', error);
            // Reset status on error
            setStreamingStatus({
                isSearching: false,
                isThinking: false,
                isStreaming: false,
                searchResultCount: undefined
            });
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
        sendStreamingMessage,
        resetConversation,
        conversationId,
        conversations,
        isLoadingConversations,
        setCurrentConversation,
        createConversation,
        deleteConversation,
        streamingStatus,
        currentStreamingMessage
    };
} 