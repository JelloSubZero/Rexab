"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/lib/auth-context";
import { getErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function RegisterPage() {
  const { register, user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [firstName, setFirstName] = useState("");
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

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register(email, password, firstName);
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
        <h1 className="text-xl font-semibold text-primary">
          Create your account
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Split bills with friends and roommates.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <Input
            id="firstName"
            label="Name"
            autoComplete="given-name"
            required
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
          />
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
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && (
            <p role="alert" className="text-sm text-negative">
              {error}
            </p>
          )}

          <Button type="submit" isLoading={isSubmitting} className="mt-2">
            Create account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-secondary">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-accent">
            Log in
          </Link>
        </p>
      </Card>
    </div>
  );
}
