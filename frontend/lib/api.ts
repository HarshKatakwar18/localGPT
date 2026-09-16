const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type StreamChatParams = {
  message: string;
  threadId: string;
  onChunk: (chunk: string) => void;
};

export type ThreadMessage = {
  role: "user" | "assistant";
  content: string;
};

export type Conversation = {
  thread_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

type ThreadResponse = {
  thread_id: string;
  messages: ThreadMessage[];
};

type RenameThreadResponse = {
  thread_id: string;
  title: string;
};

type DeleteThreadResponse = {
  message: string;
  thread_id: string;
};

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (typeof data?.message === "string") {
      return data.message;
    }
  } catch {
    // Ignore invalid or empty error responses.
  }

  return `Request failed with status ${response.status}`;
}

export async function getThreads(): Promise<Conversation[]> {
  const response = await fetch(`${API_BASE_URL}/threads`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as Conversation[];
}

export async function getThread(threadId: string): Promise<ThreadMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/threads/${encodeURIComponent(threadId)}`,
    {
      method: "GET",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  const data = (await response.json()) as ThreadResponse;

  return data.messages;
}

export async function streamChat({
  message,
  threadId,
  onChunk,
}: StreamChatParams): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      thread_id: threadId,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (!response.body) {
    throw new Error("The backend did not return a stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        break;
      }

      const chunk = decoder.decode(value, {
        stream: true,
      });

      if (chunk) {
        onChunk(chunk);
      }
    }

    const remainingChunk = decoder.decode();

    if (remainingChunk) {
      onChunk(remainingChunk);
    }
  } finally {
    reader.releaseLock();
  }
}

export async function renameThread(
  threadId: string,
  title: string,
): Promise<RenameThreadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/threads/${encodeURIComponent(threadId)}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title.trim(),
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as RenameThreadResponse;
}

export async function deleteThread(
  threadId: string,
): Promise<DeleteThreadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/threads/${encodeURIComponent(threadId)}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as DeleteThreadResponse;
}
