#!/usr/bin/env python3
"""
Generate 10,000+ domain combinations for testing
"""

# Expanded lists
business_words = [
    # Core terms (100+)
    "account", "admin", "agency", "agent", "alert", "analyze", "app", "assist",
    "auto", "bank", "bill", "book", "brand", "budget", "build", "business",
    "calendar", "call", "campaign", "care", "cash", "catalog", "center", "chat",
    "check", "claim", "client", "clinic", "cloud", "coach", "code", "commerce",
    "contact", "content", "control", "convert", "core", "cost", "course", "create",
    "credit", "crm", "customer", "dash", "data", "deal", "debt", "deliver",
    "design", "desk", "digital", "direct", "doc", "drive", "earn", "easy",
    "edit", "edu", "email", "engage", "enterprise", "erp", "event", "expense",
    "expert", "export", "fast", "feed", "file", "finance", "find", "flow",
    "focus", "follow", "forecast", "form", "forum", "free", "fulfill", "fund",
    "generate", "global", "go", "grade", "graph", "group", "grow", "guide",
    "health", "help", "hire", "home", "host", "hotel", "house", "hub",
    "idea", "image", "import", "income", "info", "insight", "inspect", "instant",
    "insure", "integrate", "interact", "interface", "inventory", "invest", "invoice",
    "join", "journey", "jump", "keep", "key", "know", "lab", "launch",
    "lead", "learn", "legal", "lend", "lesson", "letter", "level", "leverage",
    "library", "license", "life", "link", "list", "listen", "live", "load",
    "loan", "local", "locate", "lock", "log", "logic", "logistics", "look",
    "mail", "main", "maintain", "make", "manage", "manual", "map", "margin",
    "mark", "market", "master", "match", "maximize", "measure", "media", "medical",
    "meet", "member", "memo", "menu", "merge", "message", "method", "metrics",
    "micro", "migrate", "mini", "mobile", "model", "modern", "monitor", "month",
    "move", "multi", "net", "network", "news", "next", "note", "notice",
    "notify", "number", "office", "online", "open", "operate", "optimize", "option",
    "order", "organize", "origin", "outcome", "outlook", "output", "outsource",
    "over", "overview", "owner", "pace", "pack", "page", "panel", "paper",
    "parent", "partner", "pass", "password", "path", "patient", "pattern", "pay",
    "payment", "payroll", "people", "perform", "person", "photo", "pick", "pilot",
    "pipeline", "plan", "platform", "play", "plot", "point", "policy", "pool",
    "portal", "portfolio", "position", "post", "power", "practice", "predict", "prep",
    "present", "press", "preview", "price", "prime", "print", "priority", "privacy",
    "prize", "process", "product", "profile", "profit", "program", "progress", "project",
    "promise", "promo", "promote", "proof", "property", "proposal", "prospect", "protect",
    "protocol", "provider", "provision", "proxy", "public", "publish", "purchase", "pure",
    "push", "qualify", "quality", "quarter", "query", "quest", "queue", "quick",
    "quiz", "quote", "rack", "rank", "rapid", "rate", "ratio", "reach",
    "read", "ready", "real", "realize", "receipt", "receive", "recent", "record",
    "recruit", "reduce", "refer", "refine", "refresh", "region", "register", "regular",
    "relate", "release", "relevant", "reliable", "relief", "reload", "remain", "remind",
    "remote", "remove", "render", "renew", "rent", "repair", "repeat", "replace",
    "reply", "report", "represent", "request", "require", "research", "reserve", "reset",
    "resident", "resource", "respond", "response", "result", "resume", "retail", "retain",
    "retrieve", "return", "revenue", "review", "revise", "reward", "rich", "right",
    "risk", "robot", "role", "room", "roster", "rotate", "route", "routine",
    "row", "run", "safe", "sale", "sample", "save", "scale", "scan",
    "scene", "schedule", "scheme", "school", "scope", "score", "screen", "script",
    "scroll", "search", "season", "seat", "second", "secret", "section", "secure",
    "segment", "select", "self", "sell", "send", "senior", "sense", "serial",
    "series", "serve", "server", "service", "session", "setup", "share", "shelf",
    "shift", "ship", "shop", "show", "side", "sight", "sign", "signal",
    "simple", "single", "site", "size", "skill", "skip", "slide", "smart",
    "smooth", "snap", "social", "soft", "solution", "solve", "soon", "sort",
    "sound", "source", "space", "spark", "speak", "special", "spectrum", "speed",
    "spend", "split", "sponsor", "spot", "spread", "spring", "sprint", "squad",
    "square", "stable", "stack", "staff", "stage", "stamp", "stand", "standard",
    "star", "start", "state", "static", "station", "status", "stay", "step",
    "stock", "stop", "storage", "store", "story", "straight", "strategy", "stream",
    "street", "stretch", "strike", "string", "strip", "strong", "structure", "student",
    "studio", "study", "style", "submit", "subscribe", "succeed", "success", "suggest",
    "suit", "suite", "summary", "summit", "super", "supply", "support", "surface",
    "survey", "sustain", "swap", "switch", "symbol", "sync", "system", "table",
    "tag", "take", "talent", "talk", "tap", "target", "task", "taste",
    "tax", "teach", "team", "tech", "template", "tempo", "tenant", "tend",
    "term", "terminal", "territory", "test", "text", "thank", "theater", "theme",
    "theory", "think", "third", "thread", "threshold", "thrive", "through", "throw",
    "ticket", "tier", "time", "timeline", "timer", "tip", "title", "today",
    "token", "tomorrow", "tool", "topic", "total", "touch", "tour", "tower",
    "town", "trace", "track", "trade", "traffic", "trail", "train", "transfer",
    "transform", "transit", "translate", "transmit", "transport", "travel", "treasure", "treat",
    "tree", "trend", "trial", "tribe", "trigger", "trim", "trip", "trophy",
    "trouble", "trust", "truth", "try", "tune", "tunnel", "turn", "tutorial",
    "twin", "type", "ultimate", "ultra", "umbrella", "under", "understand", "undo",
    "unfold", "uniform", "union", "unique", "unit", "unite", "unity", "universal",
    "universe", "unlock", "unpack", "update", "upgrade", "upload", "upper", "urban",
    "urgent", "usage", "use", "user", "usual", "utility", "utilize", "vacation",
    "valid", "validate", "valley", "valuable", "value", "variable", "variety", "vary",
    "vault", "vector", "vehicle", "velocity", "vendor", "venture", "venue", "verify",
    "version", "vertical", "vessel", "veteran", "via", "vibrant", "video", "view",
    "villa", "vintage", "virtual", "visa", "visible", "vision", "visit", "visual",
    "vital", "vocab", "voice", "void", "volume", "volunteer", "vote", "voucher",
    "voyage", "wage", "wait", "wake", "walk", "wall", "wallet", "want",
    "ward", "ware", "warehouse", "warm", "warn", "warrant", "warranty", "wash",
    "watch", "water", "wave", "way", "wealth", "weapon", "wear", "weather",
    "web", "website", "wedding", "week", "welcome", "welfare", "well", "wellness",
    "west", "wheel", "when", "where", "while", "white", "whole", "wholesale",
    "width", "wifi", "wiki", "wild", "will", "win", "wind", "window",
    "wine", "wing", "winner", "winter", "wire", "wisdom", "wise", "wish",
    "with", "within", "without", "witness", "wizard", "wonder", "wood", "word",
    "work", "workflow", "workforce", "workplace", "workshop", "world", "worth", "wrap",
    "write", "wrong", "year", "yellow", "yes", "yesterday", "yield", "young",
    "youth", "zero", "zone", "zoom"
]

prefixes = ["my", "get", "use", "go", "try", "the", "new", "top", "best", "your"]
suffixes = ["io", "app", "ly", "ai", "co", "tech", "pro", "hq", "hub", "now"]
tlds = ["com", "io", "co", "net", "app", "tech", "ai", "ly", "me", "cc"]

domains = set()

# Pattern 1: word.tld
for word in business_words[:500]:
    for tld in tlds[:5]:
        domains.add(f"{word}.{tld}")

# Pattern 2: prefix + word.com
for prefix in prefixes:
    for word in business_words[:200]:
        domains.add(f"{prefix}{word}.com")
        domains.add(f"{prefix}-{word}.com")

# Pattern 3: word + suffix.tld
for word in business_words[:300]:
    for suffix in suffixes:
        domains.add(f"{word}{suffix}.com")
        domains.add(f"{word}.{suffix}")

# Convert to sorted list
domains_list = sorted(list(domains))[:10000]

# Write to CSV
with open('domains_10k.csv', 'w') as f:
    f.write('domain\n')
    for domain in domains_list:
        f.write(f'{domain}\n')

print(f"✅ Created domains_10k.csv with {len(domains_list)} domains")
