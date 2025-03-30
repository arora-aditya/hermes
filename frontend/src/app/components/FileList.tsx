'use client';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { useFiles } from '@/hooks/useFiles';

export function FileList() {
    const { files, selectedFiles, loading, toggleFileSelection, handleIndex } = useFiles();

    if (loading) {
        return <div className="p-4">Loading files...</div>;
    }

    return (
        <div className="w-64 border-r h-screen p-4">
            <h2 className="text-lg font-semibold mb-4">Files</h2>
            <ScrollArea className="h-[calc(100vh-200px)]">
                <div className="space-y-2">
                    {files.map((file) => (
                        <div key={file.path} className="flex items-center space-x-2">
                            <Checkbox
                                checked={selectedFiles.has(file.path)}
                                onCheckedChange={() => toggleFileSelection(file.path)}
                            />
                            <span className="text-sm truncate" title={file.filename}>
                                {file.filename}
                            </span>
                        </div>
                    ))}
                </div>
            </ScrollArea>

            {selectedFiles.size > 0 && (
                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button className="w-full mt-4">
                            Index Selected ({selectedFiles.size})
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Index Selected Files</AlertDialogTitle>
                            <AlertDialogDescription>
                                Are you sure you want to index {selectedFiles.size} selected files?
                                This action cannot be undone.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={handleIndex}>
                                Continue
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            )}
        </div>
    );
} 