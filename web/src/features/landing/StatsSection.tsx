export default function StatsSection() {
  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 mb-24">
      <div className="relative overflow-hidden rounded-2xl border border-dark-500 bg-dark-700/40 backdrop-blur-sm p-6 sm:p-10">
        <div className="pointer-events-none absolute inset-0 -z-0" aria-hidden="true">
          <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-accent-blue-600/25 blur-[100px]" />
          <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-accent-blue/20 blur-[100px]" />
        </div>
        <div className="relative grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8">
          <div className="text-center">
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-white">1</p>
            <p className="text-xs sm:text-sm text-dark-400 mt-1">Bot Instance</p>
          </div>
          <div className="text-center">
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-white">50+</p>
            <p className="text-xs sm:text-sm text-dark-400 mt-1">Commands</p>
          </div>
          <div className="text-center">
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-white">99.9%</p>
            <p className="text-xs sm:text-sm text-dark-400 mt-1">Uptime</p>
          </div>
          <div className="text-center">
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-white">Free</p>
            <p className="text-xs sm:text-sm text-dark-400 mt-1">Open Source</p>
          </div>
        </div>
      </div>
    </section>
  );
}