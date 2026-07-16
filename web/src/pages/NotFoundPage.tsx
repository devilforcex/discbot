import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-dark-900 text-dark-200">
      <h1 className="mb-4 text-6xl font-bold text-gradient">404</h1>
      <p className="mb-8 text-lg">Page not found</p>
      <Link
        to="/"
        className="rounded-lg bg-accent-violet px-6 py-3 text-white transition hover:bg-accent-violet/80"
      >
        Go Home
      </Link>
    </div>
  );
}
