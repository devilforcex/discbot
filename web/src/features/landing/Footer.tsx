export default function Footer() {
  return (
    <footer className="bg-dark-800/20 border-t border-dark-500 backdrop-blur-md rounded-bl-lg rounded-br-lg p-5 shadow-lg">
      <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-10 md:gap-20 mt-9 m-auto px-5 md:px-0">
        <div className="w-[60%]">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-[11px] bg-gradient-to-br from-accent-blue-600 to-accent-blue-300 flex items-center justify-center">
              <span className="text-white font-black text-sm">DB</span>
            </div>
            <h4 className="text-2xl font-bold text-white">DrusaBoT</h4>
          </div>
          <p className="w-full text-dark-400 mt-2 text-sm">
            High-fidelity Discord music bot powered by Lavalink v4. Open source, self-hosted,
            fully customizable.
          </p>
        </div>
        <div className="grid grid-cols-2 w-full sm:grid-cols-3 gap-5 md:gap-10">
          <div>
            <ul className="flex w-full flex-col">
              <p className="mb-3 text-lg text-white font-medium">Links</p>
              <a href="https://github.com/devilforcex/DrusaBoT" className="text-dark-400 mt-2 text-sm hover:text-accent-blue transition-colors">GitHub</a>
              <a href="https://discord.gg/" className="text-dark-400 mt-2 text-sm hover:text-accent-blue transition-colors">Discord</a>
              <li className="text-dark-400 mt-2 text-sm">Dashboard</li>
            </ul>
          </div>
          <div>
            <ul className="flex w-full flex-col">
              <p className="mb-3 text-lg text-white font-medium">Docs</p>
              <a href="/docs/PROJECT_PLAN.md" className="text-dark-400 mt-2 text-sm hover:text-accent-blue transition-colors">Project Plan</a>
              <a href="/docs/DESIGN_SYSTEM.md" className="text-dark-400 mt-2 text-sm hover:text-accent-blue transition-colors">Design System</a>
              <a href="https://github.com/devilforcex/DrusaBoT/blob/main/README.md" className="text-dark-400 mt-2 text-sm hover:text-accent-blue transition-colors">README</a>
            </ul>
          </div>
          <div>
            <ul className="flex w-full flex-col">
              <p className="mb-3 text-lg text-white font-medium">Tech</p>
              <li className="text-dark-400 mt-2 text-sm">Python 3.11+</li>
              <li className="text-dark-400 mt-2 text-sm">FastAPI</li>
              <li className="text-dark-400 mt-2 text-sm">React + Vite</li>
              <li className="text-dark-400 mt-2 text-sm">Tailwind v4</li>
            </ul>
          </div>
        </div>
      </div>
      <div className="mt-10 border-t border-dark-500 w-full max-w-6xl m-auto px-5 md:px-0">
        <div className="flex flex-col md:flex-row justify-between mt-4 text-center md:text-left">
          <p className="text-dark-400 text-sm">© 2026 DrusaBoT. Open source.</p>
          <p className="text-dark-400 text-sm">Made with ❤️</p>
        </div>
      </div>
    </footer>
  );
}