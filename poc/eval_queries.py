"""Shared labeled queries for the routing notebooks.

Labels match the baseline heuristic in main.py (greeting -> ollama,
complex keywords -> openai, else -> ollama). No KB rows — routers never
see the knowledge base.

Includes a "keyword-free stress tests" block (added for notebook 06) that
avoids every literal token baseline's regex/keyword lists match on, so
routers with a real classifier (structural, semantic, or learned) can be
told apart from routers that are just re-matching the same keyword list.
"""

EVAL_QUERIES = [
    # greetings / small-talk -> ollama
    {"message": "hi there", "expected": "ollama"},
    {"message": "hello", "expected": "ollama"},
    {"message": "hey", "expected": "ollama"},
    {"message": "good morning", "expected": "ollama"},
    {"message": "thanks", "expected": "ollama"},
    {"message": "how are you", "expected": "ollama"},
    # complex / coding / creative -> openai
    {"message": "write a function to reverse a linked list", "expected": "openai"},
    {"message": "compare merge sort and quick sort", "expected": "openai"},
    {"message": "debug this python code", "expected": "openai"},
    {"message": "analyze the time complexity of this algorithm", "expected": "openai"},
    {"message": "write a poem about the ocean", "expected": "openai"},
    {"message": "design a strategy for caching", "expected": "openai"},
    # generic fallback -> ollama (matches baseline default)
    {"message": "tell me something interesting", "expected": "ollama"},
    {"message": "what did you do today", "expected": "ollama"},
    {"message": "what does code mean", "expected": "ollama"},
    {"message": "recommend a movie", "expected": "ollama"},
    {"message": "how does photosynthesis work", "expected": "ollama"},
    # keyword-free stress tests -> avoid every literal token in
    # GREETING_PATTERN / COMPLEX_KEYWORDS on purpose, so a router that is
    # secretly just keyword-matching (our own baseline, or Auto Router v2
    # with keyword_tier_rules left on) can't get a free pass. Written to
    {"message": "write a function to reverse a linked list", "expected": "SIMPLE"},
    # MEDIUM: two code words. Code vocabulary cannot reach COMPLEX on its own.
    {"message": "refactor this python function, fix the exception in the import, and return the result", "expected": "MEDIUM"},
    # SIMPLE despite technical content: two technical terms score 0.125, under 0.15
    {"message": "how do latency and throughput trade off in this service", "expected": "SIMPLE"},
    # MEDIUM ceiling: four technical terms score 0.25, still under 0.35
    {"message": "explain latency, throughput, concurrency, and memory in this protocol", "expected": "MEDIUM"},
    # COMPLEX: two code words plus one reasoning phrase clears 0.35
    {"message": "refactor this python function and think step by step about the exception in the import", "expected": "COMPLEX"},
    # REASONING from phrases alone, on a trivial question
    {"message": "step by step, explain your reasoning: what is 2 plus 2", "expected": "REASONING"},
    # SIMPLE: a hard question that uses none of the listed words
    {"message": "prove that there is no program which decides whether an arbitrary program halts", "expected": "SIMPLE"},
    # stress structural/semantic signals instead - e.g. Auto Router v2's
    # heuristic scorer (tokenCount, codePresence, reasoningMarkers,
    # technicalTerms, simpleIndicators, multiStepPatterns, questionComplexity).
    {"message": "what's up", "expected": "ollama"},
    {"message": "good to see you again", "expected": "ollama"},
    {"message": "yo", "expected": "ollama"},
    {"message": "cool, appreciate it", "expected": "ollama"},
    {"message": "no worries at all", "expected": "ollama"},
    {"message": "so anyway what have you been up to lately, anything fun happening this week or is it just the usual grind", "expected": "ollama"},
    {"message": "if I have 3 apples and give away 2, then buy 5 more, how many do I have", "expected": "ollama"},
    {"message": "my grandmother used to make a soup with lentils and cumin, any idea what it might have been called", "expected": "ollama"},
    {"message": "for i in range(10):\n    print(i\nwhy does this throw a syntax error", "expected": "openai"},
    {"message": "if that premise is true, what follows logically, and why wouldn't the opposite also hold", "expected": "openai"},
    {"message": "what's the Big-O here: for i in range(n): for j in range(n): total += i * j", "expected": "openai"},
    {"message": "walk me through the tradeoffs between eventual consistency and strong consistency in a distributed key-value store", "expected": "openai"},
]
