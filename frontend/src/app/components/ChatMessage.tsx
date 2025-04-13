import { cn } from "@/lib/utils";

interface ChatMessageProps {
    content: string;
    role: 'user' | 'assistant';
}

export function ChatMessage({ content, role }: ChatMessageProps) {
    if (content === '') {
        return null;
    }
    return (
        <div className={cn(
            "flex w-full",
            role === 'user' ? 'justify-end' : 'justify-start'
        )}>
            <div className={cn(
                "max-w-[80%] rounded-lg px-4 py-2 mb-2",
                role === 'user'
                    ? 'bg-primary text-primary-foreground ml-auto'
                    : 'bg-muted'
            )}>
                {content}
            </div>
        </div>
    );
} 