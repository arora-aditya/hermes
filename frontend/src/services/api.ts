import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface FileInfo {
    id: number;
    filename: string;
    path: string;
    size: number;
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

class ApiService {
    private api = axios.create({
        baseURL: API_BASE_URL,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    async listFiles(): Promise<FileInfo[]> {
        const response = await this.api.get<{ files: FileInfo[] }>('/listfiles');
        return response.data.files;
    }

    async ingestFiles(files: number[]): Promise<void> {
        await this.api.post('/ingest', { document_ids: files });
    }

    async uploadFile(file: File): Promise<UploadResponse> {
        const formData = new FormData();
        formData.append('files', file);

        const response = await this.api.post<UploadResponse>(
            '/uploadfiles',
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

    async uploadMultipleFiles(files: File[]): Promise<UploadResponse[]> {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await this.api.post<UploadResponse[]>(
            '/uploadfiles',
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

    async getConversation(conversationId: string): Promise<ConversationResponse> {
        const response = await this.api.get<ConversationResponse>(`/chat/conversation/${conversationId}`);
        return response.data;
    }
}

export const apiService = new ApiService(); 