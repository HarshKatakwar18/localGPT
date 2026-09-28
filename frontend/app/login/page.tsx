"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { loginUser } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsLoading(true);

    try {
      const response = await loginUser({
        email: email.trim(),
        password,
      });

      setAccessToken(response.access_token);

      router.replace("/");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to login",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#171717] px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-[#333] bg-[#212121] p-8 shadow-2xl">

        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold">
            Welcome to LocalGPT
          </h1>

          <p className="mt-2 text-sm text-[#9b9b9b]">
            Login to continue
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-2 block text-sm font-medium"
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your email"
              className="w-full rounded-xl border border-[#444] bg-[#2a2a2a] px-4 py-3 text-white outline-none transition focus:border-[#10a37f]"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              className="w-full rounded-xl border border-[#444] bg-[#2a2a2a] px-4 py-3 text-white outline-none transition focus:border-[#10a37f]"
            />
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-[#10a37f] px-4 py-3 font-medium text-white transition hover:bg-[#0d8f70] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-[#9b9b9b]">
          Don&apos;t have an account?{" "}
          <button
            type="button"
            onClick={() => router.push("/register")}
            className="font-medium text-[#10a37f] hover:underline"
          >
            Create one
          </button>
        </div>

      </div>
    </main>
  );
}