'use client';

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useFileUpload } from '@/hooks/useFileUpload';
import { Progress } from '@/components/ui/progress';
import { Upload } from 'lucide-react';

interface FileUploadModalProps {
    userId: number;
    onUploadComplete: () => void;
}

export function FileUploadModal({ userId, onUploadComplete }: FileUploadModalProps) {
    const { isOpen, setIsOpen, uploadState, handleUpload } = useFileUpload(userId, onUploadComplete);

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Files
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Upload Files</DialogTitle>
                    <DialogDescription>
                        Select files to upload to your workspace
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-1 gap-3">
                        <input
                            type="file"
                            multiple
                            className="block w-full text-sm text-slate-500
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-md file:border-0
                                file:text-sm file:font-semibold
                                file:bg-primary file:text-primary-foreground
                                hover:file:bg-primary/90"
                            onChange={(e) => handleUpload(e.target.files)}
                            disabled={uploadState.isUploading}
                        />
                        {uploadState.isUploading && (
                            <div className="space-y-2">
                                <Progress value={uploadState.progress} className="w-full" />
                                <div className="flex flex-col gap-1">
                                    <p className="text-sm text-muted-foreground text-center">
                                        Uploading {uploadState.totalFiles} file{uploadState.totalFiles !== 1 ? 's' : ''}...
                                    </p>
                                    <p className="text-xs text-muted-foreground text-center">
                                        Progress: {uploadState.progress}%
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
} 