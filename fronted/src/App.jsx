import { Header } from './components/Header';
import { MonkeyGrid } from './components/MonkeyGrid';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';

function AppContent() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-yellow-500/30 overflow-x-hidden">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-yellow-500/10 rounded-full blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-green-500/10 rounded-full blur-[128px] animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      <div className="relative z-10">
        <Header />

        {/* Hero Section */}
        <section className="relative pt-32 pb-20 text-center px-4 overflow-hidden">
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

          <div className="relative z-10 animate-float">
            <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-6 relative inline-block">
              <span className="absolute -inset-1 blur-2xl bg-gradient-to-r from-yellow-400 to-green-500 opacity-30"></span>
              <span className="relative text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-yellow-500 to-green-500 drop-shadow-[0_0_15px_rgba(234,179,8,0.5)]">
                {t('hero_title')}
              </span>
            </h1>
          </div>

          <p className="text-zinc-400 text-lg md:text-2xl max-w-2xl mx-auto font-light tracking-wide mt-4">
            <span className="text-green-400 font-medium">{t('hero_subtitle')}</span>
            <br className="my-2" />
            {t('hero_desc')}
          </p>

          <div className="mt-8 flex justify-center gap-4">
            <div className="h-1 w-24 bg-gradient-to-r from-transparent via-yellow-500/50 to-transparent rounded-full" />
          </div>
        </section>

        <MonkeyGrid />

        <footer className="py-20 text-center text-zinc-600 text-sm border-t border-white/5 bg-zinc-950/50 backdrop-blur-xl flex flex-col items-center gap-8">
          <p>© {new Date().getFullYear()} MonkeyHub. <span className="text-zinc-500">{t('footer')}</span></p>

          {/* Cyber-Chip Acknowledgement - High Visibility Version */}
          <div className="relative group cursor-pointer inline-flex items-center gap-4 px-8 py-4 rounded-xl bg-zinc-900 border border-green-500/30 hover:border-green-400 hover:bg-zinc-800 transition-all duration-300 hover:shadow-[0_0_25px_-5px_rgba(76,175,80,0.6)] hover:-translate-y-1">
            <div className="absolute inset-0 bg-green-500/5 group-hover:bg-green-500/10 transition-colors rounded-xl" />

            {/* Status Light */}
            <div className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </div>

            <div className="flex flex-col items-start gap-0.5 z-10">
              <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest">{t('thanks_prefix')}</span>
              <a
                href="https://pighub.top"
                target="_blank"
                rel="noopener noreferrer"
                className="text-lg font-black text-white hover:text-green-300 transition-colors tracking-tight"
                style={{
                  textShadow: '0 0 10px rgba(76, 175, 80, 0.5)'
                }}
              >
                PIGHUB.TOP <span className="text-yellow-500">↗</span>
              </a>
            </div>

            {/* Decorative Corner Accents */}
            <div className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-green-500/50 rounded-tr-lg" />
            <div className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-green-500/50 rounded-bl-lg" />
          </div>
        </footer>
      </div>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

export default App;
