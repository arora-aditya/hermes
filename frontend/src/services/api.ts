import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface FileInfo {
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

    async ingestFiles(files: string[]): Promise<void> {
        await this.api.post('/ingest', { files });
    }

    async uploadFile(file: File): Promise<UploadResponse> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post<UploadResponse>(
            `${API_BASE_URL}/upload`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 100));
                    // You can use this for progress tracking if needed
                    console.log(`Upload Progress: ${percentCompleted}%`);
                },
            }
        );
        return response.data;
    }

    async uploadMultipleFiles(files: File[]): Promise<UploadResponse[]> {
        const uploadPromises = files.map(file => this.uploadFile(file));
        return Promise.all(uploadPromises);
    }
}

export const apiService = new ApiService(); 