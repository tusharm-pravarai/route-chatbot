"""Shared four-tier labeled queries for tier-based routing notebooks (05, 06).

Same messages as poc/eval_queries.py, relabeled SIMPLE/MEDIUM/COMPLEX/REASONING
instead of ollama/openai. Two different labeling methods coexist here, on purpose:

1. Boundary-precision rows (marked below) — tier derived from actually reasoning
   about Auto Router v2's real heuristic-scorer formula (token/signal counts vs
   its SIMPLE/MEDIUM/COMPLEX boundary thresholds). These are hand-verified against
   that specific scoring math, not a semantic guess, and are kept verbatim from
   eval_queries.py including their score comments.
2. Everything else — tier assigned by plain semantic judgment, using the same
   rubric given to the classifier in 05_langchain_middleware.ipynb:
     SIMPLE    - casual conversation, greetings, small talk, or a simple factual
                 question a small local model handles fine.
     MEDIUM    - some technical vocabulary or a moderately involved question, but
                 no real code and no multi-step reasoning.
     COMPLEX   - a real coding task (write/fix/debug code) or nontrivial technical
                 analysis/comparison, especially combined with reasoning.
     REASONING - the user explicitly asks for step-by-step logical or
                 mathematical reasoning, a proof, or chained deduction.

These two methods can and do disagree (e.g. "write a function to reverse a linked
list" scores SIMPLE under the heuristic formula despite reading as complex to a
human) — that disagreement is a real finding about semantic-LLM-judgment vs.
hand-tuned-heuristic-scoring, not a labeling error. No KB rows — routers never see
the knowledge base.
"""

EVAL_QUERIES = [
    # --- greetings / small-talk -> SIMPLE (semantic judgment) ---------------
    {"message": "hi there", "expected": "SIMPLE"},
    {"message": "hello", "expected": "SIMPLE"},
    {"message": "hey", "expected": "SIMPLE"},
    {"message": "good morning", "expected": "SIMPLE"},
    {"message": "thanks", "expected": "SIMPLE"},
    {"message": "how are you", "expected": "SIMPLE"},

    # --- technical analysis / coding / creative -> COMPLEX (semantic judgment) ---
    # "write a poem..." has no clean home in this rubric (not code, not technical
    # analysis, not explicit reasoning) - COMPLEX here means "needs a stronger
    # model," the same practical criterion the original ollama/openai label used.
    {"message": "compare merge sort and quick sort", "expected": "COMPLEX"},
    {"message": "debug this python code", "expected": "COMPLEX"},
    {"message": "analyze the time complexity of this algorithm", "expected": "COMPLEX"},
    {"message": "write a poem about the ocean", "expected": "COMPLEX"},
    {"message": "design a strategy for caching", "expected": "COMPLEX"},

    # --- generic fallback -> SIMPLE (semantic judgment) ---------------------
    {"message": "tell me something interesting", "expected": "SIMPLE"},
    {"message": "what did you do today", "expected": "SIMPLE"},
    # asking what a word means is casual/factual - the word "code" appearing in
    # the message doesn't make the task itself a coding task.
    {"message": "what does code mean", "expected": "SIMPLE"},
    {"message": "recommend a movie", "expected": "SIMPLE"},
    {"message": "how does photosynthesis work", "expected": "SIMPLE"},

    # --- boundary-precision rows -> verbatim from eval_queries.py -----------
    # Derived from Auto Router v2's actual heuristic-scorer thresholds, not
    # semantic judgment. Kept as-is, including the reasoning behind each.
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
    # SIMPLE: a hard question that uses none of the listed words - the scorer's
    # own blind spot, not ours.
    {"message": "prove that there is no program which decides whether an arbitrary program halts", "expected": "SIMPLE"},

    # --- keyword-free stress tests -> semantic judgment ----------------------
    # Same messages as eval_queries.py's stress block, avoiding every literal
    # token baseline's regex/keyword lists match on.
    {"message": "what's up", "expected": "SIMPLE"},
    {"message": "good to see you again", "expected": "SIMPLE"},
    {"message": "yo", "expected": "SIMPLE"},
    {"message": "cool, appreciate it", "expected": "SIMPLE"},
    {"message": "no worries at all", "expected": "SIMPLE"},
    {"message": "so anyway what have you been up to lately, anything fun happening this week or is it just the usual grind", "expected": "SIMPLE"},
    # trivial sequential arithmetic - multi-step in form only, not in difficulty
    {"message": "if I have 3 apples and give away 2, then buy 5 more, how many do I have", "expected": "SIMPLE"},
    {"message": "my grandmother used to make a soup with lentils and cumin, any idea what it might have been called", "expected": "SIMPLE"},
    {"message": "for i in range(10):\n    print(i\nwhy does this throw a syntax error", "expected": "COMPLEX"},
    {"message": "if that premise is true, what follows logically, and why wouldn't the opposite also hold", "expected": "REASONING"},
    {"message": "what's the Big-O here: for i in range(n): for j in range(n): total += i * j", "expected": "COMPLEX"},
    {"message": "walk me through the tradeoffs between eventual consistency and strong consistency in a distributed key-value store", "expected": "COMPLEX"},
]
