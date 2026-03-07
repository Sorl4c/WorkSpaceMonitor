import React, { useState } from 'react';
import { Terminal, Code, Globe, MessageSquare, Folder, LayoutGrid, Monitor, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';

// --- DATOS REALES PARSEADOS MEDIANTE HEURÍSTICA DE FRONTEND ---
const desktopsData = {
  14: {
    id: "2041DD79...",
    name: "WorkspaceMonitor Dev",
    terminal: ["◇ Ready (WorkspaceMonitor)", "Windows PowerShell"],
    code: ["global-contex.md - WorkspaceMonitor - Visual Studio Code", "*nuevo2 - Notepad++"],
    files: ["docs - Explorador de archivos"],
    web: ["Perplexity (TDAH, mapa mental, fastapi)", "Google Gemini", "Consuming StreamingResponse...", "view-source:localhost:8080 - Comet"],
    comms: ["WhatsApp"],
    system: ["Configuración"]
  },
  13: {
    id: "FB850135...",
    name: "Comandas KDS",
    terminal: ["◇ Ready (comandas-kds)", "Windows PowerShell (x2)"],
    code: ["pos_simulator.php - comandas-kds - Visual Studio Code", "DBeaver 25.3.3", "XAMPP Control Panel v3.3.0", "*Actúa como mentor... - Bloc de notas"],
    files: ["node_modules - Explorador de archivos", "comandas-kds - Explorador de archivos"],
    web: ["POS Simulator - Comet", "Perplexity", "NotebookLM", "Gmail", "view-source:alpinejs.dev..."],
    comms: ["#testimonios | DSPRO TRADING ROOM - Discord"],
    system: ["WhisperTyping", "Sin título (Recuperado) - Paint"]
  },
  2: {
    id: "2ADEF147...",
    name: "GymTrack Services",
    terminal: ["GymTrack API - python launch_api.py", "GymTrack Bot - python -m src...", "Cloudflare Tunnel (localhost:8000)", "◇ Ready (tracking-entrenamientos)"],
    code: [],
    files: ["tracking-entrenamientos - Explorador de archivos"],
    web: ["feat(tray-tts)... - Edge", "sorlacopenclaw-collab - Edge", "Google Gemini", "NotebookLM - La Voz Curiosa"],
    comms: [],
    system: []
  },
  3: {
    id: "9DED1818...",
    name: "Local TTS & Config",
    terminal: ["◇ Ready (local-tts-service)", "root@CAAB-PC: /mnt/c/local/...", "Windows PowerShell (x2)"],
    code: ["AGENTS.md - gemini - VS Code", ".env - tracking-entrenamientos - VS Code", "reproductor.jpg - local-tts-service - VS Code", "transcript_fastz.md - excalidraw - VS Code"],
    files: ["rom - Explorador de archivos", "excalidraw - Explorador de archivos"],
    web: ["ChatGPT - Comet", "Google Gemini", "NotebookLM", "Perplexity"],
    comms: [],
    system: ["Administrador de tareas", "Propiedades de local-tts-service"]
  },
  5: {
    id: "F3161439...",
    name: "IA Agents Research",
    terminal: ["◇ Ready (gemini)", "Windows PowerShell"],
    code: ["*Queremos agregar... - Bloc de notas"],
    files: ["output - Explorador", "input - Explorador", "Descargas - Explorador", "fras-ia-clean - Explorador", "gemini - Explorador"],
    web: ["Gentleman-Programming - Comet", "Pricing - Simple Plans", "Infinitas Mentes", "Perplexity", "Google Gemini"],
    comms: [],
    system: ["Reproductor multimedia", "Opciones de energía"]
  },
  12: {
    id: "29090D1C...",
    name: "Media, Utils & Comms",
    terminal: ["Windows PowerShell"],
    code: [],
    files: ["openclaw-share - Explorador", "Descargas - Explorador"],
    web: ["Cloud Player de Audible", "YouTube Music (Boris Brejcha - Space Diver)", "YouTube", "Perplexity", "Codex: descarga e instalación..."],
    comms: ["Telegram: Join Group Chat", "Telegram Web", "Telegram A", "Gmail"],
    system: ["Ubuntu 64-bit - VMware Workstation", "Microsoft Store"]
  },
  7: {
    id: "C509EE66...",
    name: "OpenClaw Comms",
    terminal: [],
    code: [],
    files: [],
    web: ["OpenClaw › 01-gym-tracker - Comet", "OpenClaw › 00-central-orquestación - Comet"],
    comms: ["Telegram - Comet (x5)"],
    system: []
  }
};

export default function WorkspaceMonitor() {
  const [activeDesktop, setActiveDesktop] = useState(14);
  const [showEmptyDesktops, setShowEmptyDesktops] = useState(false);
  const data = desktopsData[activeDesktop];

  const totalWindows = (arr) => arr ? arr.length : 0;
  const currentTotal = totalWindows(data.terminal) + totalWindows(data.code) + totalWindows(data.files) + totalWindows(data.web) + totalWindows(data.comms) + totalWindows(data.system);

  // --- HEURÍSTICAS AÑADIDAS ---
  const isWebApp = (title) => {
    const lower = title.toLowerCase();
    const keywords = ['perplexity', 'gmail', 'gemini', 'notebooklm', 'chatgpt', 'swagger', 'localhost', 'comet', 'view-source:localhost'];
    return keywords.some(kw => lower.includes(kw));
  };

  const isAnchorTerminal = (title) => {
    const lower = title.toLowerCase();
    const keywords = [
      'ready', 'python', 'npm', 'node', 'ssh', 'uvicorn', 'launch', 
      'bot', 'tunnel', 'cloudflare', 'root@', '/mnt/', 'c:\\', 
      'watch', 'serve', 'bash', 'wsl', 'server', 'worker'
    ];
    return keywords.some(kw => lower.includes(kw));
  };

  const isTool = (title) => {
    const lower = title.toLowerCase();
    const toolKeywords = ['dbeaver', 'xampp', 'postman', 'studio', 'docker', 'control panel', 'insomnia'];
    return toolKeywords.some(kw => lower.includes(kw));
  };

  const getSemanticSummary = (desk) => {
    const parts = [];
    if (desk.terminal?.length) parts.push(`${desk.terminal.length} term`);
    if (desk.code?.length) parts.push(`${desk.code.length} cód`);
    if (desk.web?.length) parts.push(`${desk.web.length} web`);
    if (desk.files?.length) parts.push(`${desk.files.length} arch`);
    if (desk.comms?.length) parts.push(`${desk.comms.length} comms`);
    return parts.length > 0 ? parts.join(' · ') : 'sin apps productivas';
  };

  const emptyDesktopsList = [1, 4, 6, 8, 9, 10, 11];

  // Agrupaciones para las subdivisiones
  const webApps = data.web.filter(w => isWebApp(w));
  const webBrowsers = data.web.filter(w => !isWebApp(w));
  
  const codeFiles = data.code.filter(c => !isTool(c));
  const codeTools = data.code.filter(c => isTool(c));

  return (
    <div className="h-screen w-screen bg-[#0a0a0a] text-gray-200 overflow-hidden flex font-sans selection:bg-green-900 selection:text-green-100">
      <style dangerouslySetInnerHTML={{__html: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #444; }
      `}} />

      {/* 1. SIDEBAR: NAVEGACIÓN DE ESCRITORIOS (20%) */}
      <aside className="w-[20%] min-w-[250px] h-full border-r border-gray-800 bg-[#0d0d0d] flex flex-col">
        <div className="p-5 border-b border-gray-800/80 shrink-0">
          <h1 className="text-lg font-bold text-white flex items-center gap-2">
            <LayoutGrid size={18} className="text-green-500" />
            WM / Cluster View
          </h1>
          <p className="text-xs text-gray-500 mt-1 font-mono">14 Virtual Desktops</p>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-3 flex flex-col gap-1">
          {Object.entries(desktopsData).map(([num, desk]) => {
            const isActive = Number(num) === activeDesktop;
            return (
              <button
                key={num}
                onClick={() => setActiveDesktop(Number(num))}
                className={`w-full text-left px-3 py-2.5 rounded-md flex justify-between items-start transition-all ${
                  isActive ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
                }`}
              >
                <div className="flex items-start gap-2 overflow-hidden w-full">
                  <span className={`font-mono text-xs w-6 mt-0.5 shrink-0 ${isActive ? 'text-green-400' : 'text-gray-600'}`}>[{num}]</span>
                  <div className="flex flex-col overflow-hidden w-full">
                    <span className="text-sm font-medium truncate">{desk.name}</span>
                    <span className={`text-[10px] font-mono mt-0.5 truncate ${isActive ? 'text-gray-400' : 'text-gray-600'}`}>
                      {getSemanticSummary(desk)}
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
          
          {/* Escritorios vacíos colapsables */}
          <div className="mt-2 pt-2 border-t border-gray-800/50">
            <button 
              onClick={() => setShowEmptyDesktops(!showEmptyDesktops)}
              className="w-full text-left px-3 py-2 rounded-md flex items-center gap-2 text-gray-600 hover:text-gray-400 transition-colors"
            >
              {showEmptyDesktops ? <ChevronDown size={14} className="shrink-0" /> : <ChevronRight size={14} className="shrink-0" />}
              <span className="text-xs font-mono truncate">[{emptyDesktopsList.join(', ')}] · {emptyDesktopsList.length} sin actividad</span>
            </button>
            
            {showEmptyDesktops && emptyDesktopsList.map(num => (
              <button key={num} className="w-full text-left px-3 py-1.5 rounded-md flex items-center gap-2 text-gray-600 cursor-not-allowed opacity-40 ml-4 mt-1">
                 <span className="font-mono text-xs w-6">[{num}]</span>
                 <span className="text-xs italic">Sin ventanas activas</span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* 2. ÁREA PRINCIPAL: EL ESCRITORIO ACTIVO (80%) */}
      <main className="flex-1 h-full flex flex-col bg-[#0a0a0a]">
        
        <header className="h-[60px] shrink-0 border-b border-gray-800 flex items-center justify-between px-8">
          <div className="flex items-center gap-3">
            <Monitor size={20} className="text-gray-500" />
            <h2 className="text-xl font-semibold text-white">Escritorio {activeDesktop}: <span className="text-gray-400">{data.name}</span></h2>
          </div>
          <div className="text-xs font-mono text-gray-500 bg-[#161616] px-3 py-1.5 rounded-full border border-gray-800">
            {currentTotal} ventanas detectadas
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* CAJA 1: TERMINALES Y MOTORES */}
            {data.terminal.length > 0 && (
              <div className="col-span-1 lg:col-span-2 bg-black border border-gray-800 rounded-sm overflow-hidden">
                <div className="bg-[#111] border-b border-gray-800 px-4 py-2 flex items-center gap-2">
                  <Terminal size={14} className="text-green-500" />
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Terminales & Ejecución</span>
                </div>
                <div className="p-4 flex flex-col gap-2">
                  {data.terminal.map((t, i) => {
                    const isAnchor = isAnchorTerminal(t);
                    return (
                      <div key={i} className={`font-mono text-sm flex gap-3 items-center ${isAnchor ? 'text-green-400 font-bold' : 'text-gray-500'}`}>
                        <span className={isAnchor ? 'text-green-500' : 'text-gray-600'}>&gt;</span>
                        <span>{t}</span>
                        {isAnchor && (
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse ml-2 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* CAJA 2: CÓDIGO & HERRAMIENTAS */}
            {data.code.length > 0 && (
              <div className="bg-[#121212] border border-gray-800 rounded-sm">
                 <div className="border-b border-gray-800/50 px-4 py-2 flex items-center gap-2">
                  <Code size={14} className="text-blue-400" />
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Código & Herramientas</span>
                </div>
                <div className="p-4 flex flex-col gap-5">
                  {codeFiles.length > 0 && (
                    <div className="flex flex-col gap-3">
                      <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-0.5">Código</div>
                      {codeFiles.map((c, i) => (
                        <div key={`code-${i}`} className="text-sm text-gray-300 flex items-start gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500/30 mt-1.5 shrink-0"></div>
                          <span className="leading-snug">{c}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {codeTools.length > 0 && (
                    <div className="flex flex-col gap-3">
                      <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-0.5">Herramientas</div>
                      {codeTools.map((c, i) => (
                        <div key={`tool-${i}`} className="text-sm text-gray-400 flex items-start gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-400/20 mt-1.5 shrink-0"></div>
                          <span className="leading-snug">{c}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* CAJA 3: SUPERFICIE WEB */}
            {data.web.length > 0 && (
              <div className="bg-[#151515] border border-gray-800/80 rounded-sm">
                 <div className="border-b border-gray-800/50 px-4 py-2 flex items-center gap-2">
                  <Globe size={14} className="text-orange-400" />
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Navegadores & Web-Apps</span>
                </div>
                <div className="p-4 flex flex-col gap-5">
                  {webApps.length > 0 && (
                    <div className="flex flex-col gap-3">
                      <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-0.5">Web-Apps</div>
                      {webApps.map((w, i) => (
                        <div key={`webapp-${i}`} className="text-sm flex items-start gap-2 text-indigo-200">
                           <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 bg-indigo-500 shadow-[0_0_6px_rgba(99,102,241,0.5)]"></div>
                          <span className="leading-snug">{w}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {webBrowsers.length > 0 && (
                    <div className="flex flex-col gap-3">
                      <div className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-0.5">Navegación</div>
                      {webBrowsers.map((w, i) => (
                        <div key={`browser-${i}`} className="text-sm flex items-start gap-2 text-gray-400">
                           <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 bg-orange-500/40"></div>
                          <span className="leading-snug">{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* CAJA 4: ARCHIVOS */}
            {data.files.length > 0 && (
              <div className="bg-[#121212] border border-gray-800 rounded-sm">
                 <div className="border-b border-gray-800/50 px-4 py-2 flex items-center gap-2">
                  <Folder size={14} className="text-yellow-500" />
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Archivos locales</span>
                </div>
                <div className="p-4 flex flex-col gap-3">
                  {data.files.map((f, i) => (
                    <div key={i} className="text-sm font-mono text-gray-400 flex items-start gap-2">
                      <span className="text-yellow-500/50">./</span>
                      <span className="leading-snug">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CAJA 5: COMUNICACIÓN */}
            {data.comms.length > 0 && (
              <div className="bg-[#121212] border border-gray-800 rounded-sm">
                 <div className="border-b border-gray-800/50 px-4 py-2 flex items-center gap-2">
                  <MessageSquare size={14} className="text-purple-400" />
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Comunicación</span>
                </div>
                <div className="p-4 flex flex-col gap-3">
                  {data.comms.map((c, i) => (
                    <div key={i} className="text-sm text-gray-300 flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-500/30 mt-1.5 shrink-0"></div>
                      <span className="leading-snug">{c}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CAJA 6: AMBIGÜEDAD / RUIDO */}
            {data.system.length > 0 && (
              <div className="col-span-1 lg:col-span-2 mt-4 bg-transparent border border-dashed border-gray-700/50 rounded-sm opacity-60 hover:opacity-100 transition-opacity">
                 <div className="px-4 py-2 flex items-center gap-2">
                  <AlertCircle size={14} className="text-gray-500" />
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Ambigüedad / Utils / Sistema</span>
                </div>
                <div className="p-4 pt-0 grid grid-cols-2 gap-2 text-xs text-gray-500">
                  {data.system.map((s, i) => (
                    <div key={i} className="truncate" title={s}>• {s}</div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      </main>
    </div>
  );
}