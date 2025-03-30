import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState, KeyboardEvent, ChangeEvent } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
    const [message, setMessage] = useState("");

    const handleSend = () => {
        if (message.trim()) {
            onSendMessage(message.trim());
            setMessage("");
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex gap-2 p-4 border-t">
            <Input
                value={message}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                disabled={disabled}
                className="flex-1"
            />
            <Button
                onClick={handleSend}
                disabled={disabled || !message.trim()}
                size="icon"
            >
                <Send className="h-4 w-4" />
            </Button>
        </div>
    );
} 