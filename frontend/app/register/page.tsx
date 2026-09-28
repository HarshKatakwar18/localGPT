"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { registerUser } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");

    if (!name.trim()) {
      setError("Please enter your name.");
      return;
    }

    if (!email.trim()) {
      setError("Please enter your email.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);

    try {
      await registerUser({
        name: name.trim(),
        email: email.trim(),
        password,
      });

      router.push("/login");
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-dvh overflow-y-auto bg-[var(--background)] text-[var(--text-primary)]">
      <div className="flex min-h-dvh items-center justify-center px-4 py-4 sm:px-6 sm:py-5">
        <div className="w-full max-w-md">

          {/* Header */}
          <div className="mb-4 text-center">
            <div className="mb-2 flex justify-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#10a37f] text-xl font-semibold text-white">
                ✦
              </div>
            </div>

            <h1 className="text-2xl font-semibold sm:text-3xl">
              Create your LocalGPT account
            </h1>

            <p className="mt-1.5 text-sm text-[var(--text-secondary)]">
              Start using your personal AI assistant
            </p>
          </div>

          {/* Registration Card */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-xl sm:p-6">

            <form onSubmit={handleSubmit} className="space-y-3.5">

              {/* Name */}
              <div>
                <label
                  htmlFor="name"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Name
                </label>

                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Enter your name"
                  autoComplete="name"
                  disabled={isLoading}
                  className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-2.5 text-[var(--text-primary)] outline-none transition placeholder:text-[var(--text-secondary)] focus:border-[#10a37f] focus:ring-1 focus:ring-[#10a37f] disabled:opacity-60"
                />
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Email
                </label>

                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="Enter your email"
                  autoComplete="email"
                  disabled={isLoading}
                  className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-2.5 text-[var(--text-primary)] outline-none transition placeholder:text-[var(--text-secondary)] focus:border-[#10a37f] focus:ring-1 focus:ring-[#10a37f] disabled:opacity-60"
                />
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="password"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Password
                </label>

                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  autoComplete="new-password"
                  disabled={isLoading}
                  className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-2.5 text-[var(--text-primary)] outline-none transition placeholder:text-[var(--text-secondary)] focus:border-[#10a37f] focus:ring-1 focus:ring-[#10a37f] disabled:opacity-60"
                />

                <p className="mt-1 text-xs text-[var(--text-secondary)]">
                  Password must be at least 8 characters.
                </p>
              </div>

              {/* Confirm Password */}
              <div>
                <label
                  htmlFor="confirmPassword"
                  className="mb-1.5 block text-sm font-medium"
                >
                  Confirm Password
                </label>

                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  placeholder="Confirm your password"
                  autoComplete="new-password"
                  disabled={isLoading}
                  className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-4 py-2.5 text-[var(--text-primary)] outline-none transition placeholder:text-[var(--text-secondary)] focus:border-[#10a37f] focus:ring-1 focus:ring-[#10a37f] disabled:opacity-60"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Register */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-xl bg-[#10a37f] px-4 py-2.5 font-medium text-white transition hover:bg-[#0d8f70] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isLoading ? "Creating account..." : "Create account"}
              </button>
            </form>

            {/* Login */}
            <div className="mt-4 text-center text-sm text-[var(--text-secondary)]">
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => router.push("/login")}
                className="font-medium text-[#10a37f] hover:underline"
              >
                Log in
              </button>
            </div>
          </div>

          {/* Footer */}
          <p className="mt-3 text-center text-xs text-[var(--text-secondary)]">
            By creating an account, you can securely access your LocalGPT
            conversations.
          </p>
        </div>
      </div>
    </main>
  );
}