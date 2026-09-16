"use client";

import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import SettingsModal from "@/components/SettingsModal";
import { ThemeId } from "@/lib/themes";

import {
  deleteThread as deleteThreadApi,
  getThread,
  getThreads,
  renameThread,
  streamChat,
} from "@/lib/api";

import type { ChatMessage, ChatThread } from "@/types/chat";

function createThreadId(): string {
  return crypto.randomUUID();
}

function createThreadTitle(message: string): string {
  const title = message.trim();

  if (title.length <= 35) {
    return title;
  }

  return `${title.slice(0, 35)}...`;
}

function SidebarIcon({ children }: { children: ReactNode }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  );
}

function TooltipButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <div className="group relative">
      <button
        type="button"
        onClick={onClick}
        aria-label={label}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-[#b4b4b4] transition hover:bg-[var(--surface)] hover:text-white"
      >
        {children}
      </button>

      <div className="pointer-events-none absolute left-1/2 top-full z-50 mt-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-[#111] px-2.5 py-1.5 text-xs text-white opacity-0 shadow-xl transition-opacity duration-150 group-hover:opacity-100">
        {label}
      </div>
    </div>
  );
}

export default function Home() {
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const [theme, setTheme] = useState<ThemeId>("midnight");
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);

  const [editingTitle, setEditingTitle] = useState("");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    void initializeApp();
  }, []);

  useEffect(() => {
  const savedTheme = localStorage.getItem(
    "localgpt-theme",
  ) as ThemeId | null;

  if (savedTheme) {
    setTheme(savedTheme);
  }
}, []);

useEffect(() => {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("localgpt-theme", theme);
}, [theme]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function initializeApp() {
    try {
      const backendThreads = await getThreads();

      const convertedThreads: ChatThread[] = backendThreads.map((thread) => ({
        id: thread.thread_id,
        title: thread.title,
      }));

      setThreads(convertedThreads);

      const savedThreadId = localStorage.getItem("localgpt-thread-id");

      if (
        savedThreadId &&
        convertedThreads.some((thread) => thread.id === savedThreadId)
      ) {
        setActiveThreadId(savedThreadId);
        await loadThread(savedThreadId);
      }
    } catch (error) {
      console.error("Failed to initialize LocalGPT:", error);
    }
  }

  async function refreshThreads() {
    try {
      const backendThreads = await getThreads();

      setThreads(
        backendThreads.map((thread) => ({
          id: thread.thread_id,
          title: thread.title,
        })),
      );
    } catch (error) {
      console.error("Failed to refresh conversations:", error);
    }
  }

  async function loadThread(threadId: string) {
    try {
      const loadedMessages = await getThread(threadId);

      const convertedMessages: ChatMessage[] = loadedMessages.map(
        (message, index) => ({
          id: `${threadId}-${index}`,
          role: message.role,
          content: message.content,
        }),
      );

      setMessages(convertedMessages);
    } catch (error) {
      console.error("Failed to load conversation:", error);
      setMessages([]);
    }
  }

  function createNewChat() {
    const newThreadId = createThreadId();

    setActiveThreadId(newThreadId);
    setMessages([]);
    setInput("");
    setOpenMenuId(null);
    setEditingThreadId(null);
    setEditingTitle("");

    localStorage.setItem("localgpt-thread-id", newThreadId);

    window.setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  }

  async function selectThread(threadId: string) {
    if (isLoading) {
      return;
    }

    setActiveThreadId(threadId);
    setOpenMenuId(null);
    setEditingThreadId(null);

    localStorage.setItem("localgpt-thread-id", threadId);

    await loadThread(threadId);
  }

  function startEditingThread(thread: ChatThread) {
    setOpenMenuId(null);
    setEditingThreadId(thread.id);
    setEditingTitle(thread.title);
  }

  async function saveEditedTitle(threadId: string) {
    const title = editingTitle.trim();

    if (!title) {
      setEditingThreadId(null);
      setEditingTitle("");
      return;
    }

    try {
      await renameThread(threadId, title);

      setThreads((previousThreads) =>
        previousThreads.map((thread) =>
          thread.id === threadId
            ? {
                ...thread,
                title,
              }
            : thread,
        ),
      );
    } catch (error) {
      console.error("Failed to rename conversation:", error);
    } finally {
      setEditingThreadId(null);
      setEditingTitle("");
    }
  }

  async function handleDeleteThread(threadId: string) {
    const confirmed = window.confirm("Delete this conversation permanently?");

    if (!confirmed) {
      return;
    }

    try {
      await deleteThreadApi(threadId);

      setThreads((previousThreads) =>
        previousThreads.filter((thread) => thread.id !== threadId),
      );

      if (activeThreadId === threadId) {
        createNewChat();
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    } finally {
      setOpenMenuId(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedInput = input.trim();

    if (!trimmedInput || isLoading) {
      return;
    }

    let currentThreadId = activeThreadId;

    if (!currentThreadId) {
      currentThreadId = createThreadId();
      setActiveThreadId(currentThreadId);
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedInput,
    };

    const assistantMessageId = crypto.randomUUID();

    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
    };

    const isFirstMessage = messages.length === 0;

    setMessages((previousMessages) => [
      ...previousMessages,
      userMessage,
      assistantMessage,
    ]);

    setInput("");
    setIsLoading(true);

    if (isFirstMessage) {
      setThreads((previousThreads) => [
        {
          id: currentThreadId,
          title: createThreadTitle(trimmedInput),
        },
        ...previousThreads.filter((thread) => thread.id !== currentThreadId),
      ]);
    }

    try {
      await streamChat({
        message: trimmedInput,
        threadId: currentThreadId,
        onChunk: (chunk) => {
          setMessages((previousMessages) =>
            previousMessages.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: message.content + chunk,
                  }
                : message,
            ),
          );
        },
      });

      await refreshThreads();
    } catch (error) {
      console.error("Streaming failed:", error);

      setMessages((previousMessages) =>
        previousMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content:
                  "Sorry, something went wrong while contacting LocalGPT.",
              }
            : message,
        ),
      );
    } finally {
      setIsLoading(false);
    }
  }

  function handleInputChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(event.target.value);

    const textarea = event.target;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (!isLoading && input.trim()) {
        event.currentTarget.form?.requestSubmit();
      }
    }
  }

  return (
    <main className="flex h-screen overflow-hidden bg-[var(--background)] text-[var(--text-primary)]">
      {/* Sidebar */}
      <aside
        className={`flex h-screen shrink-0 flex-col bg-[var(--sidebar)] transition-all duration-200 ${
          isSidebarOpen ? "w-[260px]" : "w-0 overflow-hidden"
        }`}
      >
        <div className="flex h-full min-h-0 flex-col px-2 py-3">
          <div className="mb-3 flex items-center justify-between px-2">
            <button
              type="button"
              onClick={createNewChat}
              className="flex items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-white transition hover:bg-[var(--surface)]"
            >
              <span className="text-lg">✦</span>
              <span>LocalGPT</span>
            </button>

            <TooltipButton
              label="Close sidebar"
              onClick={() => setIsSidebarOpen(false)}
            >
              <SidebarIcon>
                <rect x="3" y="4" width="18" height="16" rx="3" />
                <path d="M9 4v16" />
              </SidebarIcon>
            </TooltipButton>
          </div>

          <button
            type="button"
            onClick={createNewChat}
            className="mb-3 flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-white transition hover:bg-[var(--surface)]"
          >
            <span className="text-xl">＋</span>
            <span>New chat</span>
          </button>

          <div className="mb-2 px-3 text-xs font-medium text-[#8e8e8e]">
            Your conversations
          </div>

          <div className="scroll-area min-h-0 flex-1 overflow-y-auto">
            <div className="space-y-1">
              {threads.map((thread) => {
                const isActive = thread.id === activeThreadId;

                const isEditing = editingThreadId === thread.id;

                return (
                  <div
                    key={thread.id}
                    className={`group relative flex items-center rounded-lg transition ${
                      isActive ? "bg-[var(--surface)]" : "hover:bg-[#2a2a2a]"
                    }`}
                  >
                    {isEditing ? (
                      <input
                        autoFocus
                        value={editingTitle}
                        onChange={(event) =>
                          setEditingTitle(event.target.value)
                        }
                        onBlur={() => void saveEditedTitle(thread.id)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            void saveEditedTitle(thread.id);
                          }

                          if (event.key === "Escape") {
                            setEditingThreadId(null);
                            setEditingTitle("");
                          }
                        }}
                        className="min-w-0 flex-1 rounded-md bg-[#404040] px-3 py-2 text-sm text-white outline-none"
                      />
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => void selectThread(thread.id)}
                          className="min-w-0 flex-1 truncate px-3 py-3 text-left text-sm text-[var(--text-primary)]"
                        >
                          {thread.title || "New conversation"}
                        </button>

                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();

                            setOpenMenuId((current) =>
                              current === thread.id ? null : thread.id,
                            );
                          }}
                          aria-label="Conversation options"
                          className="mr-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-lg leading-none text-[#b4b4b4] opacity-0 transition hover:bg-[#444] hover:text-white group-hover:opacity-100"
                        >
                          ⋯
                        </button>

                        {openMenuId === thread.id && (
                          <div className="absolute right-1 top-10 z-50 w-48 rounded-xl border border-[#454545] bg-[var(--surface)] p-1.5 shadow-2xl">
                            <button
                              type="button"
                              onClick={() => startEditingThread(thread)}
                              className="flex w-full items-center rounded-lg px-3 py-2.5 text-left text-sm text-[var(--text-primary)] transition hover:bg-[#424242]"
                            >
                              <SidebarIcon>
                                <path d="M12 20h9" />
                                <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" />
                              </SidebarIcon>

                              <span className="ml-3">Rename</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => void handleDeleteThread(thread.id)}
                              className="flex w-full items-center rounded-lg px-3 py-2.5 text-left text-sm text-red-400 transition hover:bg-[#424242]"
                            >
                              <SidebarIcon>
                                <path d="M3 6h18" />
                                <path d="M8 6V4h8v2" />
                                <path d="M19 6l-1 14H6L5 6" />
                                <path d="M10 11v5" />
                                <path d="M14 11v5" />
                              </SidebarIcon>

                              <span className="ml-3">Delete chat</span>
                            </button>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-3 border-t border-[var(--border)] px-3 pt-3">
            <button
              type="button"
              onClick={() => setSettingsOpen(true)}
              className="mb-3 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-[var(--text-primary)] transition hover:bg-[var(--surface)]"
            >
              <SidebarIcon>
                <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" />
                <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-1.8 1.8-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V20h-2.54v-.1a1.7 1.7 0 0 0-1.03-1.56 1.7 1.7 0 0 0-1.88.34l-.06.06-1.8-1.8.06-.06A1.7 1.7 0 0 0 8.12 15a1.7 1.7 0 0 0-1.56-1.03H6v-2.54h.56A1.7 1.7 0 0 0 8.12 10a1.7 1.7 0 0 0-.34-1.88l-.06-.06 1.8-1.8.06.06a1.7 1.7 0 0 0 1.88.34 1.7 1.7 0 0 0 1.03-1.56V5h2.54v.1a1.7 1.7 0 0 0 1.03 1.56 1.7 1.7 0 0 0 1.88-.34l.06-.06 1.8 1.8-.06.06A1.7 1.7 0 0 0 19.4 10a1.7 1.7 0 0 0 1.56 1.03H21v2.54h-.04A1.7 1.7 0 0 0 19.4 15Z" />
              </SidebarIcon>
              <span>Settings</span>
            </button>

            <div className="flex items-center gap-2 text-xs text-[#8e8e8e]">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              LocalGPT is running locally
            </div>
          </div>
        </div>
      </aside>

      {/* Main section */}
      <section className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            {!isSidebarOpen && (
              <TooltipButton
                label="Open sidebar"
                onClick={() => setIsSidebarOpen(true)}
              >
                <SidebarIcon>
                  <rect x="3" y="4" width="18" height="16" rx="3" />
                  <path d="M9 4v16" />
                </SidebarIcon>
              </TooltipButton>
            )}

            <button
              type="button"
              onClick={createNewChat}
              className="flex items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-[var(--text-primary)] transition hover:bg-[var(--surface)]"
            >
              <span>LocalGPT</span>
              <span className="text-xs text-[#8e8e8e]">⌄</span>
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={createNewChat}
              className="rounded-lg px-3 py-2 text-sm text-[#b4b4b4] transition hover:bg-[var(--surface)] hover:text-white"
            >
              New chat
            </button>

            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--accent)] text-sm font-semibold text-white">
              H
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="scroll-area min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-3xl px-4 py-8">
            {messages.length === 0 ? (
              <div className="flex min-h-[calc(100vh-220px)] flex-col items-center justify-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--surface)] text-3xl">
                  ✦
                </div>

                <h1 className="mb-2 text-2xl font-semibold text-white">
                  How can I help you today?
                </h1>

                <p className="text-center text-sm text-[#8e8e8e]">
                  Ask anything and start a conversation with LocalGPT.
                </p>
              </div>
            ) : (
              <div className="space-y-8">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-4 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-sm font-semibold text-white">
                        ✦
                      </div>
                    )}

                    <div
                      className={`max-w-[85%] whitespace-pre-wrap text-[15px] leading-7 ${
                        message.role === "user"
                          ? "rounded-3xl bg-[var(--surface)] px-5 py-3 text-white"
                          : "pt-1 text-[var(--text-primary)]"
                      }`}
                    >
                      {message.content ||
                        (isLoading && message.role === "assistant" ? "▍" : "")}
                    </div>

                    {message.role === "user" && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#565656] text-sm font-semibold text-white">
                        H
                      </div>
                    )}
                  </div>
                ))}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Composer */}
        <div className="shrink-0 px-4 pb-5 pt-3">
          <div className="mx-auto w-full max-w-3xl">
            <form
              onSubmit={handleSubmit}
              className="relative rounded-3xl bg-[var(--surface)] shadow-sm transition focus-within:bg-[#353535]"
            >
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Message LocalGPT"
                rows={1}
                disabled={isLoading}
                className="max-h-[180px] min-h-[56px] w-full resize-none rounded-3xl border-0 bg-transparent px-5 pb-14 pt-4 text-[15px] text-white placeholder:text-[#8e8e8e] outline-none ring-0 focus:border-0 focus:outline-none focus:ring-0 disabled:cursor-not-allowed"
              />

              <div className="absolute bottom-3 left-4">
                <button
                  type="button"
                  title="Attach files"
                  aria-label="Attach files"
                  className="rounded-full p-1 text-xl text-[#b4b4b4] transition hover:bg-[#444] hover:text-white"
                >
                  ＋
                </button>
              </div>

              <div className="absolute bottom-3 right-3">
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  title="Send message"
                  aria-label="Send message"
                  className={`flex h-9 w-9 items-center justify-center rounded-full text-lg transition ${
                    isLoading || !input.trim()
                      ? "cursor-not-allowed bg-[#676767] text-[#aaa]"
                      : "bg-white text-black hover:bg-[#d9d9d9]"
                  }`}
                >
                  ↑
                </button>
              </div>
            </form>

            <p className="mt-2 text-center text-xs text-[#8e8e8e]">
              LocalGPT can make mistakes. Check important information.
            </p>
          </div>
        </div>
      </section>

      <SettingsModal
        open={settingsOpen}
        theme={theme}
        onThemeChange={setTheme}
        onClose={() => setSettingsOpen(false)}
      />
    </main>
  );
}
