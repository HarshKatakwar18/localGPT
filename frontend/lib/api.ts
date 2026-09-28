import {
  getAccessToken,
  removeAccessToken,
  setAccessToken,
} from "@/lib/auth";

import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
} from "@/types/auth";

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

/* =========================
   Authentication Errors
========================= */

export class AuthenticationError extends Error {
  constructor(message = "Your session has expired") {
    super(message);
    this.name = "AuthenticationError";
  }
}

/*
 * Only one refresh request is allowed to run at a time.
 *
 * If multiple API requests receive 401 at the same time,
 * they will all wait for this same Promise instead of
 * creating multiple refresh sessions.
 */
let refreshPromise: Promise<string> | null = null;

/* =========================
   Error Handling
========================= */

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

/* =========================
   Refresh Access Token
========================= */

async function refreshAccessToken(): Promise<string> {
  /*
   * If another request is already refreshing the session,
   * wait for that same refresh operation.
   */
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/refresh`,
        {
          method: "POST",
          credentials: "include",
          cache: "no-store",
        },
      );

      if (!response.ok) {
        const message = await parseError(response);

        removeAccessToken();

        throw new AuthenticationError(message);
      }

      const data = (await response.json()) as AuthResponse;

      if (!data.access_token) {
        removeAccessToken();

        throw new AuthenticationError(
          "The server did not return a new access token",
        );
      }

      setAccessToken(data.access_token);

      return data.access_token;
    } catch (error) {
      removeAccessToken();

      if (error instanceof AuthenticationError) {
        throw error;
      }

      throw new AuthenticationError(
        "Unable to refresh your session",
      );
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/* =========================
   Authenticated Request
========================= */

async function authenticatedFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  let accessToken = getAccessToken();

  /*
   * No access token in localStorage does NOT automatically
   * mean the user must log in.
   *
   * The refresh-token cookie may still represent a valid session.
   */
  if (!accessToken) {
    accessToken = await refreshAccessToken();
  }

  const headers = new Headers(options.headers);

  headers.set(
    "Authorization",
    `Bearer ${accessToken}`,
  );

  let response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  /*
   * If the access token expired, try to refresh the session
   * and retry the original request exactly once.
   */
  if (response.status === 401) {
    /*
     * Another request may already have refreshed the token
     * between our original request and this 401.
     *
     * If so, use that newer token instead of refreshing again.
     */
    const latestAccessToken = getAccessToken();

    if (
      latestAccessToken &&
      latestAccessToken !== accessToken
    ) {
      const retryHeaders = new Headers(options.headers);

      retryHeaders.set(
        "Authorization",
        `Bearer ${latestAccessToken}`,
      );

      response = await fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: "include",
      });

      return response;
    }

    const newAccessToken = await refreshAccessToken();

    const retryHeaders = new Headers(options.headers);

    retryHeaders.set(
      "Authorization",
      `Bearer ${newAccessToken}`,
    );

    response = await fetch(url, {
      ...options,
      headers: retryHeaders,
      credentials: "include",
    });
  }

  return response;
}

/* =========================
   Authentication
========================= */

export async function registerUser(
  request: RegisterRequest,
): Promise<User> {
  const response = await fetch(
    `${API_BASE_URL}/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as User;
}

export async function loginUser(
  request: LoginRequest,
): Promise<AuthResponse> {
  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(request),
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as AuthResponse;
}

export async function logoutUser(): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/auth/logout`,
      {
        method: "POST",
        credentials: "include",
        cache: "no-store",
      },
    );

    if (!response.ok) {
      throw new Error(await parseError(response));
    }
  } finally {
    /*
     * The access token is only a client-side representation
     * of the current authenticated session.
     *
     * Always remove it when logout is requested, even if
     * the backend logout request fails.
     */
    removeAccessToken();
  }
}

/* =========================
   Conversations
========================= */

export async function getThreads(): Promise<Conversation[]> {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/threads`,
    {
      method: "GET",
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as Conversation[];
}

export async function getThread(
  threadId: string,
): Promise<ThreadMessage[]> {
  const response = await authenticatedFetch(
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

/* =========================
   Chat Streaming
========================= */

export async function streamChat({
  message,
  threadId,
  onChunk,
}: StreamChatParams): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE_URL}/chat/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        thread_id: threadId,
      }),
    },
  );

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

/* =========================
   Rename
========================= */

export async function renameThread(
  threadId: string,
  title: string,
): Promise<RenameThreadResponse> {
  const response = await authenticatedFetch(
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

/* =========================
   Delete
========================= */

export async function deleteThread(
  threadId: string,
): Promise<DeleteThreadResponse> {
  const response = await authenticatedFetch(
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
