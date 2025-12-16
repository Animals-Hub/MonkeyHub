import React from 'react';
import { Ghost, Globe } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

export function Header() {
  const { t, lang, setLang } = useLanguage();

  const toggleLang = () => {
    const langs = ['zh', 'en', 'ja'];
    const nextIndex = (langs.indexOf(lang) + 1) % langs.length;
    setLang(langs[nextIndex]);
  };

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-zinc-950/80 border-b border-white/10">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 group cursor-pointer">
          <div className="p-2 rounded-xl bg-yellow-400/10 group-hover:bg-yellow-400/20 transition-colors">
            <Ghost className="w-6 h-6 text-yellow-500" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white">
            {t('title')}
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-zinc-400">
          <a href="#" className="hover:text-yellow-500 transition-colors">{t('home')}</a>
          <a href="#" className="hover:text-yellow-500 transition-colors">{t('all_monkeys')}</a>
          <a href="#" className="hover:text-yellow-500 transition-colors">{t('about')}</a>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleLang}
            className="p-2 rounded-full hover:bg-white/10 text-zinc-400 hover:text-white transition-colors flex items-center gap-1 font-mono text-xs border border-transparent hover:border-white/10"
            title="Switch Language"
          >
            <Globe className="w-4 h-4" />
            <span className="uppercase">{lang}</span>
          </button>

          <button className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 text-sm font-medium text-white transition-all border border-white/5 hover:border-white/10">
            <span>{t('upload')}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
