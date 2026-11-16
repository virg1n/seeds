"""Our labelled benchmark for Part A: tasks x algorithms x textual variants.

Every task has an input generator gen(n, rng) -> args tuple, a ladder of sizes and several
algorithms, each written in >= 2 deliberately different styles (loop kind, helper functions,
library vs hand-written, recursion vs iteration where the *algorithm* stays the same).
Pairs inside a task: same algorithm label -> "same" (positive for similarity),
otherwise "different". Hard positives (e.g. bisect vs hand-written binary search,
top-down vs bottom-up DP) are labelled "same" on purpose.
Entry point of every program: solve(*args).
"""
from __future__ import annotations

import random

P = {}  # task -> list of (algo, code)
TASKS = {}


def task(name, gen, sizes, test_sizes=(3, 5, 8), extend=4):
    # the traced ladder stops at the line-event cap; the extra (bigger) sizes are used by the
    # untraced timing runs, which reveal work hidden inside C builtins (sorted, set, `in list` ...)
    sizes = list(sizes) + [sizes[-1] * 2 ** k for k in range(1, extend + 1)]
    TASKS[name] = {"gen": gen, "sizes": sizes, "test_sizes": list(test_sizes)}
    P[name] = []


def prog(name, algo, code):
    P[name].append((algo, code.strip("\n") + "\n"))


# =========================================================== 1. sort
task("sort", lambda n, r: ([r.randint(0, 10 * n) for _ in range(n)],), [8, 16, 32, 64, 128, 256, 512, 1024])
prog("sort", "bubble", """
def solve(a):
    a = list(a)
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a
""")
prog("sort", "bubble", """
def solve(arr):
    res = arr[:]
    changed = True
    end = len(res)
    while changed:
        changed = False
        k = 1
        while k < end:
            if res[k - 1] > res[k]:
                tmp = res[k]; res[k] = res[k - 1]; res[k - 1] = tmp
                changed = True
            k += 1
        end -= 1
    return res
""")
prog("sort", "insertion", """
def solve(a):
    a = list(a)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a
""")
prog("sort", "insertion", """
def solve(items):
    out = []
    for x in items:
        pos = len(out)
        out.append(x)
        while pos > 0 and out[pos - 1] > x:
            out[pos], out[pos - 1] = out[pos - 1], out[pos]
            pos -= 1
    return out
""")
prog("sort", "merge", """
def merge(l, r):
    res, i, j = [], 0, 0
    while i < len(l) and j < len(r):
        if l[i] <= r[j]:
            res.append(l[i]); i += 1
        else:
            res.append(r[j]); j += 1
    return res + l[i:] + r[j:]

def solve(a):
    if len(a) <= 1:
        return list(a)
    mid = len(a) // 2
    return merge(solve(a[:mid]), solve(a[mid:]))
""")
prog("sort", "merge", """
def solve(a):
    def msort(xs):
        if len(xs) < 2:
            return xs
        h = len(xs) // 2
        left, right = msort(xs[:h]), msort(xs[h:])
        out = []
        while left and right:
            out.append(left.pop(0) if left[0] <= right[0] else right.pop(0))
        out.extend(left or right)
        return out
    return msort(list(a))
""")
prog("sort", "quick", """
def solve(a):
    if len(a) <= 1:
        return list(a)
    p = a[len(a) // 2]
    return solve([x for x in a if x < p]) + [x for x in a if x == p] + solve([x for x in a if x > p])
""")
prog("sort", "quick", """
import random
def solve(a):
    a = list(a)
    def part(lo, hi):
        k = random.randint(lo, hi)
        a[k], a[hi] = a[hi], a[k]
        pivot, i = a[hi], lo
        for j in range(lo, hi):
            if a[j] < pivot:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        return i
    def qs(lo, hi):
        if lo < hi:
            m = part(lo, hi)
            qs(lo, m - 1)
            qs(m + 1, hi)
    qs(0, len(a) - 1)
    return a
""")
prog("sort", "heap", """
import heapq
def solve(a):
    h = list(a)
    heapq.heapify(h)
    return [heapq.heappop(h) for _ in range(len(h))]
""")
prog("sort", "heap", """
def solve(a):
    a = list(a)
    n = len(a)
    def sift(i, size):
        while True:
            l, r, big = 2 * i + 1, 2 * i + 2, i
            if l < size and a[l] > a[big]: big = l
            if r < size and a[r] > a[big]: big = r
            if big == i: return
            a[i], a[big] = a[big], a[i]
            i = big
    for i in range(n // 2 - 1, -1, -1):
        sift(i, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift(0, end)
    return a
""")
prog("sort", "counting", """
def solve(a):
    if not a:
        return []
    lo, hi = min(a), max(a)
    cnt = [0] * (hi - lo + 1)
    for x in a:
        cnt[x - lo] += 1
    out = []
    for v, c in enumerate(cnt):
        out.extend([v + lo] * c)
    return out
""")
prog("sort", "counting", """
def solve(a):
    freq = {}
    for x in a:
        freq[x] = freq.get(x, 0) + 1
    res = []
    if a:
        for v in range(min(a), max(a) + 1):
            if v in freq:
                for _ in range(freq[v]):
                    res.append(v)
    return res
""")

# =========================================================== 2. primes up to n
task("primes", lambda n, r: (n,), [16, 32, 64, 128, 256, 512, 1024, 2048], test_sizes=(10, 30, 50))
prog("primes", "trial_all", """
def solve(n):
    res = []
    for k in range(2, n + 1):
        for d in range(2, k):
            if k % d == 0:
                break
        else:
            res.append(k)
    return res
""")
prog("primes", "trial_all", """
def is_prime(k):
    if k < 2:
        return False
    d = 2
    while d < k:
        if k % d == 0:
            return False
        d += 1
    return True

def solve(n):
    return [k for k in range(n + 1) if is_prime(k)]
""")
prog("primes", "trial_sqrt", """
def solve(n):
    out = []
    for k in range(2, n + 1):
        i, ok = 2, True
        while i * i <= k:
            if k % i == 0:
                ok = False
                break
            i += 1
        if ok:
            out.append(k)
    return out
""")
prog("primes", "trial_sqrt", """
import math
def solve(n):
    def prime(x):
        return x > 1 and all(x % d for d in range(2, math.isqrt(x) + 1))
    return list(filter(prime, range(n + 1)))
""")
prog("primes", "sieve", """
def solve(n):
    if n < 2:
        return []
    is_p = [True] * (n + 1)
    is_p[0] = is_p[1] = False
    i = 2
    while i * i <= n:
        if is_p[i]:
            is_p[i * i::i] = [False] * len(range(i * i, n + 1, i))
        i += 1
    return [i for i, v in enumerate(is_p) if v]
""")
prog("primes", "sieve", """
def solve(n):
    composite = set()
    primes = []
    for i in range(2, n + 1):
        if i not in composite:
            primes.append(i)
            for j in range(i * i, n + 1, i):
                composite.add(j)
    return primes
""")
prog("primes", "trial_by_primes", """
def solve(n):
    ps = []
    for k in range(2, n + 1):
        if all(k % p for p in ps if p * p <= k):
            ps.append(k)
    return ps
""")
prog("primes", "trial_by_primes", """
def solve(n):
    found = []
    k = 2
    while k <= n:
        good = True
        for p in found:
            if p * p > k:
                break
            if k % p == 0:
                good = False
                break
        if good:
            found.append(k)
        k += 1
    return found
""")


# =========================================================== 3. search in sorted list
def _gen_search(n, r):
    a = sorted(r.sample(range(4 * n + 4), n))
    x = r.choice(a) if r.random() < 0.7 else -1
    return (a, x)


task("search", _gen_search, [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096])
prog("search", "linear", """
def solve(a, x):
    for i, v in enumerate(a):
        if v == x:
            return i
    return -1
""")
prog("search", "linear", """
def solve(arr, target):
    i = 0
    while i < len(arr):
        if arr[i] == target:
            return i
        i += 1
    return -1
""")
prog("search", "binary", """
def solve(a, x):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""")
prog("search", "binary", """
def solve(arr, target):
    def go(l, r):
        if l > r:
            return -1
        m = l + (r - l) // 2
        if arr[m] == target:
            return m
        return go(m + 1, r) if arr[m] < target else go(l, m - 1)
    return go(0, len(arr) - 1)
""")
prog("search", "binary", """
from bisect import bisect_left
def solve(a, x):
    i = bisect_left(a, x)
    return i if i < len(a) and a[i] == x else -1
""")
prog("search", "jump", """
import math
def solve(a, x):
    n = len(a)
    step = int(math.sqrt(n)) or 1
    prev = 0
    while prev < n and a[min(n, prev + step) - 1] < x:
        prev += step
    for i in range(prev, min(n, prev + step)):
        if a[i] == x:
            return i
    return -1
""")
prog("search", "jump", """
def solve(arr, target):
    n = len(arr)
    block = max(1, int(n ** 0.5))
    start = 0
    while start + block < n and arr[start + block - 1] < target:
        start += block
    end = min(n, start + block)
    j = start
    while j < end:
        if arr[j] == target:
            return j
        j += 1
    return -1
""")

# =========================================================== 4. fibonacci mod
task("fib", lambda n, r: (n,), [8, 16, 24, 32, 64, 128, 256, 512, 1024], test_sizes=(1, 7, 15))
prog("fib", "naive_rec", """
def solve(n):
    if n < 2:
        return n
    return (solve(n - 1) + solve(n - 2)) % 1000000007
""")
prog("fib", "naive_rec", """
MOD = 10**9 + 7
def fib(k):
    return k if k <= 1 else fib(k - 2) + fib(k - 1)
def solve(n):
    return fib(n) % MOD
""")
prog("fib", "memo", """
from functools import lru_cache
@lru_cache(maxsize=None)
def f(n):
    return n if n < 2 else (f(n - 1) + f(n - 2)) % 1000000007
def solve(n):
    return f(n)
""")
prog("fib", "memo", """
def solve(n):
    memo = {0: 0, 1: 1}
    def go(k):
        if k not in memo:
            memo[k] = (go(k - 1) + go(k - 2)) % 1000000007
        return memo[k]
    return go(n)
""")
prog("fib", "iter_dp", """
def solve(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, (a + b) % 1000000007
    return a
""")
prog("fib", "iter_dp", """
def solve(n):
    dp = [0] * (n + 2)
    dp[1] = 1
    i = 2
    while i <= n:
        dp[i] = (dp[i - 1] + dp[i - 2]) % 1000000007
        i += 1
    return dp[n]
""")
prog("fib", "matrix_pow", """
M = 1000000007
def mul(A, B):
    return [[(A[0][0]*B[0][0] + A[0][1]*B[1][0]) % M, (A[0][0]*B[0][1] + A[0][1]*B[1][1]) % M],
            [(A[1][0]*B[0][0] + A[1][1]*B[1][0]) % M, (A[1][0]*B[0][1] + A[1][1]*B[1][1]) % M]]
def mpow(A, p):
    if p == 1:
        return A
    H = mpow(A, p // 2)
    H = mul(H, H)
    return mul(H, A) if p % 2 else H
def solve(n):
    if n == 0:
        return 0
    return mpow([[1, 1], [1, 0]], n)[0][1]
""")
prog("fib", "matrix_pow", """
def solve(n):
    MOD = 10**9 + 7
    def mm(x, y):
        return [[sum(x[i][k] * y[k][j] for k in range(2)) % MOD for j in range(2)] for i in range(2)]
    result = [[1, 0], [0, 1]]
    base = [[1, 1], [1, 0]]
    while n > 0:
        if n & 1:
            result = mm(result, base)
        base = mm(base, base)
        n >>= 1
    return result[0][1]
""")


# =========================================================== 5. two-sum exists
def _gen_two_sum(n, r):
    a = [r.randint(0, 50 * n) for _ in range(n)]
    return (a, -1)  # worst case: no pair exists


task("two_sum", _gen_two_sum, [8, 16, 32, 64, 128, 256, 512, 1024, 2048])
prog("two_sum", "brute", """
def solve(a, t):
    n = len(a)
    for i in range(n):
        for j in range(i + 1, n):
            if a[i] + a[j] == t:
                return True
    return False
""")
prog("two_sum", "brute", """
from itertools import combinations
def solve(nums, target):
    return any(x + y == target for x, y in combinations(nums, 2))
""")
prog("two_sum", "hash", """
def solve(a, t):
    seen = set()
    for x in a:
        if t - x in seen:
            return True
        seen.add(x)
    return False
""")
prog("two_sum", "hash", """
def solve(nums, target):
    index = {}
    for i, v in enumerate(nums):
        if target - v in index:
            return True
        index[v] = i
    return False
""")
prog("two_sum", "two_pointers", """
def solve(a, t):
    b = sorted(a)
    i, j = 0, len(b) - 1
    while i < j:
        s = b[i] + b[j]
        if s == t:
            return True
        if s < t:
            i += 1
        else:
            j -= 1
    return False
""")
prog("two_sum", "two_pointers", """
def solve(nums, target):
    nums = list(nums)
    nums.sort()
    left, right = 0, len(nums) - 1
    found = False
    while left < right and not found:
        cur = nums[left] + nums[right]
        found = cur == target
        left += cur < target
        right -= cur > target
    return found
""")
prog("two_sum", "sort_bsearch", """
import bisect
def solve(a, t):
    b = sorted(a)
    for i, x in enumerate(b):
        k = bisect.bisect_left(b, t - x, i + 1)
        if k < len(b) and b[k] == t - x:
            return True
    return False
""")
prog("two_sum", "sort_bsearch", """
def solve(nums, target):
    s = sorted(nums)
    n = len(s)
    for i in range(n):
        need = target - s[i]
        lo, hi = i + 1, n - 1
        while lo <= hi:
            m = (lo + hi) // 2
            if s[m] == need:
                return True
            if s[m] < need:
                lo = m + 1
            else:
                hi = m - 1
    return False
""")

# =========================================================== 6. count distinct
task("distinct", lambda n, r: ([r.randint(0, n) for _ in range(n)],), [8, 16, 32, 64, 128, 256, 512, 1024, 2048])
prog("distinct", "quadratic", """
def solve(a):
    cnt = 0
    for i in range(len(a)):
        dup = False
        for j in range(i):
            if a[j] == a[i]:
                dup = True
                break
        if not dup:
            cnt += 1
    return cnt
""")
prog("distinct", "quadratic", """
def solve(items):
    uniq = []
    for x in items:
        if x not in uniq:
            uniq.append(x)
    return len(uniq)
""")
prog("distinct", "hash", """
def solve(a):
    return len(set(a))
""")
prog("distinct", "hash", """
def solve(items):
    seen = set()
    for x in items:
        seen.add(x)
    return len(seen)
""")
prog("distinct", "sort_scan", """
def solve(a):
    b = sorted(a)
    return sum(1 for i in range(len(b)) if i == 0 or b[i] != b[i - 1])
""")
prog("distinct", "sort_scan", """
def solve(items):
    xs = list(items)
    xs.sort()
    count, prev = 0, None
    for x in xs:
        if count == 0 or x != prev:
            count += 1
            prev = x
    return count
""")

# =========================================================== 7. max subarray
task("max_subarray", lambda n, r: ([r.randint(-50, 50) for _ in range(n)],), [8, 16, 32, 64, 128, 256, 512, 1024])
prog("max_subarray", "brute", """
def solve(a):
    best = a[0]
    for i in range(len(a)):
        s = 0
        for j in range(i, len(a)):
            s += a[j]
            best = max(best, s)
    return best
""")
prog("max_subarray", "brute", """
def solve(nums):
    pre = [0]
    for x in nums:
        pre.append(pre[-1] + x)
    n = len(nums)
    return max(pre[j] - pre[i] for i in range(n) for j in range(i + 1, n + 1))
""")
prog("max_subarray", "kadane", """
def solve(a):
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
""")
prog("max_subarray", "kadane", """
def solve(nums):
    best = float('-inf')
    run = 0
    for v in nums:
        run += v
        if run > best:
            best = run
        if run < 0:
            run = 0
    return best
""")
prog("max_subarray", "divide_conquer", """
def solve(a):
    def rec(lo, hi):
        if lo == hi:
            return a[lo]
        mid = (lo + hi) // 2
        s, left = 0, float('-inf')
        for i in range(mid, lo - 1, -1):
            s += a[i]
            left = max(left, s)
        s, right = 0, float('-inf')
        for i in range(mid + 1, hi + 1):
            s += a[i]
            right = max(right, s)
        return max(rec(lo, mid), rec(mid + 1, hi), left + right)
    return rec(0, len(a) - 1)
""")
prog("max_subarray", "divide_conquer", """
def cross(nums, l, m, r):
    best_l, acc = nums[m], 0
    k = m
    while k >= l:
        acc += nums[k]
        best_l = max(best_l, acc)
        k -= 1
    best_r, acc = nums[m + 1], 0
    k = m + 1
    while k <= r:
        acc += nums[k]
        best_r = max(best_r, acc)
        k += 1
    return best_l + best_r

def helper(nums, l, r):
    if l == r:
        return nums[l]
    m = (l + r) // 2
    return max(helper(nums, l, m), helper(nums, m + 1, r), cross(nums, l, m, r))

def solve(nums):
    return helper(nums, 0, len(nums) - 1)
""")


# =========================================================== 8. LCS length
def _gen_lcs(n, r):
    return ("".join(r.choice("abc") for _ in range(n)), "".join(r.choice("abc") for _ in range(n)))


task("lcs", _gen_lcs, [4, 6, 8, 10, 12, 16, 32, 64, 128, 256], test_sizes=(2, 4, 6))
prog("lcs", "dp", """
def solve(s, t):
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]
""")
prog("lcs", "dp", """
def solve(a, b):
    prev = [0] * (len(b) + 1)
    for ch in a:
        cur = [0]
        for j, ch2 in enumerate(b):
            cur.append(prev[j] + 1 if ch == ch2 else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]
""")
prog("lcs", "dp", """
from functools import lru_cache
def solve(s, t):
    @lru_cache(maxsize=None)
    def go(i, j):
        if i == len(s) or j == len(t):
            return 0
        if s[i] == t[j]:
            return 1 + go(i + 1, j + 1)
        return max(go(i + 1, j), go(i, j + 1))
    return go(0, 0)
""")
prog("lcs", "naive_rec", """
def solve(s, t):
    if not s or not t:
        return 0
    if s[-1] == t[-1]:
        return 1 + solve(s[:-1], t[:-1])
    return max(solve(s[:-1], t), solve(s, t[:-1]))
""")
prog("lcs", "naive_rec", """
def solve(a, b):
    def rec(i, j):
        if i >= len(a) or j >= len(b):
            return 0
        best = rec(i + 1, j)
        best = max(best, rec(i, j + 1))
        if a[i] == b[j]:
            best = max(best, 1 + rec(i + 1, j + 1))
        return best
    return rec(0, 0)
""")

# =========================================================== 9. gcd
task("gcd", lambda n, r: (2 * n + r.randint(1, 5), n), [16, 64, 256, 1024, 4096, 16384, 65536], test_sizes=(5, 12, 30))
prog("gcd", "euclid", """
def solve(a, b):
    while b:
        a, b = b, a % b
    return a
""")
prog("gcd", "euclid", """
def solve(x, y):
    return x if y == 0 else solve(y, x % y)
""")
prog("gcd", "subtraction", """
def solve(a, b):
    while a != b:
        if a > b:
            a -= b
        else:
            b -= a
    return a
""")
prog("gcd", "subtraction", """
def solve(x, y):
    big, small = max(x, y), min(x, y)
    while small:
        big = big - small
        if big < small:
            big, small = small, big
    return big
""")
prog("gcd", "brute", """
def solve(a, b):
    g = 1
    for d in range(1, min(a, b) + 1):
        if a % d == 0 and b % d == 0:
            g = d
    return g
""")
prog("gcd", "brute", """
def solve(x, y):
    d = min(x, y)
    while d > 1:
        if x % d == 0 and y % d == 0:
            return d
        d -= 1
    return 1
""")

# =========================================================== 10. power mod
task("powmod", lambda n, r: (r.randint(2, 1000), n, 1000000007), [16, 64, 256, 1024, 4096, 16384, 65536],
     test_sizes=(0, 5, 13))
prog("powmod", "naive", """
def solve(a, b, m):
    r = 1 % m
    for _ in range(b):
        r = r * a % m
    return r
""")
prog("powmod", "naive", """
def solve(base, exp, mod):
    acc = 1 % mod
    while exp > 0:
        acc = (acc * base) % mod
        exp -= 1
    return acc
""")
prog("powmod", "fast_pow", """
def solve(a, b, m):
    r = 1 % m
    a %= m
    while b:
        if b & 1:
            r = r * a % m
        a = a * a % m
        b >>= 1
    return r
""")
prog("powmod", "fast_pow", """
def solve(base, exp, mod):
    if exp == 0:
        return 1 % mod
    half = solve(base, exp // 2, mod)
    sq = half * half % mod
    return sq * base % mod if exp % 2 else sq
""")


# =========================================================== 11. anagram
def _gen_anagram(n, r):
    s = "".join(r.choice("abcdefghij") for _ in range(n))
    t = list(s)
    r.shuffle(t)
    if r.random() < 0.4:
        t[0] = "z"
    return (s, "".join(t))


task("anagram", _gen_anagram, [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096])
prog("anagram", "sort", """
def solve(s, t):
    return sorted(s) == sorted(t)
""")
prog("anagram", "sort", """
def solve(a, b):
    if len(a) != len(b):
        return False
    x = ''.join(sorted(a))
    y = ''.join(sorted(b))
    return x == y
""")
prog("anagram", "count", """
def solve(s, t):
    if len(s) != len(t):
        return False
    cnt = {}
    for c in s:
        cnt[c] = cnt.get(c, 0) + 1
    for c in t:
        if cnt.get(c, 0) == 0:
            return False
        cnt[c] -= 1
    return True
""")
prog("anagram", "count", """
from collections import Counter
def solve(a, b):
    return Counter(a) == Counter(b)
""")
prog("anagram", "count", """
def solve(s, t):
    f = [0] * 26
    for c in s:
        f[ord(c) - 97] += 1
    for c in t:
        f[ord(c) - 97] -= 1
    return all(v == 0 for v in f)
""")
prog("anagram", "remove", """
def solve(s, t):
    rest = list(t)
    for c in s:
        if c in rest:
            rest.remove(c)
        else:
            return False
    return not rest
""")
prog("anagram", "remove", """
def solve(a, b):
    if len(a) != len(b):
        return False
    for ch in a:
        k = b.find(ch)
        if k < 0:
            return False
        b = b[:k] + b[k + 1:]
    return b == ''
""")


# =========================================================== 12. k-th smallest
def _gen_kth(n, r):
    return ([r.randint(0, 10 * n) for _ in range(n)], max(1, n // 2))


task("kth", _gen_kth, [8, 16, 32, 64, 128, 256, 512, 1024, 2048])
prog("kth", "sort", """
def solve(a, k):
    return sorted(a)[k - 1]
""")
prog("kth", "sort", """
def solve(nums, k):
    b = list(nums)
    b.sort()
    return b[k - 1]
""")
prog("kth", "heap", """
import heapq
def solve(a, k):
    return heapq.nsmallest(k, a)[-1]
""")
prog("kth", "heap", """
import heapq
def solve(nums, k):
    h = []
    for x in nums:
        heapq.heappush(h, -x)
        if len(h) > k:
            heapq.heappop(h)
    return -h[0]
""")
prog("kth", "quickselect", """
def solve(a, k):
    pivot = a[len(a) // 2]
    lo = [x for x in a if x < pivot]
    eq = [x for x in a if x == pivot]
    if k <= len(lo):
        return solve(lo, k)
    if k <= len(lo) + len(eq):
        return pivot
    return solve([x for x in a if x > pivot], k - len(lo) - len(eq))
""")
prog("kth", "quickselect", """
import random
def solve(nums, k):
    arr = list(nums)
    lo, hi, target = 0, len(arr) - 1, k - 1
    while True:
        p = random.randint(lo, hi)
        arr[p], arr[hi] = arr[hi], arr[p]
        store = lo
        for i in range(lo, hi):
            if arr[i] < arr[hi]:
                arr[store], arr[i] = arr[i], arr[store]
                store += 1
        arr[store], arr[hi] = arr[hi], arr[store]
        if store == target:
            return arr[store]
        if store < target:
            lo = store + 1
        else:
            hi = store - 1
""")
prog("kth", "repeated_min", """
def solve(a, k):
    b = list(a)
    for _ in range(k - 1):
        b.remove(min(b))
    return min(b)
""")
prog("kth", "repeated_min", """
def solve(nums, k):
    rest = list(nums)
    val = None
    for _ in range(k):
        mi = 0
        for i in range(1, len(rest)):
            if rest[i] < rest[mi]:
                mi = i
        val = rest.pop(mi)
    return val
""")

# =========================================================== 13. inversions
task("inversions", lambda n, r: ([r.randint(0, 3 * n) for _ in range(n)],), [8, 16, 32, 64, 128, 256, 512, 1024])
prog("inversions", "brute", """
def solve(a):
    c = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i] > a[j]:
                c += 1
    return c
""")
prog("inversions", "brute", """
def solve(nums):
    return sum(1 for i, x in enumerate(nums) for y in nums[i + 1:] if x > y)
""")
prog("inversions", "merge_count", """
def solve(a):
    def sort_count(xs):
        if len(xs) <= 1:
            return xs, 0
        m = len(xs) // 2
        l, cl = sort_count(xs[:m])
        r, cr = sort_count(xs[m:])
        out, i, j, c = [], 0, 0, cl + cr
        while i < len(l) and j < len(r):
            if l[i] <= r[j]:
                out.append(l[i]); i += 1
            else:
                out.append(r[j]); j += 1
                c += len(l) - i
        out += l[i:] + r[j:]
        return out, c
    return sort_count(list(a))[1]
""")
prog("inversions", "merge_count", """
def solve(nums):
    arr = list(nums)
    tmp = [0] * len(arr)
    def rec(lo, hi):
        if hi - lo < 2:
            return 0
        mid = (lo + hi) // 2
        inv = rec(lo, mid) + rec(mid, hi)
        i, j, k = lo, mid, lo
        while i < mid or j < hi:
            if j >= hi or (i < mid and arr[i] <= arr[j]):
                tmp[k] = arr[i]; i += 1
            else:
                tmp[k] = arr[j]; j += 1
                inv += mid - i
            k += 1
        arr[lo:hi] = tmp[lo:hi]
        return inv
    return rec(0, len(arr))
""")
prog("inversions", "fenwick", """
def solve(a):
    vals = sorted(set(a))
    rank = {v: i + 1 for i, v in enumerate(vals)}
    n = len(vals)
    tree = [0] * (n + 1)
    inv = 0
    for seen, x in enumerate(a):
        r = rank[x]
        i, s = r, 0
        while i > 0:
            s += tree[i]
            i -= i & -i
        inv += seen - s
        i = r
        while i <= n:
            tree[i] += 1
            i += i & -i
    return inv
""")
prog("inversions", "fenwick", """
class BIT:
    def __init__(self, n):
        self.n = n
        self.t = [0] * (n + 1)
    def add(self, i):
        while i <= self.n:
            self.t[i] += 1
            i += i & (-i)
    def query(self, i):
        s = 0
        while i:
            s += self.t[i]
            i -= i & (-i)
        return s

def solve(nums):
    order = {v: k for k, v in enumerate(sorted(set(nums)), 1)}
    bit = BIT(len(order))
    total = 0
    for x in reversed(nums):
        total += bit.query(order[x] - 1)
        bit.add(order[x])
    return total
""")

# =========================================================== 14. LIS length
task("lis", lambda n, r: ([r.randint(0, 4 * n) for _ in range(n)],), [8, 16, 32, 64, 128, 256, 512, 1024])
prog("lis", "dp_quadratic", """
def solve(a):
    if not a:
        return 0
    dp = [1] * len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
""")
prog("lis", "dp_quadratic", """
def solve(nums):
    best = []
    for i, x in enumerate(nums):
        best.append(1 + max([best[j] for j in range(i) if nums[j] < x], default=0))
    return max(best, default=0)
""")
prog("lis", "patience", """
from bisect import bisect_left
def solve(a):
    tails = []
    for x in a:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
""")
prog("lis", "patience", """
def solve(nums):
    piles = []
    for x in nums:
        lo, hi = 0, len(piles)
        while lo < hi:
            mid = (lo + hi) // 2
            if piles[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(piles):
            piles.append(x)
        else:
            piles[lo] = x
    return len(piles)
""")


# =========================================================== 15. connected components
def _gen_graph(n, r):
    edges = [[r.randrange(n), r.randrange(n)] for _ in range(n * 3 // 4)]
    return (n, edges)


task("components", _gen_graph, [8, 16, 32, 64, 128, 256, 512, 1024, 2048])
prog("components", "bfs", """
from collections import deque
def solve(n, edges):
    g = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v); g[v].append(u)
    seen = [False] * n
    comps = 0
    for s in range(n):
        if seen[s]:
            continue
        comps += 1
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for w in g[u]:
                if not seen[w]:
                    seen[w] = True
                    q.append(w)
    return comps
""")
prog("components", "bfs", """
def solve(n, edges):
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    visited = set()
    count = 0
    for start in range(n):
        if start in visited:
            continue
        count += 1
        frontier = [start]
        visited.add(start)
        while frontier:
            nxt = []
            for u in frontier:
                for v in adj[u]:
                    if v not in visited:
                        visited.add(v)
                        nxt.append(v)
            frontier = nxt
    return count
""")
prog("components", "dfs", """
def solve(n, edges):
    g = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v); g[v].append(u)
    seen = [False] * n
    def dfs(u):
        seen[u] = True
        for w in g[u]:
            if not seen[w]:
                dfs(w)
    c = 0
    for s in range(n):
        if not seen[s]:
            c += 1
            dfs(s)
    return c
""")
prog("components", "dfs", """
def solve(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    mark = [0] * n
    comps = 0
    for s in range(n):
        if mark[s]:
            continue
        comps += 1
        stack = [s]
        while stack:
            u = stack.pop()
            if mark[u]:
                continue
            mark[u] = 1
            stack.extend(v for v in adj[u] if not mark[v])
    return comps
""")
prog("components", "union_find", """
def solve(n, edges):
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    comps = n
    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
            comps -= 1
    return comps
""")
prog("components", "union_find", """
def solve(n, edges):
    par = list(range(n))
    size = [1] * n
    def root(x):
        if par[x] != x:
            par[x] = root(par[x])
        return par[x]
    for a, b in edges:
        a, b = root(a), root(b)
        if a == b:
            continue
        if size[a] < size[b]:
            a, b = b, a
        par[b] = a
        size[a] += size[b]
    return sum(1 for i in range(n) if root(i) == i)
""")


# =========================================================== 16. majority element
def _gen_major(n, r):
    m = r.randint(0, n)
    a = [m] * (n // 2 + 1) + [r.randint(0, n) for _ in range(n - n // 2 - 1)]
    r.shuffle(a)
    return (a,)


task("majority", _gen_major, [8, 16, 32, 64, 128, 256, 512, 1024, 2048])
prog("majority", "count", """
def solve(a):
    cnt = {}
    for x in a:
        cnt[x] = cnt.get(x, 0) + 1
        if cnt[x] > len(a) // 2:
            return x
""")
prog("majority", "count", """
from collections import Counter
def solve(nums):
    return Counter(nums).most_common(1)[0][0]
""")
prog("majority", "sort_middle", """
def solve(a):
    return sorted(a)[len(a) // 2]
""")
prog("majority", "sort_middle", """
def solve(nums):
    b = nums[:]
    b.sort()
    mid = len(b) // 2
    return b[mid]
""")
prog("majority", "boyer_moore", """
def solve(a):
    cand, c = None, 0
    for x in a:
        if c == 0:
            cand = x
        c += 1 if x == cand else -1
    return cand
""")
prog("majority", "boyer_moore", """
def solve(nums):
    count = 0
    candidate = nums[0]
    i = 0
    while i < len(nums):
        if count == 0:
            candidate = nums[i]
            count = 1
        elif nums[i] == candidate:
            count += 1
        else:
            count -= 1
        i += 1
    return candidate
""")
prog("majority", "brute", """
def solve(a):
    for x in a:
        if a.count(x) > len(a) // 2:
            return x
""")
prog("majority", "brute", """
def solve(nums):
    n = len(nums)
    for i in range(n):
        c = 0
        for j in range(n):
            if nums[j] == nums[i]:
                c += 1
        if 2 * c > n:
            return nums[i]
""")

# =========================================================== 17. sum 1..n
task("sum_to_n", lambda n, r: (n,), [16, 64, 256, 1024, 4096, 16384, 65536], test_sizes=(0, 1, 10))
prog("sum_to_n", "loop", """
def solve(n):
    s = 0
    for i in range(1, n + 1):
        s += i
    return s
""")
prog("sum_to_n", "loop", """
def solve(n):
    total, k = 0, n
    while k > 0:
        total += k
        k -= 1
    return total
""")
prog("sum_to_n", "formula", """
def solve(n):
    return n * (n + 1) // 2
""")
prog("sum_to_n", "formula", """
def solve(n):
    pairs = n // 2
    s = pairs * (n + 1)
    if n % 2:
        s += (n + 1) // 2
    return s
""")


# =========================================================== 18. balanced parentheses
def _gen_parens(n, r):
    s = "(" * (n // 2) + ")" * (n // 2)
    if r.random() < 0.5:
        s = s[:-1] + "("
    return (s,)


task("parens", _gen_parens, [8, 16, 32, 64, 128, 256, 512, 1024, 2048], test_sizes=(2, 4, 6))
prog("parens", "counter", """
def solve(s):
    d = 0
    for c in s:
        d += 1 if c == '(' else -1
        if d < 0:
            return False
    return d == 0
""")
prog("parens", "counter", """
def solve(text):
    bal = 0
    i = 0
    while i < len(text):
        if text[i] == '(':
            bal += 1
        else:
            bal -= 1
            if bal < 0:
                break
        i += 1
    return bal == 0
""")
prog("parens", "stack", """
def solve(s):
    st = []
    for c in s:
        if c == '(':
            st.append(c)
        elif not st:
            return False
        else:
            st.pop()
    return not st
""")
prog("parens", "stack", """
from collections import deque
def solve(text):
    stack = deque()
    for ch in text:
        if ch == ')':
            if not stack:
                return False
            stack.pop()
        else:
            stack.append(ch)
    return len(stack) == 0
""")
prog("parens", "replace", """
def solve(s):
    while '()' in s:
        s = s.replace('()', '')
    return s == ''
""")
prog("parens", "replace", """
def solve(text):
    prev = None
    while prev != text:
        prev = text
        k = text.find('()')
        if k >= 0:
            text = text[:k] + text[k + 2:]
    return len(text) == 0
""")

# =========================================================== 19. integer sqrt
task("isqrt", lambda n, r: (n * n + r.randint(0, n),), [16, 64, 256, 1024, 4096, 16384], test_sizes=(0, 1, 5))
prog("isqrt", "linear", """
def solve(n):
    r = 0
    while (r + 1) * (r + 1) <= n:
        r += 1
    return r
""")
prog("isqrt", "linear", """
def solve(x):
    for k in range(x + 2):
        if k * k > x:
            return k - 1
""")
prog("isqrt", "binary", """
def solve(n):
    lo, hi = 0, n + 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid
    return lo
""")
prog("isqrt", "binary", """
def solve(x):
    def go(lo, hi):
        if lo > hi:
            return hi
        m = (lo + hi) // 2
        if m * m == x:
            return m
        return go(m + 1, hi) if m * m < x else go(lo, m - 1)
    return go(0, x)
""")
prog("isqrt", "newton", """
def solve(n):
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x
""")
prog("isqrt", "newton", """
def solve(x):
    if x == 0:
        return 0
    g = x
    while True:
        ng = (g + x // g) >> 1
        if ng >= g:
            return g
        g = ng
""")

# =========================================================== 20. min coins
task("coins", lambda n, r: ([1, 3, 4, 7], n), [8, 16, 32, 64, 128, 256, 512, 1024], test_sizes=(0, 6, 11))
prog("coins", "dp", """
def solve(coins, amount):
    INF = float('inf')
    dp = [0] + [INF] * amount
    for v in range(1, amount + 1):
        for c in coins:
            if c <= v and dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    return dp[amount] if dp[amount] != INF else -1
""")
prog("coins", "dp", """
def solve(coins, amount):
    memo = {}
    def best(rem):
        if rem == 0:
            return 0
        if rem in memo:
            return memo[rem]
        res = min((best(rem - c) + 1 for c in coins if c <= rem), default=float('inf'))
        memo[rem] = res
        return res
    ans = best(amount)
    return -1 if ans == float('inf') else ans
""")
prog("coins", "bfs", """
from collections import deque
def solve(coins, amount):
    if amount == 0:
        return 0
    dist = {0: 0}
    q = deque([0])
    while q:
        v = q.popleft()
        for c in coins:
            w = v + c
            if w == amount:
                return dist[v] + 1
            if w < amount and w not in dist:
                dist[w] = dist[v] + 1
                q.append(w)
    return -1
""")
prog("coins", "bfs", """
def solve(coins, amount):
    level, frontier, seen = 0, [amount], {amount}
    while frontier:
        if 0 in frontier:
            return level
        nxt = []
        for rem in frontier:
            for c in coins:
                r = rem - c
                if r >= 0 and r not in seen:
                    seen.add(r)
                    nxt.append(r)
        frontier = nxt
        level += 1
    return -1
""")


# =========================================================== 21. substring search
def _gen_substr(n, r):
    m = max(2, n // 4)
    return ("a" * n + "b", "a" * (m - 1) + "b")


task("substring", _gen_substr, [8, 16, 32, 64, 128, 256, 512, 1024, 2048], test_sizes=(2, 4, 8))
prog("substring", "naive", """
def solve(text, pat):
    n, m = len(text), len(pat)
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pat[j]:
            j += 1
        if j == m:
            return i
    return -1
""")
prog("substring", "naive", """
def solve(s, p):
    for start in range(len(s) - len(p) + 1):
        if all(s[start + k] == p[k] for k in range(len(p))):
            return start
    return -1
""")
prog("substring", "kmp", """
def solve(text, pat):
    m = len(pat)
    fail = [0] * m
    k = 0
    for i in range(1, m):
        while k and pat[i] != pat[k]:
            k = fail[k - 1]
        if pat[i] == pat[k]:
            k += 1
        fail[i] = k
    k = 0
    for i, c in enumerate(text):
        while k and c != pat[k]:
            k = fail[k - 1]
        if c == pat[k]:
            k += 1
        if k == m:
            return i - m + 1
    return -1
""")
prog("substring", "kmp", """
def prefix_function(s):
    pi = [0] * len(s)
    for i in range(1, len(s)):
        j = pi[i - 1]
        while j > 0 and s[i] != s[j]:
            j = pi[j - 1]
        if s[i] == s[j]:
            j += 1
        pi[i] = j
    return pi

def solve(s, p):
    combo = p + '#' + s
    pi = prefix_function(combo)
    for i in range(len(p) + 1, len(combo)):
        if pi[i] == len(p):
            return i - 2 * len(p)
    return -1
""")
prog("substring", "rabin_karp", """
def solve(text, pat):
    B, M = 256, 1000000007
    n, m = len(text), len(pat)
    if m > n:
        return -1
    hp = ht = 0
    for i in range(m):
        hp = (hp * B + ord(pat[i])) % M
        ht = (ht * B + ord(text[i])) % M
    pw = pow(B, m - 1, M)
    for i in range(n - m + 1):
        if hp == ht and text[i:i + m] == pat:
            return i
        if i + m < n:
            ht = ((ht - ord(text[i]) * pw) * B + ord(text[i + m])) % M
    return -1
""")
prog("substring", "rabin_karp", """
def solve(s, p):
    base, mod = 131, (1 << 61) - 1
    def h(x):
        v = 0
        for ch in x:
            v = (v * base + ord(ch)) % mod
        return v
    m = len(p)
    if m > len(s):
        return -1
    target, cur = h(p), h(s[:m])
    top = pow(base, m, mod)
    i = 0
    while True:
        if cur == target and s[i:i + m] == p:
            return i
        if i + m >= len(s):
            return -1
        cur = (cur * base + ord(s[i + m]) - ord(s[i]) * top) % mod
        i += 1
""")


# =========================================================== API
def build(seed=0):
    """Returns (tasks, programs). Each task is in the common task format used by the sandbox."""
    tasks, progs = [], []
    for name, spec in TASKS.items():
        r = random.Random(seed)
        ladder = []
        for n in spec["sizes"]:
            rr = random.Random(seed * 7919 + n)
            ladder.append({"ladder": "main", "size": n, "arg": repr(spec["gen"](n, rr))})
        tests_args = [spec["gen"](n, random.Random(seed + 17 * i + n)) for i, n in enumerate(spec["test_sizes"])]
        tasks.append({"id": f"curated/{name}", "source": "curated", "kind": "func", "entry": "solve",
                      "setup": "", "ladder": ladder, "test_args": [repr(a) for a in tests_args]})
        for i, (algo, code) in enumerate(P[name]):
            progs.append({"pid": f"curated/{name}/{i}", "task": f"curated/{name}", "algo": algo, "code": code})
        del r
    return tasks, progs


def pairs(progs):
    out = []
    by = {}
    for p in progs:
        by.setdefault(p["task"], []).append(p)
    for t, ps in by.items():
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                out.append({"a": ps[i]["pid"], "b": ps[j]["pid"], "task": t,
                            "same": int(ps[i]["algo"] == ps[j]["algo"]), "dataset": "ours"})
    return out
