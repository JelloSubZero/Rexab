"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/lib/auth-context";
import { getErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function LoginPage() {
  const { login, user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && user) {
      router.replace("/dashboard");
    }
  }, [authLoading, user, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <Card className="w-full max-w-sm">
        <h1 className="text-xl font-semibold text-primary">Welcome back</h1>
        <p className="mt-1 text-sm text-secondary">
          Log in to see your rooms and balances.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <Input
            id="email"
            type="email"
            label="Email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Input
            id="password"
            type="password"
            label="Password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && (
            <p role="alert" className="text-sm text-negative">
              {error}
            </p>
          )}

          <Button type="submit" isLoading={isSubmitting} className="mt-2">
            Log in
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-secondary">
          No account?{" "}
          <Link href="/register" className="font-medium text-accent">
            Create one
          </Link>
        </p>
      </Card>
    </div>
  );
}
