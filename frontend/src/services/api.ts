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
}

export const apiService = new ApiService(); 