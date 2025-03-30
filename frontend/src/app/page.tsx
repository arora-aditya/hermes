'use client';

import { FileList } from './components/FileList';
import { FileUploadModal } from './components/FileUploadModal';
import { useFiles } from '@/hooks/useFiles';
import { ChatHistory } from './components/ChatHistory';
import { ChatInput } from './components/ChatInput';
import { useChat } from '@/hooks/useChat';
import { useEffect } from 'react';

export default function Home() {
  const { files, selectedFiles, loading, toggleFileSelection, handleIndex, fetchFiles } = useFiles();
  const { messages, isLoading, sendMessage, resetConversation } = useChat('34f76c29-cf93-472f-8259-7fd2fd58db7d');

  // Reset conversation on first load
  useEffect(() => {
    resetConversation();
  }, []);

  return (
    <div className="flex min-h-screen">
      <FileList
        files={files}
        selectedFiles={selectedFiles}
        loading={loading}
        toggleFileSelection={toggleFileSelection}
        handleIndex={handleIndex}
      />
      <div className="flex-1 flex flex-col">
        <div className="flex justify-end p-4">
          <FileUploadModal onUploadComplete={fetchFiles} />
        </div>
        <div className="flex-1 flex flex-col">
          <ChatHistory messages={messages} />
          <ChatInput onSendMessage={sendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}
