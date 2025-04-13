import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface FileInfo {
    id: number;
    filename: string;
    is_ingested: boolean;
    created_at: string;
    updated_at?: string;
}

export interface DirectoryTreeNode {
    type: 'file' | 'directory';
    name: string;
    path: string[];
    children?: DirectoryTreeNode[];
    document?: {
        id: number;
        filename: string;
        path_array: string[];
        is_ingested: boolean;
        created_at: string;
        updated_at?: string;
    };
}

export interface DirectoryTreeResponse {
    children: DirectoryTreeNode[];
}

export interface UploadResponse {
    success: boolean;
    message: string;
    path?: string;
}

export interface ChatRequest {
    message: string;
    conversation_id?: string | null;
    user_id: string;
}

export interface ChatResponse {
    message: string;
    conversation_id: string;
}

export interface Message {
    message_id: number;
    conversation_id: string;  // UUID string
    content: string;
    role: 'user' | 'assistant';
    created_at: string;
}

export interface Conversation {
    id: number;
    user_id: string;
    conversation_id: string;  // UUID string
    last_message_id: number | null;
    created_at: string;
    updated_at: string;
}

export interface ConversationResponse {
    messages: Message[];
}

export interface StreamingEvent {
    event: 'search_start' | 'search_complete' | 'thinking_start' | 'thinking_complete' | 'token' | 'complete';
    data?: string;
}

export interface StreamingEventCallbacks {
    onSearchStart?: () => void;
    onSearchComplete?: () => void;
    onThinkingStart?: () => void;
    onThinkingComplete?: () => void;
    onToken?: (token: string) => void;
    onComplete?: () => void;
    onError?: (error: Error) => void;
}

export interface StreamingChatRequest {
    message: string;
    user_id: string;
    conversation_id?: string;
}

class ApiService {
    private api = axios.create({
        baseURL: API_BASE_URL,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    async listFiles(userId: number): Promise<DirectoryTreeResponse> {
        const response = await this.api.get<DirectoryTreeResponse>(`/documents/${userId}`);
        return response.data;
    }

    async ingestFiles(userId: number, files: number[]): Promise<void> {
        await this.api.post(`/documents/ingest?user_id=${userId}`, { document_ids: files });
    }

    async uploadFile(userId: number, file: File): Promise<UploadResponse> {
        const formData = new FormData();
        formData.append('files', file);

        const response = await this.api.post<UploadResponse>(
            `/documents/upload?user_id=${userId}`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 100));
                    console.log(`Upload Progress: ${percentCompleted}%`);
                },
            }
        );

        // Ensure we have a properly formatted response
        const data = response.data;
        if (!data || typeof data.success !== 'boolean') {
            throw new Error('Invalid response format from server');
        }
        return data;
    }

    async uploadMultipleFiles(userId: number, files: File[]): Promise<UploadResponse[]> {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await this.api.post<UploadResponse[]>(
            `/documents/upload?user_id=${userId}`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 100));
                    console.log(`Upload Progress: ${percentCompleted}%`);
                },
            }
        );

        return response.data;
    }

    async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
        const response = await this.api.post<ChatResponse>('/chat', request);
        return response.data;
    }

    async getConversations(): Promise<Conversation[]> {
        const response = await this.api.get<Conversation[]>('/chat/conversations/2');
        return response.data;
    }

    async createConversation(user_id: number): Promise<Conversation> {
        const response = await this.api.post<Conversation>(`/chat/conversation/${user_id}`);
        return response.data;
    }

    async getConversation(conversationId: string): Promise<ConversationResponse> {
        const response = await this.api.get<ConversationResponse>(`/chat/conversation/${conversationId}`);
        return response.data;
    }

    async deleteConversation(conversationId: string): Promise<Conversation> {
        const response = await this.api.delete<Conversation>(`/chat/conversation/${conversationId}`);
        return response.data;
    }

    async moveFile(userId: number, documentId: number, newPath: string): Promise<FileInfo> {
        const response = await this.api.put<FileInfo>(
            `/documents/move/${documentId}?user_id=${userId}&new_path=${encodeURIComponent(newPath)}`
        );
        return response.data;
    }

    async deleteFile(userId: number, documentId: number): Promise<void> {
        await this.api.delete(`/documents/${documentId}?user_id=${userId}`);
    }

    async streamChat(request: StreamingChatRequest, callbacks: StreamingEventCallbacks): Promise<void> {
        try {
            const response = await fetch(`${API_BASE_URL}/chat/stream/rag`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No reader available');

            let buffer = '';
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // Convert chunk to text and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete lines from buffer
                const lines = buffer.split('\n');
                // Keep the last potentially incomplete line in buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

                    try {
                        const jsonStr = trimmedLine.slice(6); // Remove 'data: ' prefix
                        console.log('Processing line:', jsonStr);
                        const eventData = JSON.parse(jsonStr) as StreamingEvent;

                        switch (eventData.event) {
                            case 'search_start':
                                callbacks.onSearchStart?.();
                                break;
                            case 'search_complete':
                                callbacks.onSearchComplete?.();
                                break;
                            case 'thinking_start':
                                callbacks.onThinkingStart?.();
                                break;
                            case 'thinking_complete':
                                callbacks.onThinkingComplete?.();
                                break;
                            case 'token':
                                if (eventData.data) {
                                    console.log('Processing single token:', eventData.data);
                                    callbacks.onToken?.(eventData.data);
                                }
                                break;
                            case 'complete':
                                // Process any remaining buffer before completing
                                if (buffer.trim()) {
                                    const remainingLine = buffer.trim();
                                    if (remainingLine.startsWith('data: ')) {
                                        try {
                                            const remainingData = JSON.parse(remainingLine.slice(6)) as StreamingEvent;
                                            if (remainingData.event === 'token' && remainingData.data) {
                                                callbacks.onToken?.(remainingData.data);
                                            }
                                        } catch (e) {
                                            console.warn('Error processing remaining buffer:', e);
                                        }
                                    }
                                }
                                callbacks.onComplete?.();
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing streaming event:', error, 'Line:', line);
                        callbacks.onError?.(new Error('Failed to parse streaming event'));
                    }
                }
            }
        } catch (error) {
            console.error('Streaming chat error:', error);
            callbacks.onError?.(error instanceof Error ? error : new Error('Unknown streaming error'));
        }
    }
}

export const apiService = new ApiService(); 