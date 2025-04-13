'use client';

import { FileUploadModal } from './components/FileUploadModal';
import { useFiles } from '@/hooks/useFiles';
import { ChatHistory } from './components/ChatHistory';
import { ChatInput } from './components/ChatInput';
import { useChat } from '@/hooks/useChat';
import { useEffect } from 'react';
import { ConversationHistory } from './components/ConversationHistory';

export default function Home() {
  const userId = 2;
  const { files, selectedFiles, loading, toggleFileSelection, handleIndex, fetchFiles, moveFile, deleteFile } = useFiles(userId);
  const { conversations, isLoadingConversations, messages, isLoading, sendMessage, resetConversation, setCurrentConversation, createConversation, deleteConversation, conversationId } = useChat(userId);

  useEffect(() => {
    resetConversation();
  }, []);

  return (
    <div className="flex h-screen">
      <ConversationHistory
        conversations={conversations}
        isLoadingConversations={isLoadingConversations}
        onSelectConversation={setCurrentConversation}
        onDeleteConversation={deleteConversation}
        currentConversationId={conversationId || undefined}
        files={files}
        selectedFiles={selectedFiles}
        loading={loading}
        toggleFileSelection={toggleFileSelection}
        handleIndex={handleIndex}
        moveFile={moveFile}
        deleteFile={deleteFile}
      />
      <div className="flex-1 flex flex-col">
        <div className="flex justify-end p-4 border-b gap-2">
          <button
            onClick={createConversation}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            New Conversation
          </button>
          <FileUploadModal userId={userId} onUploadComplete={fetchFiles} />
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
