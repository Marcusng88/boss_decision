
// Cartoon SVG avatars for each domain agent

interface AvatarProps { size?: number }

const HRAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="hr-bg" cx="40%" cy="30%" r="65%">
        <stop offset="0%" stopColor="#A78BFA" />
        <stop offset="100%" stopColor="#6D28D9" />
      </radialGradient>
    </defs>
    <circle cx="32" cy="32" r="32" fill="url(#hr-bg)" />
    {/* Hair buns */}
    <circle cx="17" cy="21" r="7" fill="#4C1D95" />
    <circle cx="47" cy="21" r="7" fill="#4C1D95" />
    <path d="M16 25 Q16 8 32 9 Q48 8 48 25" fill="#4C1D95" />
    {/* Face */}
    <ellipse cx="32" cy="33" rx="15" ry="14" fill="#FDE68A" />
    {/* Blush */}
    <circle cx="22" cy="36" r="3.5" fill="#FCA5A5" opacity="0.55" />
    <circle cx="42" cy="36" r="3.5" fill="#FCA5A5" opacity="0.55" />
    {/* Eyes */}
    <circle cx="26" cy="30" r="3.5" fill="#1E1B4B" />
    <circle cx="38" cy="30" r="3.5" fill="#1E1B4B" />
    <circle cx="27.3" cy="28.7" r="1.2" fill="white" />
    <circle cx="39.3" cy="28.7" r="1.2" fill="white" />
    {/* Smile */}
    <path d="M26 37 Q32 43 38 37" stroke="#6D28D9" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    {/* Body */}
    <path d="M18 47 Q18 54 32 55 Q46 54 46 47" fill="#7C3AED" />
    {/* Clipboard */}
    <rect x="27" y="50" width="10" height="8" rx="1.5" fill="white" />
    <rect x="29" y="48" width="6" height="3" rx="1.5" fill="#5B21B6" />
    <line x1="29" y1="55" x2="35" y2="55" stroke="#7C3AED" strokeWidth="1.2" />
    <line x1="29" y1="57" x2="33" y2="57" stroke="#7C3AED" strokeWidth="1.2" />
  </svg>
);

const LegalAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="legal-bg" cx="40%" cy="30%" r="65%">
        <stop offset="0%" stopColor="#3B82F6" />
        <stop offset="100%" stopColor="#1E3A8A" />
      </radialGradient>
    </defs>
    <circle cx="32" cy="32" r="32" fill="url(#legal-bg)" />
    {/* Lawyer wig */}
    <ellipse cx="32" cy="13" rx="15" ry="9" fill="#F1F5F9" />
    <path d="M17 17 Q14 22 14 27 Q17 24 17 27" fill="#E2E8F0" />
    <path d="M47 17 Q50 22 50 27 Q47 24 47 27" fill="#E2E8F0" />
    <circle cx="17" cy="26" r="4" fill="#E2E8F0" />
    <circle cx="47" cy="26" r="4" fill="#E2E8F0" />
    <circle cx="17" cy="31" r="3.5" fill="#E2E8F0" />
    <circle cx="47" cy="31" r="3.5" fill="#E2E8F0" />
    {/* Face */}
    <ellipse cx="32" cy="34" rx="14" ry="13" fill="#FDE68A" />
    {/* Eyebrows (serious) */}
    <path d="M24 28 L28 29" stroke="#92400E" strokeWidth="2" strokeLinecap="round" />
    <path d="M36 29 L40 28" stroke="#92400E" strokeWidth="2" strokeLinecap="round" />
    {/* Eyes */}
    <circle cx="27" cy="32" r="3" fill="#1E3A8A" />
    <circle cx="37" cy="32" r="3" fill="#1E3A8A" />
    <circle cx="28" cy="31" r="1" fill="white" />
    <circle cx="38" cy="31" r="1" fill="white" />
    {/* Neutral mouth */}
    <path d="M27 39 Q32 41 37 39" stroke="#92400E" strokeWidth="2" strokeLinecap="round" fill="none" />
    {/* Body / robe */}
    <path d="M19 47 Q19 55 32 56 Q45 55 45 47" fill="#1D4ED8" />
    {/* Scales icon */}
    <line x1="32" y1="49" x2="32" y2="55" stroke="#BFDBFE" strokeWidth="1.5" />
    <line x1="27" y1="51" x2="37" y2="51" stroke="#BFDBFE" strokeWidth="1.5" />
    <circle cx="27" cy="53" r="2.5" fill="#93C5FD" opacity="0.8" />
    <circle cx="37" cy="53" r="2.5" fill="#93C5FD" opacity="0.8" />
  </svg>
);

const SalesAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="sales-bg" cx="40%" cy="30%" r="65%">
        <stop offset="0%" stopColor="#34D399" />
        <stop offset="100%" stopColor="#047857" />
      </radialGradient>
    </defs>
    <circle cx="32" cy="32" r="32" fill="url(#sales-bg)" />
    {/* Spiky hair */}
    <path d="M20 22 L16 8 L22 18 L24 6 L28 16 L30 5 L32 16 L34 5 L36 16 L40 6 L42 18 L48 8 L44 22" fill="#065F46" />
    {/* Face */}
    <ellipse cx="32" cy="33" rx="15" ry="14" fill="#FDE68A" />
    {/* Blush */}
    <circle cx="21" cy="36" r="3.5" fill="#FCA5A5" opacity="0.55" />
    <circle cx="43" cy="36" r="3.5" fill="#FCA5A5" opacity="0.55" />
    {/* Eyes (big excited) */}
    <circle cx="26" cy="30" r="4" fill="#064E3B" />
    <circle cx="38" cy="30" r="4" fill="#064E3B" />
    <circle cx="27.5" cy="28.5" r="1.5" fill="white" />
    <circle cx="39.5" cy="28.5" r="1.5" fill="white" />
    {/* Big smile */}
    <path d="M24 37 Q32 46 40 37" stroke="#065F46" strokeWidth="2.5" strokeLinecap="round" fill="#FCA5A5" opacity="0.4" />
    <path d="M24 37 Q32 46 40 37" stroke="#065F46" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    {/* Body */}
    <path d="M18 47 Q18 54 32 55 Q46 54 46 47" fill="#059669" />
    {/* Tie */}
    <polygon points="32,47 30,53 32,51 34,53" fill="#A7F3D0" />
    {/* Rising chart */}
    <polyline points="24,56 27,54 30,55 33,52 37,50 40,48" stroke="#D1FAE5" strokeWidth="1.5" fill="none" strokeLinecap="round" />
  </svg>
);

const FinanceAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="fin-bg" cx="40%" cy="30%" r="65%">
        <stop offset="0%" stopColor="#FCD34D" />
        <stop offset="100%" stopColor="#B45309" />
      </radialGradient>
    </defs>
    <circle cx="32" cy="32" r="32" fill="url(#fin-bg)" />
    {/* Neat side-parted hair */}
    <path d="M14 26 Q14 7 32 8 Q48 7 50 26 Q44 20 32 22 Q20 20 14 26" fill="#92400E" />
    {/* Face */}
    <ellipse cx="32" cy="33" rx="15" ry="14" fill="#FEF3C7" />
    {/* Glasses frames */}
    <circle cx="26" cy="31" r="5.5" fill="none" stroke="#92400E" strokeWidth="2" />
    <circle cx="38" cy="31" r="5.5" fill="none" stroke="#92400E" strokeWidth="2" />
    <line x1="31.5" y1="31" x2="32.5" y2="31" stroke="#92400E" strokeWidth="2" />
    <line x1="20.5" y1="29" x2="17" y2="27" stroke="#92400E" strokeWidth="2" />
    <line x1="43.5" y1="29" x2="47" y2="27" stroke="#92400E" strokeWidth="2" />
    {/* Eyes behind glasses */}
    <circle cx="26" cy="31" r="2.5" fill="#92400E" />
    <circle cx="38" cy="31" r="2.5" fill="#92400E" />
    <circle cx="26.8" cy="30.2" r="0.8" fill="white" />
    <circle cx="38.8" cy="30.2" r="0.8" fill="white" />
    {/* Focused mouth */}
    <path d="M26 39 Q32 43 38 39" stroke="#92400E" strokeWidth="2" strokeLinecap="round" fill="none" />
    {/* Body */}
    <path d="M18 47 Q18 54 32 55 Q46 54 46 47" fill="#D97706" />
    {/* Calculator */}
    <rect x="26" y="49" width="12" height="9" rx="2" fill="#FEF3C7" />
    <rect x="27.5" y="50.5" width="9" height="2" rx="0.5" fill="#D97706" />
    <circle cx="28.5" cy="55" r="1" fill="#D97706" />
    <circle cx="32" cy="55" r="1" fill="#D97706" />
    <circle cx="35.5" cy="55" r="1" fill="#D97706" />
  </svg>
);

const MarketingAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="mkt-bg" cx="40%" cy="30%" r="65%">
        <stop offset="0%" stopColor="#F472B6" />
        <stop offset="100%" stopColor="#BE185D" />
      </radialGradient>
    </defs>
    <circle cx="32" cy="32" r="32" fill="url(#mkt-bg)" />
    {/* Wild star hair */}
    <path d="M32 4 L33.5 10 L38 6 L37 12 L43 9 L40 15 L47 14 L43 19 L50 20 L44 23" fill="#831843" />
    <path d="M32 4 L30.5 10 L26 6 L27 12 L21 9 L24 15 L17 14 L21 19 L14 20 L20 23" fill="#831843" />
    <circle cx="20" cy="10" r="2" fill="#F9A8D4" />
    <circle cx="44" cy="10" r="2" fill="#F9A8D4" />
    <circle cx="14" cy="18" r="1.5" fill="#F9A8D4" />
    <circle cx="50" cy="18" r="1.5" fill="#F9A8D4" />
    {/* Face */}
    <ellipse cx="32" cy="33" rx="15" ry="13" fill="#FDE68A" />
    {/* Blush */}
    <circle cx="21" cy="36" r="4" fill="#FCA5A5" opacity="0.6" />
    <circle cx="43" cy="36" r="4" fill="#FCA5A5" opacity="0.6" />
    {/* Star eyes */}
    <circle cx="26" cy="30" r="3.5" fill="#831843" />
    <circle cx="38" cy="30" r="3.5" fill="#831843" />
    <circle cx="27.5" cy="28.5" r="1.2" fill="white" />
    <circle cx="39.5" cy="28.5" r="1.2" fill="white" />
    {/* Excited smile with teeth */}
    <path d="M24 37 Q32 45 40 37" stroke="#831843" strokeWidth="2.5" strokeLinecap="round" fill="#FCA5A5" opacity="0.3" />
    {/* Body */}
    <path d="M18 46 Q18 54 32 55 Q46 54 46 46" fill="#DB2777" />
    {/* Megaphone */}
    <polygon points="25,49 25,56 29,56 36,52 36,49" fill="#FBCFE8" />
    <rect x="22" y="49" width="3" height="7" rx="1" fill="#F9A8D4" />
    {/* Sound waves */}
    <path d="M37 50 Q40 51 40 52.5 Q40 54 37 55" stroke="#FBCFE8" strokeWidth="1.5" fill="none" />
    <path d="M38 48.5 Q43 50 43 52.5 Q43 55 38 56.5" stroke="#FBCFE8" strokeWidth="1.2" fill="none" />
  </svg>
);

const SupplyChainAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="sc-bg" cx="40%" cy="30%" r="65%">
        <stop offset="0%" stopColor="#FB923C" />
        <stop offset="100%" stopColor="#C2410C" />
      </radialGradient>
    </defs>
    <circle cx="32" cy="32" r="32" fill="url(#sc-bg)" />
    {/* Hard hat brim */}
    <path d="M14 28 Q14 24 32 24 Q50 24 50 28 L50 30 Q50 28 32 28 Q14 28 14 30Z" fill="#FCD34D" />
    {/* Hard hat dome */}
    <ellipse cx="32" cy="20" rx="16" ry="10" fill="#FBBF24" />
    {/* Hat stripe */}
    <path d="M16 24 Q16 20 32 20 Q48 20 48 24" stroke="#F59E0B" strokeWidth="2" fill="none" />
    {/* Face */}
    <ellipse cx="32" cy="35" rx="15" ry="14" fill="#FDE68A" />
    {/* Blush */}
    <circle cx="21" cy="38" r="3" fill="#FCA5A5" opacity="0.5" />
    <circle cx="43" cy="38" r="3" fill="#FCA5A5" opacity="0.5" />
    {/* Eyes */}
    <circle cx="26" cy="32" r="3.5" fill="#7C2D12" />
    <circle cx="38" cy="32" r="3.5" fill="#7C2D12" />
    <circle cx="27.3" cy="30.7" r="1.2" fill="white" />
    <circle cx="39.3" cy="30.7" r="1.2" fill="white" />
    {/* Smile */}
    <path d="M25 39 Q32 45 39 39" stroke="#7C2D12" strokeWidth="2.5" strokeLinecap="round" fill="none" />
    {/* Body */}
    <path d="M18 49 Q18 56 32 57 Q46 56 46 49" fill="#EA580C" />
    {/* Box / package */}
    <rect x="26" y="50" width="12" height="9" rx="1.5" fill="#FED7AA" />
    <line x1="32" y1="50" x2="32" y2="59" stroke="#EA580C" strokeWidth="1.5" />
    <line x1="26" y1="54" x2="38" y2="54" stroke="#EA580C" strokeWidth="1.5" />
  </svg>
);

const DefaultAvatar = ({ size = 60 }: AvatarProps) => (
  <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="32" cy="32" r="32" fill="#6B7280" />
    <circle cx="32" cy="28" r="12" fill="#D1D5DB" />
    <ellipse cx="32" cy="50" rx="16" ry="10" fill="#D1D5DB" />
  </svg>
);

const AVATAR_MAP: Record<string, (p: AvatarProps) => JSX.Element> = {
  hr: HRAvatar,
  legal: LegalAvatar,
  sales: SalesAvatar,
  finance: FinanceAvatar,
  marketing: MarketingAvatar,
  supply_chain: SupplyChainAvatar,
  'supply chain': SupplyChainAvatar,
};

export const AGENT_COLORS: Record<string, { gradient: string; ring: string; text: string; light: string }> = {
  hr: { gradient: 'from-violet-500 to-purple-700', ring: 'ring-violet-400', text: 'text-violet-700', light: 'bg-violet-50 border-violet-200' },
  legal: { gradient: 'from-blue-600 to-blue-900', ring: 'ring-blue-400', text: 'text-blue-800', light: 'bg-blue-50 border-blue-200' },
  sales: { gradient: 'from-emerald-400 to-green-700', ring: 'ring-emerald-400', text: 'text-emerald-700', light: 'bg-emerald-50 border-emerald-200' },
  finance: { gradient: 'from-yellow-400 to-amber-600', ring: 'ring-amber-400', text: 'text-amber-700', light: 'bg-amber-50 border-amber-200' },
  marketing: { gradient: 'from-pink-400 to-rose-700', ring: 'ring-pink-400', text: 'text-pink-700', light: 'bg-pink-50 border-pink-200' },
  supply_chain: { gradient: 'from-orange-400 to-red-600', ring: 'ring-orange-400', text: 'text-orange-700', light: 'bg-orange-50 border-orange-200' },
  'supply chain': { gradient: 'from-orange-400 to-red-600', ring: 'ring-orange-400', text: 'text-orange-700', light: 'bg-orange-50 border-orange-200' },
};

interface AgentAvatarProps {
  agentName: string;
  size?: number;
}

export const AgentAvatar = ({ agentName, size = 60 }: AgentAvatarProps) => {
  const key = agentName.toLowerCase().replace(/\s+/g, '_');
  const AvatarComponent = AVATAR_MAP[key] || AVATAR_MAP[agentName.toLowerCase()] || DefaultAvatar;
  return <AvatarComponent size={size} />;
};
