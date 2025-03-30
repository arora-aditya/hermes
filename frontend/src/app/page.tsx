'use client';

import { FileUploadModal } from './components/FileUploadModal';
import { useFiles } from '@/hooks/useFiles';
import { ChatHistory } from './components/ChatHistory';
import { ChatInput } from './components/ChatInput';
import { useChat } from '@/hooks/useChat';
import { useEffect, useState } from 'react';
import { ConversationHistory } from './components/ConversationHistory';

export default function Home() {
  const { files, selectedFiles, loading, toggleFileSelection, handleIndex, fetchFiles } = useFiles();
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>('34f76c29-cf93-472f-8259-7fd2fd58db7d');
  const { messages, isLoading, sendMessage, resetConversation } = useChat(currentConversationId);

  // Reset conversation on first load
  useEffect(() => {
    resetConversation();
  }, [currentConversationId]);

  const handleConversationSelect = (conversationId: string) => {
    console.log('conversationId', conversationId);
    setCurrentConversationId(conversationId);
  };

  return (
    <div className="flex h-screen">
      <ConversationHistory
        onSelectConversation={handleConversationSelect}
        currentConversationId={currentConversationId}
        files={files}
        selectedFiles={selectedFiles}
        loading={loading}
        toggleFileSelection={toggleFileSelection}
        handleIndex={handleIndex}
      />
      <div className="flex-1 flex flex-col">
        <div className="flex justify-end p-4 border-b">
          <FileUploadModal onUploadComplete={fetchFiles} />
        </div>
        <div className="flex-1 flex flex-col relative">
          <div className="absolute inset-0 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              <ChatHistory messages={messages} />
            </div>
            <div className="p-4 border-t">
              <ChatInput onSendMessage={sendMessage} disabled={isLoading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
