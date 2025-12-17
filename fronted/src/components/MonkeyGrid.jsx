
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LazyLoadImage } from 'react-lazy-load-image-component';
import 'react-lazy-load-image-component/src/effects/blur.css';
import { Loader2, Download, Copy, Check } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const PAGE_SIZE = 24;

const ImageCard = ({ item }) => {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);
  const [isCopying, setIsCopying] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    if (isCopying) return;

    setIsCopying(true);
    try {
      const response = await fetch(item.monkey_url);
      const inputBlob = await response.blob();

      // Convert to PNG if strictly needed, or just ensure it is PNG for clipboard
      // Since we know source is WebP, we must convert for WeChat/preview compatibility
      const pngBlob = await new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(inputBlob);

        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          canvas.toBlob((blob) => {
            URL.revokeObjectURL(url);
            if (blob) resolve(blob);
            else reject(new Error('Canvas toBlob failed'));
          }, 'image/png');
        };

        img.onerror = () => {
          URL.revokeObjectURL(url);
          reject(new Error('Failed to load image for conversion'));
        };

        img.src = url;
      });

      await navigator.clipboard.write([
        new ClipboardItem({
          'image/png': pngBlob,
        }),
      ]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy content: ', err);
      // Fallback: try copying original url or blob if conversion fails?
      // For now, let's keep it simple. If conversion fails, it fails.
    } finally {
      setIsCopying(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, rotate: -5 }}
      whileHover={{ y: -10, rotateX: 5, rotateY: -5, zIndex: 10 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      style={{ perspective: 1000 }}
      className="mb-6 break-inside-avoid relative"
    >
      <div className="group relative rounded-3xl overflow-hidden bg-zinc-900/50 backdrop-blur-md border border-white/5 transition-all duration-300 hover:shadow-[0_0_30px_-5px_rgba(76,175,80,0.3)] hover:border-green-500/30">

        {/* Holographic Border Overlay */}
        <div className="absolute inset-0 z-20 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-tr from-yellow-500/10 via-transparent to-green-500/10 mix-blend-overlay" />

        <div className="relative aspect-auto">
          <LazyLoadImage
            effect="blur"
            src={item.monkey_url}
            alt={item.id}
            width="100%"
            wrapperClassName="w-full h-full block"
            className="w-full h-auto object-cover transition-transform duration-700 group-hover:scale-110 grayscale-[20%] group-hover:grayscale-0"
          />

          {/* Pig Layout (Reveal) */}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-all duration-300 z-10 pointer-events-none">
            <img
              src={item.pig_url}
              alt={`${item.id} original`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20" />
            <div className="absolute bottom-3 right-3 bg-black/40 border border-white/10 px-3 py-1.5 rounded-full text-xs text-white/90 font-medium backdrop-blur-md flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-500 animate-pulse" />
              Original Pig
            </div>
          </div>

          {/* Floaty Actions */}
          <div className="absolute top-3 right-3 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-4 group-hover:translate-x-0 z-30 delay-75">
            <div className="relative">
              <AnimatePresence>
                {copied && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: -50 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="absolute right-0 top-1/2 -translate-y-1/2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-md whitespace-nowrap pointer-events-none"
                  >
                    {t('copied') || "Copied!"}
                  </motion.div>
                )}
              </AnimatePresence>
              <button
                onClick={handleCopy}
                disabled={isCopying}
                className="p-2.5 rounded-2xl bg-black/40 hover:bg-green-500/20 backdrop-blur-xl text-white border border-white/10 hover:border-green-500/50 transition-all hover:scale-110 active:scale-95 shadow-lg relative"
                title={t('copy')}
              >
                {isCopying ? (
                  <Loader2 className="w-4 h-4 animate-spin text-yellow-400" />
                ) : copied ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
            <a
              href={item.monkey_url}
              download={item.id}
              className="p-2.5 rounded-2xl bg-black/40 hover:bg-yellow-500/20 backdrop-blur-xl text-white border border-white/10 hover:border-yellow-500/50 transition-all hover:scale-110 active:scale-95 shadow-lg"
              title={t('download')}
              onClick={(e) => e.stopPropagation()}
            >
              <Download className="w-4 h-4" />
            </a>
          </div>
        </div>

        <div className="p-4 bg-gradient-to-b from-zinc-900/0 to-zinc-950/80 absolute bottom-0 inset-x-0 z-20 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
          <h3 className="text-xs font-mono text-green-400 truncate opacity-80 mb-1">
            ID: {item.id}
          </h3>
          <div className="h-0.5 w-full bg-gradient-to-r from-green-500/50 to-transparent rounded-full" />
        </div>
      </div>
    </motion.div>
  );
};

export function MonkeyGrid() {
  const { t } = useLanguage();
  const [items, setItems] = useState([]);
  const [displayedItems, setDisplayedItems] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    fetch('/monkey_manifest.json')
      .then(res => res.json())
      .then(data => {
        setItems(data);
        setDisplayedItems(data.slice(0, PAGE_SIZE));
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load manifest:", err);
        setLoading(false);
      });
  }, []);

  const spawnParticles = (x, y) => {
    const newParticles = Array.from({ length: 12 }).map((_, i) => ({
      id: Date.now() + i,
      x,
      y,
      angle: Math.random() * 360,
      velocity: Math.random() * 20 + 10,
      emoji: ['🍌', '🐒', '✨', '⚡️'][Math.floor(Math.random() * 4)]
    }));
    setParticles(prev => [...prev, ...newParticles]);
    setTimeout(() => {
      setParticles(prev => prev.filter(p => !newParticles.find(np => np.id === p.id)));
    }, 1000);
  };

  const loadMore = (e) => {
    if (!hasMore) return;

    // Spawn particles at click position
    const rect = e.target.getBoundingClientRect();
    spawnParticles(rect.left + rect.width / 2, rect.top + rect.height / 2);

    setLoading(true);
    setTimeout(() => {
      const nextPage = page + 1;
      const nextItems = items.slice(0, nextPage * PAGE_SIZE);
      setDisplayedItems(nextItems);
      setPage(nextPage);
      setLoading(false);
      if (nextItems.length >= items.length) setHasMore(false);
    }, 600);
  };

  return (
    <main className="container mx-auto px-4 py-8 perspective-1000">
      <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-6 space-y-6 pb-20">
        <AnimatePresence mode='popLayout'>
          {displayedItems.map((item) => (
            <ImageCard key={item.id} item={item} />
          ))}
        </AnimatePresence>
      </div>

      <div className="flex justify-center py-20 relative z-20">
        {loading && items.length === 0 ? (
          <div className="flex flex-col items-center gap-4 text-green-400/50 font-mono text-sm animate-pulse">
            <div className="p-4 rounded-full bg-green-500/5 border border-green-500/20">
              <Loader2 className="w-8 h-8 animate-spin text-green-500" />
            </div>
            <span>{t('initializing')}</span>
          </div>
        ) : (
          <motion.button
            onClick={loadMore}
            disabled={!hasMore || loading}
            whileHover={{ scale: 1.1, rotate: [-1, 1, -1] }}
            whileTap={{ scale: 0.9 }}
            className={`
                group relative px-10 py-5 rounded-full font-black text-xl transition-all duration-300 border-b-4 active:border-b-0 active:translate-y-1
                ${hasMore
                ? 'bg-gradient-to-r from-yellow-400 to-pink-500 text-white border-yellow-700 shadow-[0_10px_20px_rgba(234,179,8,0.4)] hover:shadow-[0_0_30px_rgba(236,72,153,0.6)]'
                : 'bg-zinc-800 text-zinc-600 border-zinc-900 cursor-not-allowed'}
            `}
          >
            {loading ? (
              <span className="flex items-center gap-3 font-mono">
                <Loader2 className="w-6 h-6 animate-spin" />
                {t('loading_data')}
              </span>
            ) : hasMore ? (
              <span className="flex items-center gap-2 drop-shadow-md">
                <span className="text-2xl animate-bounce">🍌</span>
                {t('load_more')}
              </span>
            ) : (
              <span className="font-mono text-sm opacity-50 tracking-widest">
                {t('end_archive')}
              </span>
            )}
          </motion.button>
        )}

        {/* Simple Particle Rendering */}
        {particles.map(p => (
          <motion.div
            key={p.id}
            initial={{ x: 0, y: 0, opacity: 1, scale: 0.5 }}
            animate={{
              x: Math.cos(p.angle) * 100,
              y: Math.sin(p.angle) * 100,
              opacity: 0,
              scale: 1.5
            }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="fixed pointer-events-none text-2xl z-50"
            style={{ left: p.x, top: p.y }}
          >
            {p.emoji}
          </motion.div>
        ))}
      </div>
    </main>
  );
}
