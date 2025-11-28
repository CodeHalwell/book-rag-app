import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { BookOpen, Plus, Send, LogOut, ChevronDown, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/context/AuthContext'
import { streamChat } from '@/lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

export default function Chat() {
  const { user, loading, logout } = useAuth()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm BookRAG. Ask me any question about your document collection.",
    },
  ])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState(() => generateSessionId())
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const streamingContentRef = useRef('')

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  const handleNewChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: "Hello! I'm BookRAG. Ask me any question about your document collection.",
      },
    ])
    setSessionId(generateSessionId())
  }

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault()
    
    const query = input.trim()
    if (!query || isStreaming) return

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: query,
    }

    const assistantMessageId = `assistant_${Date.now()}`
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
    }

    // Reset streaming content ref
    streamingContentRef.current = ''

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setInput('')
    setIsStreaming(true)

    try {
      for await (const token of streamChat(query, sessionId)) {
        // Accumulate content in ref to avoid state mutation issues
        streamingContentRef.current += token
        const currentContent = streamingContentRef.current
        
        setMessages((prev) => {
          return prev.map((msg) => 
            msg.id === assistantMessageId 
              ? { ...msg, content: currentContent }
              : msg
          )
        })
      }
    } catch (error) {
      setMessages((prev) => {
        return prev.map((msg) => 
          msg.id === assistantMessageId 
            ? { ...msg, content: 'Sorry, an error occurred. Please try again.' }
            : msg
        )
      })
    } finally {
      setIsStreaming(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border p-4 flex items-center justify-between shadow-lg z-10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <BookOpen className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-xl font-bold tracking-wide">BookRAG</h1>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleNewChat}
            title="New Chat"
            className="text-muted-foreground hover:text-foreground"
          >
            <Plus className="h-5 w-5" />
          </Button>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center space-x-2 px-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{user.name.charAt(0).toUpperCase()}</AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium hidden sm:inline">{user.name}</span>
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Chat Container */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-4 space-y-4 max-w-4xl mx-auto w-full">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex message-appear ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex flex-col space-y-1 max-w-[80%] ${message.role === 'user' ? 'items-end' : ''}`}>
                <div className={`flex items-start space-x-2 ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <Avatar className="h-8 w-8 mt-0.5 shrink-0">
                    <AvatarFallback className={message.role === 'user' ? 'bg-secondary' : 'bg-primary'}>
                      {message.role === 'user' ? <User className="h-4 w-4" /> : 'AI'}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`p-4 ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-none'
                        : 'bg-card border border-border rounded-2xl rounded-tl-none'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                      <div className="prose-chat">
                        <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border bg-card p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              className="flex-1 min-h-14 max-h-32"
              disabled={isStreaming}
            />
            <Button
              type="submit"
              size="icon"
              className="h-14 w-14 shrink-0"
              disabled={!input.trim() || isStreaming}
            >
              <Send className="h-5 w-5" />
            </Button>
          </form>
          <p className="text-center text-xs text-muted-foreground mt-2">
            AI can make mistakes. Please verify information.
          </p>
        </div>
      </div>
    </div>
  )
}
