"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { ProblemSection } from "@/components/landing/ProblemSection";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ProductShowcase } from "@/components/landing/ProductShowcase";
import { Features } from "@/components/landing/Features";
import { UseCases } from "@/components/landing/UseCases";
import { InteractiveDemo } from "@/components/landing/InteractiveDemo";
import { TrustSection } from "@/components/landing/TrustSection";
import { FinalCTA } from "@/components/landing/FinalCTA";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [isLoading, user, router]);

  return (
    <div className="overflow-x-hidden">
      <Navbar />
      <main>
        <Hero />
        <ProblemSection />
        <HowItWorks />
        <ProductShowcase />
        <Features />
        <UseCases />
        <InteractiveDemo />
        <TrustSection />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
