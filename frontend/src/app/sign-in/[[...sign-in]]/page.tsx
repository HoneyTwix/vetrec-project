import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
      <SignIn afterSignInUrl="/extract" redirectUrl="/extract" />
    </div>
  );
} 