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
}

export const apiService = new ApiService(); 