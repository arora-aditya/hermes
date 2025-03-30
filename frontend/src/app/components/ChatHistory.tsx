import { ChatMessage } from "./ChatMessage";

interface Message {
    content: string;
    role: 'user' | 'assistant';
}

interface ChatHistoryProps {
    messages: Message[];
}

export function ChatHistory({ messages }: ChatHistoryProps) {
    return (
        <div className="flex-1 h-[calc(100vh-200px)] overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
            {messages.map((message, index) => (
                <ChatMessage
                    key={index}
                    content={message.content}
                    role={message.role}
                />
            ))}
        </div>
    );
} 