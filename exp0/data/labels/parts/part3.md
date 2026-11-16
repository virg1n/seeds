## PAIR 150  (task apps/4293)

### A
```python
import sys

def solve():
    # Read P, Q, R from standard input
    tokens = sys.stdin.read().split()
    if not tokens:
        return
    P, Q, R = int(tokens[0]), int(tokens[1]), int(tokens[2])

    # The three possible round trips are:
    # 1. A -> B -> C  : P + Q
    # 2. A -> C -> A  : R + R = 2*R  (start at A, go A->C, C->A)
    # 3. B -> C -> B  : Q + Q = 2*Q  (start at B, go B->C, C->B)
    # 4. C -> A -> C  : R + R = 2*R  (start at C, go C->A, A->C)

    # Among the minimums, choose the smallest total time.
    time1 = P + Q
    time2 = 2 * R
    time3 = 2 * Q

    # Also consider the case where the cycle repeats and we take the shortest edge twice in a cycle
    time4 = 2 * min(P, Q, R) * 1  # Wait, that logic is wrong.
    
    # Actually, we can also consider:
    # Start at A, go to A via C: 2*R
    # Start at B, go to B via A: 2*P
    # Start at C, go to C via B: 2*Q
    # These are already covered.

    # But note: the problem says "start at one of the airports, fly to another airport and then fly to the other airport".
    # This implies a path of length exactly 2 edges in a 3-node graph.
    # The possible 2-edge paths in a complete graph K3 (3 nodes) are:
    # - Path A->B->C, total = P+Q
    # - Path B->A->C, total = P+R  (Wait, the example says B->A->C is 1+4=5, so P=1, R=4 -> P+R=5)
    # - Path C->B->A, total = Q+P  (Same as above)
    # - Path B->C->A, total = Q+R
    # - Path A->C->B, total = R+Q
    # - Path C->A->B, total = R+P

    # Let's recompute the 2-edge paths explicitly using the variable names:
    # A->B->C: P+Q
    # A->C->B: R+Q
    # B->A->C: P+R
    # B->C->A: Q+R
    # C->A->B: R+P
    # C->B->A: Q+P

    # The problem asks for the minimum sum.
    # In the sample: P=1, Q=3, R=4
    # P+Q = 4
    # R+Q = 7
    # P+R = 5
    # Q+R = 7
    # R+P = 5
    # Q+P = 4
    # Minimum is 4.

    # So we need min(P+Q, Q+R, P+R, P+Q, Q+R, R+P)
    # Actually, the set of unique sums is {P+Q, Q+R, R+P}.
    # Because:
    # A->B->C = P+Q
    # B->C->A = Q+R
    # C->A->B = R+P
    # A->C->B = R+Q = same as Q+R
    # C->B->A = Q+P = same as P+Q
    # B->A->C = P+R = same as P+R

    # So we just need min(P + Q, Q + R, P + R)

    min_total = min(P + Q, Q + R, P + R)

    print(min_total)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    P = int(input_data[0])
    Q = int(input_data[1])
    R = int(input_data[2])
    
    # The three possible routes with different sums:
    # Start at A: A -> B -> C gives P + Q
    #          A -> C -> A gives R + R (cycle)
    # Start at B: B -> C -> A gives Q + R
    #          B -> A -> B gives P + P (cycle)
    # Start at C: C -> A -> B gives R + P
    #          C -> B -> C gives R + R (cycle)
    
    # Since the cycle routes always add R or P (or both) extra,
    # the minimum will always be one of the simple paths without cycling back.
    # Specifically, the minimal simple path is the minimum of:
    # P + Q, Q + R, R + P
    
    candidates = [P + Q, P + R, Q + R]
    print(min(candidates))

if __name__ == "__main__":
    main()
```

## PAIR 151  (task apps/4176)

### A
```python
import sys

def main():
    line = sys.stdin.readline()
    if not line:
        return
    a_str, b_str = line.strip().split()
    a = int(a_str)
    b = int(b_str)

    # LCM(A, B) is the smallest number that is divisible by both A and B.
    lcm = a * b // gcd(a, b)
    print(lcm)

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

if __name__ == "__main__":
    main()
```

### B
```python
import sys

def main():
    line = sys.stdin.read().strip()
    if not line:
        return
    A, B = map(int, line.split())

    # We want the minimum total pieces N such that:
    # N % A == 0 and N % B == 0
    # That is, N is a common multiple of A and B.
    # The minimum such N is the Least Common Multiple (LCM).

    def gcd(x, y):
        while y:
            x, y = y, x % y
        return x

    def lcm(a, b):
        if a == 0 or b == 0:
            return 0
        return abs(a * b) // gcd(a, b)

    print(lcm(A, B))

if __name__ == "__main__":
    main()
```

## PAIR 152  (task apps/4504)

### A
```python
def solve():
    # Read the input string from standard input
    s = input()
    
    # An even string is concatenation of two equal strings.
    # We want to find the longest substring of s ending at some position i
    # such that s[0:i+1] is even, and i+1 < len(s).
    # In other words, delete at least one character from the end.
    
    n = len(s)
    # We iterate over all possible end positions (excluding the full string)
    # The last character of the substring is at index i (0-based), so length = i + 1
    # We want i+1 < n, so i <= n - 2
    # Check for evenness at each possible split point from the end
    
    max_len = 0
    
    # Iterate through possible split points:
    # Split at index k (0-based), meaning left part = s[0:k], right part = s[k:]
    # But we also require right part == left part.
    # Instead, simpler: try all substrings that end at any position i < n-1
    # and check if they are even.
    # Actually, easier: try all substrings s[0:i+1] where i+1 < n, and check if it is even.
    
    for i in range(1, n - 1):  # i = length of substring - 1, so length from 2 to n-2
        sub = s[:i+1]
        # Check if sub is even
        left = sub[:len(sub)//2]
        right = sub[len(sub)//2:]
        
        if left == right:
            max_len = max(max_len, len(sub))
    
    print(max_len)


solve()
```

### B
```python
def solve():
    s = input()
    n = len(s)
    # We need the longest even suffix (deleting from the end) that is also even,
    # and must delete at least one character, so length must be < n.
    # An even string is formed by two equal halves.

    # If n is even, we check suffixes of lengths 2*(n//2) - 1, 2*(n//2) - 2, ...
    # In general, for a given n, we want the largest L < n such that:
    # S[:n] with length L is even, and L = n - k for some k >= 1.
    # Actually, we don't fix the full S; we fix the length L and check if
    # a string of length L can be formed as two equal parts by deleting from the
    # end of S[:n]. But since we are only deleting from the end, the remaining
    # prefix of S has length L, and we want that prefix to be even.
    # So we iterate L from n-1 down to 1, check if prefix S[:L] is even.

    def is_even(s):
        if len(s) % 2 != 0:
            return False
        mid = len(s) // 2
        return s[:mid] == s[mid:]

    # Since the problem guarantees a non-empty answer exists, we can just binary search or iterate.
    # Constraints: n <= 200, so simple iteration is fine.
    for L in range(n - 1, 0, -1):
        if is_even(s[:L]):
            print(L)
            return

solve()
```

## PAIR 153  (task apps/4057)

### A
```python
import sys

def solve():
    n = int(sys.stdin.readline())
    if n == 0:
        print(0)
        return
    
    a = list(map(int, sys.stdin.readline().split()))
    
    # Count the frequency of each coin value
    from collections import Counter
    counts = Counter(a)
    
    # The number of pockets is determined by the maximum frequency of any coin value
    # because each pocket can hold at most one instance of each coin type.
    max_freq = max(counts.values())
    
    print(max_freq)

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    # Read n
    try:
        line1 = input().strip()
        if not line1:
            return  # Handle empty input gracefully
        n = int(line1)
    except (ValueError, IndexError):
        return

    # Read the list of coin values
    try:
        line2 = input().strip()
        a = list(map(int, line2.split()))
    except (ValueError, IndexError):
        return

    # Frequency array for values 1..100
    counts = [0] * 101

    for x in a:
        counts[x] += 1

    # We need the minimum number of pockets such that no two coins with the same value go in the same pocket.
    # For each unique value v, we can put coins of that value into distinct pockets.
    # If value v appears c times, it will occupy c pockets.
    # The total number of pockets needed is the maximum count among all values.
    max_pockets = max(counts) if counts else 0

    print(max_pockets)

solve()
```

## PAIR 154  (task apps/4464)

### A
```python
def solve():
    import sys

    # Read all tokens from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    A = int(input_data[0])
    B = int(input_data[1])
    C = int(input_data[2])

    # Each selected integer is a multiple of A
    # The sum will be a multiple of A.
    # We want: sum % B == C
    # Since sum % A == 0, the necessary condition for existence is:
    # (some multiple of A) % B == C
    # This is equivalent to: C % gcd(A, B) == 0

    import math

    g = math.gcd(A, B)

    if C % g == 0:
        print("YES")
    else:
        print("NO")


if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    import sys
    input = sys.stdin.read
    data = input().strip().split()
    if not data:
        return
    A, B, C = map(int, data)

    # Since we can pick any number of multiples of A,
    # the possible sums we can form are all positive integers that are multiples of gcd(A, B).
    # Actually, more precisely: the set of achievable sums is the set of all integers >= 0
    # that are congruent to 0 modulo gcd(A, B)? Let's check.
    #
    # Wait, the problem says:
    # - each selected integer is a multiple of A
    # - we can pick any non-empty set of such integers
    # - we want sum % B == C
    #
    # Let the selected integers be a1*A, a2*A, ..., ka*A where a_i >= 1.
    # Then sum = A * (a1 + a2 + ... + ka).
    # Let S = a1 + a2 + ... + ka. Since each a_i >= 1, we must have S >= k >= 1.
    # Also, we can choose k arbitrarily and any a_i >= 1, so S can be any integer >= 1?
    # Actually, the sum S = a1 + ... + ak is just the sum of k positive integers, so S >= k.
    # But we can choose k = 1 and S = A.
    # Can we achieve any S >= 1? Yes, because we can take k=1, a1=S.
    # So the set of possible values of the sum of coefficients is all integers S >= 1.
    #
    # Therefore, the total sum = A * S, where S is any integer >= 1.
    # So we can form any sum of the form A * S with S >= 1.
    # We need A * S ≡ C (mod B).
    # This is equivalent to: does there exist an integer S >= 1 such that (A * S) mod B == C?
    #
    # Let’s consider the set of values R = {A mod B * S mod B | S in positive integers}.
    # As S varies over positive integers, A * S mod B cycles with period B / gcd(A, B).
    # Specifically, the reachable residues modulo B are multiples of g = gcd(A, B).
    # That is, A * S ≡ 0 (mod g) for all S.
    # So the set of residues {A * S mod B} is exactly {0, g, 2g, ..., B - g} ∪ {0} ? 
    # Actually, the set is all multiples of g modulo B.
    # More precisely, the values A * S mod B take all values in {k * g | 0 <= k < B/g}.
    #
    # So we can achieve residue C modulo B if and only if C is a multiple of gcd(A, B).
    # But wait, there's a constraint: S must be at least 1.
    # Does this restriction affect whether we can reach C?
    # If C = 0, can we achieve 0? Yes, by picking S such that A*S ≡ 0 (mod B).
    # For example, pick S = B / gcd(A, B). Then A*S is divisible by B, so A*S ≡ 0 (mod B).
    # This S is positive since A, B >= 1.
    #
    # If C != 0, can we always find S >= 1?
    # Yes, because the set of values A*S mod B for S >= 1 is exactly the same as for S >= 0,
    # except possibly for small values of S?
    # Actually, since the sequence repeats every B/gcd(A,B) >= 1 steps, and includes all multiples of gcd(A,B),
    # it definitely includes C if C is a multiple of gcd(A,B).
    #
    # So the condition is simply: C % gcd(A, B) == 0.
    #
    # Let's double-check with the sample:
    # A=7, B=5, C=1
    # gcd(7,5) = 1. C=1 is divisible by 1 -> YES. Correct.
    #
    # Another test: A=3, B=5, C=2
    # gcd(3,5)=1, C=2 -> YES? 
    # We need 3*S ≡ 2 (mod 5). Multiply by 2: S≡4 (mod 5). S=4 -> 3*4=12≡2. YES.
    # A=3, B=5, C=1 -> 3*S≡1 (mod 5) -> S≡2 (mod 5) -> S=2 -> 3*2=6≡1. YES.
    # A=3, B=5, C=3 -> 3*S≡3 (mod 5) -> S≡1 (mod 5) -> S=1 -> 3*1=3. YES.
    # A=3, B=5, C=4 -> 3*S≡4 (mod 5) -> S≡3 (mod 5) -> S=3 -> 9≡4. YES.
    # So yes, seems correct.
    #
    # Therefore, check if C % gcd(A,B) == 0.
    import math

    d = math.gcd(A, B)
    if C % d == 0:
        print("YES")
    else:
        print("NO")

if __name__ == "__main__":
    solve()
```

## PAIR 155  (task apps/4142)

### A
```python
S = input().strip()

for i, char in enumerate(S, start=1):
    # 1-indexed positions: odd = 1, 3, 5, ...
    # even = 2, 4, 6, ...
    if i % 2 == 0:
        if char not in 'LUD':
            print("No")
            exit()
    else:
        if char not in 'RUD':
            print("No")
            exit()

print("Yes")
```

### B
```python
S = input()

# Check every character
# Odd positions (1-indexed) -> index 0, 2, 4, ... -> should be R, U, D
# Even positions (1-indexed) -> index 1, 3, 5, ... -> should be L, U, D

for i, char in enumerate(S):
    if i % 2 == 0:  # odd position (1st, 3rd, 5th...)
        if char not in ("R", "U", "D"):
            print("No")
            exit()
    else:  # even position (2nd, 4th, 6th...)
        if char not in ("L", "U", "D"):
            print("No")
            exit()

print("Yes")
```

## PAIR 156  (task apps/4339)

### A
```python
def solve():
    # Read n
    n = int(input())
    
    # Read array a
    a = list(map(int, input().split()))
    
    # Read array b
    b = list(map(int, input().split()))
    
    # Count good pairs
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if a[i] + a[j] > b[i] + b[j]:
                count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        n = int(next(iterator))
        a = []
        for _ in range(n):
            a.append(int(next(iterator)))
        b = []
        for _ in range(n):
            b.append(int(next(iterator)))
    except StopIteration:
        return

    # We want to count pairs (i, j) with i < j such that a[i] + a[j] > b[i] + b[j].
    # This is equivalent to: a[i] - b[i] + a[j] - b[j] > 0.
    # Let c[i] = a[i] - b[i].
    # We need pairs (i, j) with i < j such that c[i] + c[j] > 0.
    
    c = [a[i] - b[i] for i in range(n)]
    
    # Count pairs (i, j) with i < j and c[i] + c[j] > 0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            if c[i] + c[j] > 0:
                count += 1
    print(count)

if __name__ == "__main__":
    solve()
```

## PAIR 157  (task mbpp/390)

### A
```python
def add_string(data, format_str):
    return [format_str.format(data[i]) for i in range(len(data))]
```

### B
```python
def add_string(data, format_str):
    result = []
    for i, value in enumerate(data):
        result.append(format_str.format(value, i))
    return result
```

## PAIR 158  (task apps/4261)

### A
```python
def solve():
    # Read A, B, C from standard input
    A, B, C = map(int, input().split())

    # Transfer water from Bottle 2 to Bottle 1 as much as possible
    # Max amount to transfer is min(C, A - B)
    transfer = min(C, A - B)
    remaining = C - transfer

    # Print the remaining amount in Bottle 2
    print(remaining)

if __name__ == "__main__":
    solve()
```

### B
```python
a, b, c = map(int, input().split())
# Transfer min(C, A-B) from Bottle 2 to Bottle 1
remain = c - min(c, a - b)
print(remain)
```

## PAIR 159  (task apps/4347)

### A
```python
def solve():
    import sys
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    n = int(input_data)
    
    # Total permutations of 2n people is (2n)!
    # Divide by 2! for ordering of the two round dances
    # For each chosen subset of n people, the number of round dances is (n-1)!
    # But wait, let's re-derive using the example.
    # n=2: (2*1)! = 2! = 2. Divide by 2! for two dances -> 1. Correct.
    # n=4: (4*1)! = 24. Divide by 2! -> 12. 
    # But example says 3. So the formula is not simple factorial division.
    # Let's use the explicit formula derived from examples.
    
    # For n people split into two groups of n/2 people each, and each group forms a round dance.
    # Step 1: Choose n/2 people for the first dance from n people: C(n, n/2) ways.
    # Step 2: The remaining n/2 people form the second dance: 1 way.
    # Step 3: Permute the first group in a circle: (n/2 - 1)! ways.
    # Step 4: Permute the second group in a circle: (n/2 - 1)! ways.
    
    # However, note that swapping the two round dances might be considered the same?
    # Example n=4: 3 ways.
    # My formula: C(4,2) * (1!) * (1!) * (1!) * (1!) = 6 * 1 * 1 * 1 * 1 = 6.
    # Why 3? Because the order of the two dances matters? No, "indistinguishable".
    # Actually, in example n=4, the options listed are pairs like { {1,2}, {3,4} }, { {2,4}, {3,1} }, { {4,1}, {3,2} }.
    # These are sets of two pairs. The order of the pairs doesn't matter.
    # So we divide by 2!.
    # 6 / 2 = 3. Correct.
    # Example n=2: C(2,1) * 1! * 1! / 2! = 2 / 2 = 1. Correct.
    
    # Example n=8:
    # C(8,4) * (4-1)! * (4-1)! / 2!
    # C(8,4) = 70
    # (3)! = 6
    # 70 * 6 * 6 / 2 = 70 * 18 = 1260. Correct.
    
    # Example n=20:
    # C(20,10) * (9)! * (9)! / 2!
    # C(20,10) = 184756
    # 9! = 362880
    # 184756 * 362880 * 362880 / 2
    # = 184756 * 66688320 * 0.5 ?
    # Let's compute properly:
    # C(20,10) = 184756
    # (9)! = 362880
    # Product = 184756 * 362880^2
    # Then divide by 2.
    # 184756 * 131710174096 / 2 = 184756 * 65855087048 = 12164510040883200.
    # Matches example.
    
    import math
    
    n_half = n // 2
    c_n_n_half = math.comb(n, n_half)
    factor1 = math.factorial(n_half - 1)
    factor2 = math.factorial(n_half - 1)
    
    result = c_n_n_half * factor1 * factor2
    result = result // 2
    
    print(result)

solve()
```

### B
```python
import sys

def solve():
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        n = int(input_data)
    except ValueError:
        return

    if n % 2 != 0 or n < 2:
        # Per problem statement, n is even and >= 2.
        # But handle gracefully.
        print(0)
        return

    # Number of people
    n_people = n

    # Each round dance has n_people // 2 people.
    m = n_people // 2

    # Number of ways to partition n_people into two sets of size m (order of sets doesn't matter yet).
    # This is the multinomial coefficient: n! / (m! * m!)
    # Then divide by 2 because the two sets are indistinguishable in the sense that choosing set A
    # as dance 1 and set B as dance 2 is the same as vice versa, EXCEPT we need to consider
    # whether the sets themselves can be swapped.
    # Actually, let's think carefully:
    # Step 1: Choose a set of size m from n_people: C(n, m)
    # Step 2: The remaining n-m people form the other set.
    # Step 3: Arrange the first set into a round dance: (m-1)! ways (since circle permutations).
    # Step 4: Arrange the second set into a round dance: (m-1)! ways.
    # Total arrangements for a fixed partition of sets: (m-1)! * (m-1)!
    # Since the two sets are indistinguishable in terms of which one gets labeled "dance 1" and "dance 2",
    # and we have already counted the partition C(n, m), we must account for symmetry.
    #
    # Alternatively:
    # Total ways = (n! / (m! * m!)) * ((m-1)! * (m-1)!)
    #               = n! / ((m!)^2) * ((m-1)!)^2
    #               = n! / m^2 * 1/m! * (m-1)!^2
    #               = n! / (m^2 * m * (m-1)^2) * (m-1)^2 ... simpler:
    # Let's simplify:
    # C(n, m) = n! / (m! * (n-m)!)
    # For a specific unordered pair of sets {S1, S2}, we assign them to Dance1 and Dance2.
    # However, the problem says "two round dances". The order of dancing doesn't matter for the final
    # configuration count because the sets are just grouped.
    # Actually, the standard interpretation for "n people make two round dances" where the two dances
    # are indistinguishable (just two such circles) is:
    # Choose the first set: nC m
    # Arrange that set: (m-1)!
    # Arrange the second set: (m-1)!
    # But since the two dances are indistinguishable, we divide by 2! to swap them.
    # Total = C(n, m) * (m-1)! * (m-1)! / 2
    #
    # Compute C(n, m) * (m-1)! * (m-1)! // 2
    #
    # Let's compute:
    # C(n, m) = n! / (m! * (n-m)!) where n-m = m. So n! / (m! * m!)
    # Term = (n! / (m! * m!)) * ((m-1)! * (m-1)!) / 2
    #      = n! / (m * m * (m-1) * (m-1))
    #
    # Let's verify with n=4, m=2:
    # n! = 24
    # m! = 2, m! = 2
    # Term = 24 / (2*2) * (1*1) / 2 = 6 * 1 / 2 = 3. Correct.
    #
    # n=2, m=1:
    # n! = 2
    # m! = 1, m! = 1
    # Term = 2 / (1*1) * 0! * 0! / 2 = 2 * 1 / 2 = 1. Correct.

    from math import factorial
    import math

    n_fact = factorial(n)
    m_fact = factorial(m)

    # We need C(n, m) * (m-1)! * (m-1)! / 2
    # C(n, m) = n! / (m! * m!)
    # So total = (n! / (m! * m!)) * ((m-1)! * (m-1)!) * 2? No wait, we divide by 2.
    # Total = (n! / (m! * m!)) * ((m-1)! * (m-1)!) / 2

    # Calculate factorial of m-1
    if m - 1 < 0:
        # m >= 2 because n >= 2 and even, so m = n/2 >= 1.
        # If n=2, m=1, m-1=0, 0! = 1.
        m_minus_1_fact = 1
    else:
        m_minus_1_fact = factorial(m - 1)

    ans = (n_fact // (m_fact * m_fact)) * (m_minus_1_fact * m_minus_1_fact) // 2
    print(ans)

if __name__ == "__main__":
    solve()
```

## PAIR 160  (task apps/4361)

### A
```python
import sys
from typing import List

def solve() -> None:
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        N = int(next(iterator))
        K = int(next(iterator))
    except StopIteration:
        return

    h = []
    for _ in range(N):
        try:
            h.append(int(next(iterator)))
        except StopIteration:
            break

    # Sort the heights
    h.sort()

    # If K trees are chosen, the best possible h_max - h_min is determined by
    # considering adjacent sorted elements in h. Since we want to minimize the span,
    # the optimal strategy is to pick K consecutive elements.
    # The span for a range [i, i+K-1] is h[i+K-1] - h[i].
    # We need to iterate through all such ranges and find the minimum span.
    # Since the array is sorted, a monotonic queue or simple iteration works.
    # However, for N up to 10^5, O(N*K) is too slow (worst-case 10^10).
    # We need O(N) solution: sliding window minimum/maximum logic.

    # Approach: Use a deque to maintain the window of K consecutive elements,
    # but actually, since we want h_max - h_min for any subset of K,
    # and the sorted array ensures that any contiguous subset has minimal range
    # when we pick elements in order, we just need the minimum span of
    # any consecutive K elements.

    # Sliding window of size K
    # Current window spans from i to i+K-1
    # We slide i from 0 to N-K

    if K == 0:
        print(0)
        return
    if K == 1:
        print(0)
        return

    # We'll use a deque to maintain the indices of the current window
    # Actually, simpler: since the array is sorted, the span of K consecutive elements
    # is minimized at the beginning of the window. But wait, not necessarily.
    # Example: [1, 5, 6, 10, 11, 12], K=3.
    # Subarrays of length 3: [1,5,6]->5-1=4, [5,6,10]->5, [6,10,11]->5, [10,11,12]->2.
    # Minimum is 2, at the end of the window.
    # So we need to find min(h[j] - h[i]) where j = i + K - 1.

    # Let's compute all spans and find min.
    # Since N <= 10^5, O(N) is required.
    # We can use a deque to find min in O(1) amortized per slide.
    # But here we need both max and min in the window.
    # Since array is sorted:
    # max in window = h[j], min in window = h[i].
    # So span = h[j] - h[i] = h[i+K-1] - h[i].
    # As i increases, h[i] increases, so the span decreases until i = N-K-1?
    # Actually, h[j] increases as j increases, h[i] increases as i increases.
    # The term h[i+K-1] - h[i] is the difference.
    # Let's just compute all and take min.

    min_span = float('inf')
    for i in range(N - K + 1):
        span = h[i + K - 1] - h[i]
        if span < min_span:
            min_span = span

    print(min_span)

if __name__ == '__main__':
    solve()
```

### B
```python
import sys
from functools import lru_cache

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    N = int(input_data[0])
    K = int(input_data[1])
    heights = [int(input_data[i+2]) for i in range(N)]  # Skip first two elements
    
    # Sort heights in non-decreasing order
    heights.sort()
    
    # We want to pick exactly K trees such that h_max - h_min is minimized.
    # The optimal set of K trees will be a contiguous subarray of the sorted heights.
    # Let the chosen subarray be from index i to i+K-1.
    # Then h_max = heights[i+K-1] and h_min = heights[i].
    # We need to find i such that heights[i+K-1] - heights[i] is minimized.
    
    min_diff = float('inf')
    
    # Iterate over all possible starting positions (i) from 0 to N-K
    for i in range(N - K + 1):
        diff = heights[i + K - 1] - heights[i]
        if diff < min_diff:
            min_diff = diff
    
    print(min_diff)

if __name__ == '__main__':
    solve()
```

## PAIR 161  (task apps/4363)

### A
```python
import sys

def solve():
    # Read K and S from standard input
    line = sys.stdin.read().split()
    if not line:
        return
    K = int(line[0])
    S = int(line[1])

    # Constraints check (problem statement ensures validity, but good for robustness)
    if K < 2 or K > 2500 or S > 3 * K or S < 0:
        print(0)
        return

    # Since K <= 2500, O(K^3) is too slow, O(K^2) is acceptable.
    # We will iterate through possible values of X and Y, then compute Z = S - X - Y.
    # We need to check if 0 <= Z <= K.

    count = 0
    for x in range(K + 1):
        for y in range(K + 1):
            z = S - x - y
            # Check if Z is within the valid range [0, K]
            if 0 <= z <= K:
                count += 1

    print(count)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    # Read K and S from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    K = int(input_data[0])
    S = int(input_data[1])
    
    # We need to find the number of triples (X, Y, Z) such that:
    # 0 <= X, Y, Z <= K
    # X + Y + Z = S
    
    # Iterate over all possible values for X (0 to K)
    count = 0
    for X in range(K + 1):
        # Since 0 <= X, Y, Z <= K, the maximum possible sum is 3K,
        # and minimum is 0. Since S is guaranteed to be between 0 and 3K,
        # we just need to check valid Y and Z.
        
        max_y_z = S - X
        min_y_z = 0
        
        if max_y_z < min_y_z:
            break
            
        for Y in range(max(0, min_y_z), K + 1):
            Z = S - X - Y
            if Z >= 0 and Z <= K:
                count += 1
    
    print(count)

if __name__ == "__main__":
    solve()
```

## PAIR 162  (task mbpp/395)

### A
```python
def first_non_repeating_character(s):
    from collections import Counter

    char_count = Counter(s)
    for char in s:
        if char_count[char] == 1:
            return char
    return None
```

### B
```python
def first_non_repeating_character(s):
    """Return the first non-repeated character in the given string."""
    from collections import Counter

    # Count occurrences of each character
    counts = Counter(s)
    
    # Check each character from the start of the string
    for char in s:
        if counts[char] == 1:
            return char

    # If no character is found as unique, return None
    return None
```

## PAIR 163  (task apps/4258)

### A
```python
import sys

def main():
    lines = sys.stdin.read().strip().split('\n')
    A, B, T = map(int, lines[0].split())
    
    t = float(T + 0.5)
    total = 0
    a = A
    
    while a <= t:
        total += B
        a += A
        
    print(total)

if __name__ == "__main__":
    main()
```

### B
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    A = int(input_data[0])
    B = int(input_data[1])
    T = int(input_data[2])

    # We need to count biscuits produced at times A, 2A, 3A, ..., kA such that kA <= T + 0.5.
    # This means kA < T + 0.5 => kA <= floor(T + 0.5) - 1 if we strictly follow < T+0.5
    # Actually, since kA is an integer, the condition is kA <= T + 0.5 <=> kA <= floor(T + 0.5)
    # Since floor(T + 0.5) = T when T is integer (e.g., floor(7.5) = 7),
    # the number of multiples is simply T + 1?
    # Let's check sample: A=3, B=5, T=7. Output = 10.
    # Multiples: 3, 6 (2 biscuits). Next would be 9 which is > 7.5. So only 2 batches. 2 * 5 = 10. Correct.
    # Wait, the problem says: "A seconds, 2A seconds, 3A seconds and each subsequent multiple of A seconds"
    # The times are discrete moments. We count how many moments <= T + 0.5 occur.
    # Since T is integer, T + 0.5 has fractional part 0.5.
    # Any integer kA <= T + 0.5 is equivalent to kA <= T (since kA is integer and T is integer).
    # Wait, kA <= T + 0.5. If kA = T, then T <= T + 0.5 (true).
    # If kA = T + 1, then T+1 <= T + 0.5 => 1 <= 0.5 (false).
    # So only multiples up to T inclusive satisfy kA <= T + 0.5.
    # Number of multiples = floor(T / A) + 1? 
    # Let's verify with sample: T=7, A=3. Multiples <= 7: 3, 6. Count = 2. 
    # floor(7/3) = 2, so 2+1 = 3? No, we only have 2.
    # The multiples are A, 2A, 3A... kA.
    # We need to find the largest integer k such that kA <= T + 0.5.
    # Since kA is integer, kA <= T + 0.5 <=> kA <= floor(T + 0.5).
    # Since T is integer, floor(T + 0.5) = T.
    # So kA <= T => k = floor(T / A).
    # Number of biscuits = B * floor(T / A).

    num_batches = T // A
    result = num_batches * B

    print(result)

if __name__ == "__main__":
    solve()
```

## PAIR 164  (task apps/4277)

### A
```python
import sys

def main():
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    parts = input_data.split()
    N = int(parts[0])
    A = int(parts[1])
    B = int(parts[2])

    train_cost = N * A
    taxi_cost = B

    if train_cost < taxi_cost:
        print(train_cost)
    else:
        print(taxi_cost)

if __name__ == "__main__":
    main()
```

### B
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    n = int(input_data[0])
    a = int(input_data[1])
    b = int(input_data[2])

    train_total = n * a
    taxi_total = b

    print(min(train_total, taxi_total))

if __name__ == "__main__":
    solve()
```

## PAIR 165  (task mbpp/772)

### A
```python
def remove_length(text: str, k: int) -> str:
    words = text.split()
    result = []
    for word in words:
        if len(word) != k:
            result.append(word)
    return ' '.join(result)
```

### B
```python
def remove_length(word, k):
    return ' '.join([w for w in word.split() if len(w) != k])

assert remove_length('The person is most value tet', 3) == 'person is most value'
```

## PAIR 166  (task mbpp/418)

### A
```python
def Find_Max(nums):
    max_len = 0
    max_index = -1

    for i in range(len(nums)):
        if len(nums[i]) > max_len:
            max_len = len(nums[i])
            max_index = i

    return nums[max_index]
```

### B
```python
def Find_Max(lst):
    return max(lst, key=len)
```

## PAIR 167  (task apps/4257)

### A
```python
import sys

def main():
    # Read input from standard input
    line = sys.stdin.read().strip()
    if not line:
        return
    parts = line.split()
    a = int(parts[0])
    b = int(parts[1])

    # Compute and print the product
    print(a * b)

if __name__ == "__main__":
    main()
```

### B
```python
# Read input from standard input
line = input().split()
A = int(line[0])
B = int(line[1])

# Compute A multiplied by B
result = A * B

# Print the result to standard output
print(result)
```

## PAIR 168  (task apps/4144)

### A
```python
def solve():
    import sys
    input = sys.stdin.read
    data = input().split()
    if not data:
        return
    n = int(data[0])
    
    MOD = 1_000_000_007
    
    # Total sequences where not (A_i=0) and not (A_i=9) is: 10
    # We need at least one 0 and at least one 9.
    # This is equivalent to: (Total) - (No 0) - (No 9) + (No 0 and No 9)
    #
    # No 0: Each A_i in {1..9}, so 9 choices -> 9^N
    # No 9: Each A_i in {0..8}, so 10 - 1 = 9 choices? Wait:
    # Actually "No 9" means A_i != 9, so {0..8} -> 9 choices -> 9^N
    # No 0 and No 9: Each A_i in {1..8} -> 8 choices -> 8^N
    #
    # So:
    ans = (10**n - 9**n - 9**n + 8**n) % MOD
    print(ans)

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    import sys
    
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    
    # Total number of sequences with digits 0..9 of length N is 10^N.
    # Conditions:
    # 1. 0 <= A_i <= 9 (always true for digits)
    # 2. At least one 0 exists.
    # 3. At least one 9 exists.
    
    # Total sequences: 10^N
    # Exclude sequences without 0: 9^N (each digit in {1..9})
    # Exclude sequences without 9: 9^N (each digit in {0..8})
    # By inclusion-exclusion:
    # Count = 10^N - 9^N + 9^N - 0 = 10^N - 9^N
    
    # Wait, let's re-verify inclusion-exclusion carefully:
    # Total = 10^N
    # A: no 0 -> digits from {1..9} -> 9^N
    # B: no 9 -> digits from {0..8} -> 9^N
    # Neither A nor B: no 0 and no 9 -> digits from {1..8} -> 8^N
    # Count with at least one 0 AND at least one 9 = Total - |A union B|
    # |A union B| = |A| + |B| - |A intersection B|
    #             = 9^N + 9^N - 8^N
    # So Answer = 10^N - (9^N + 9^N - 8^N)
    #             = 10^N - 2*9^N + 8^N
    
    MOD = 10**9 + 7
    
    # Compute powers using modular exponentiation
    pow10 = pow(10, N, MOD)
    pow9 = pow(9, N, MOD)
    pow8 = pow(8, N, MOD)
    
    ans = (pow10 - 2 * pow9 + pow8) % MOD
    if ans < 0:
        ans += MOD
    
    print(ans)

if __name__ == "__main__":
    solve()
```

## PAIR 169  (task mbpp/588)

### A
```python
def big_diff(numbers):
    """Calculate the difference between the largest and smallest values in a list."""
    return max(numbers) - min(numbers)
```

### B
```python
def big_diff(nums):
    if not nums:
        raise ValueError("Empty list provided")
    if len(nums) == 1:
        return 0
    return max(nums) - min(nums)

# Example test
assert big_diff([1, 2, 3, 4]) == 3
```

## PAIR 170  (task mbpp/238)

### A
```python
def number_of_substrings(s: str) -> int:
    if not s:
        return 0
    return len(s) * (len(s) + 1) // 2
```

### B
```python
def number_of_substrings(s: str) -> int:
    n = len(s)
    count = 0
    for i in range(n):
        for j in range(i + 1, n + 1):
            # s[i:j] excludes the character at j, so it is the substring of length (j - i)
            count += 1
    return count
```

## PAIR 171  (task apps/4369)

### A
```python
import sys

def solve():
    n = int(sys.stdin.readline().strip())
    # Number of sheets = ceil(N / 2)
    # Equivalent to (n + 1) // 2 in integer arithmetic
    print((n + 1) // 2)

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    n = int(input())
    print((n + 1) // 2)

if __name__ == "__main__":
    solve()
```

## PAIR 172  (task mbpp/569)

### A
```python
def sort_sublists(l):
    """
    Sort each sublist in the given list of lists lexicographically.

    The sorting is done element-wise, meaning if one sublist has more elements
    than another, the additional elements are appended in sorted order to match
    the length of the shorter sublist.

    Examples:
        sort_sublists([['c'], ['b', 'a']])  # -> [['b', 'a'], ['c']]
        sort_sublists([['a', 'b', 'c'], ['d']])  # -> [['a', 'b', 'c'], ['d']]
    """
    # Normalize: ensure all sublists have the same number of elements by sorting
    # and padding shorter lists with empty strings to the end
    sorted_by_len = [sort_strs(sublist) for sublist in l]

    # Sort each sublist using the normalized version
    for i in range(len(sorted_by_len)):
        sorted_by_len[i] = sort_strs(sorted_by_len[i])

    return sorted_by_len


def sort_strs(lst):
    """
    Sort a list of strings lexicographically.
    Note: This function does not handle the padding logic itself; it returns
    a new list sorted in place.
    """
    return sorted(lst)
```

### B
```python
def sort_sublists(lst):
    """Sort each sublist of strings in a given list of lists."""
    return [sorted(sublist) for sublist in lst]
```

## PAIR 173  (task mbpp/471)

### A
```python
def find_remainder(numbers, n):
    """
    Calculate the product of the array numbers modulo n.
    
    Parameters:
    numbers (list): List of integers
    n (int): Modulo value
    
    Returns:
    int: The product of numbers modulo n
    """
    result = 1
    for num in numbers:
        result = (result * num) % n
    return result

# Test case
print(find_remainder([100, 10, 5, 25, 35, 14], 11))  # Expected output: 9
```

### B
```python
def find_remainder(nums, n):
    """
    Computes the product of the array elements modulo n.
    
    Args:
        nums (List[int]): The list of integers.
        n (int): The modulus.
    
    Returns:
        int: The product of elements modulo n.
    """
    product = 1
    for num in nums:
        product = (product * num) % n
    return product

# Test case provided in the prompt
assert find_remainder([ 100, 10, 5, 25, 35, 14 ], 11) == 9
```

## PAIR 174  (task apps/4197)

### A
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    n = int(input_data[0])
    a = [int(x) for x in input_data[1:]]

    # A_i is the count of people when student i enters (inclusive of i)
    # So person with number i contributes +1 to A_i, but this value depends on how many
    # people entered before i.
    # Let last[x] be the time (count) when the person with number x entered.
    # last[3] = A[3]
    # last[1] = A[1]
    # ...
    # last[2] = A[2]

    last = [a[i] for i in range(n)]

    # Sort indices based on last values in ascending order
    # Smaller last value means entered earlier
    sorted_indices = sorted(range(n), key=lambda i: last[i])

    result = [str(i + 1) for i in sorted_indices]  # Student numbers are 1-based

    print(" ".join(result))

solve()
```

### B
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    if not data:
        return
    
    N = int(data[0])
    A = []
    for i in range(1, N + 1):
        A.append(int(data[i]))
    
    # A_i is the number of students in the classroom when student i entered
    # So the order of arrival corresponds to increasing A_i
    # Because if student X enters first, at that moment there are 1 other person already there (total 2).
    # If student Y enters later, there are 2 other people already there (total 3).
    # So the sequence of A values must be strictly increasing.
    
    # Let's verify this logic:
    # Suppose the arrival order is p1, p2, ..., pN.
    # At time of p1: student p1 entered, and pN were already in the room (since N is the max).
    # Actually, the problem says: "A_i students in the classroom when student i entered (including student i)".
    # So when student i enters, there are (A_i - 1) other students already in the room, plus student i.
    # These other students are exactly those who entered before i.
    # Therefore, the student who entered first must have had the largest number of people already present (since the room can't grow without people leaving, but here we just track the count).
    # Actually, if someone left and came back, the problem doesn't mention that. It says "all the students entered at different times" and "reconstruct the order".
    # The key constraint given is A_i != A_j for i != j.
    # This strictly implies the arrival order is strictly increasing with respect to A_i.
    # So the student with smallest A enters last? No.
    # Let's trace:
    # Max students present at the moment a student enters = Total students = N (since no one left).
    # Wait, the problem says "A_i students in the classroom when student i entered".
    # So when student i enters, there are exactly A_i students.
    # This means A_i - 1 students were already there when student i entered.
    # These A_i - 1 students must be the ones who entered before student i.
    # Therefore, student i entered AFTER all students who entered before student i?
    # Actually, the set of students currently in the room when student i enters is {p | p entered before i} U {i}.
    # Since no one leaves, the room size is just the count of people who entered before i plus 1.
    # So A_i = count of people who entered before student i + 1.
    # This implies: count_before_student_i = A_i - 1.
    # So the student who enters with A_i = 2 has 1 person before them (max possible since there are N students).
    # The student who enters with A_i = 1 has 0 people before them (entered first).
    # The student who enters with A_i = N has N-1 people before them.
    # So the arrival order corresponds to increasing A_i.
    # Smallest A_i -> earliest to enter? No.
    # If A_i = 1, then 0 people before -> entered 1st.
    # If A_i = 2, then 1 person before -> entered 2nd.
    # So the earliest entered student has the smallest A_i value.
    # Therefore, the order is: students with A_i = 1, then A_i = 2, etc.
    
    # But wait, let's re-read carefully: "A_i students in the classroom when student i entered".
    # Does "when student i entered" include student i? Yes, "including student number i".
    # So count(A_i) = number of people present at that moment.
    # Since people don't leave, the maximum number of people ever in the room is N.
    # But the record A_i tells us the count at the exact moment student i entered.
    # If student i enters, there are A_i students. This means A_i - 1 students entered earlier.
    # So the student with the smallest A_i has the fewest previous students -> entered first.
    # The student with the largest A_i has the most previous students -> entered last.
    # Correct.
    
    # Wait, the sample output says:
    # Input: 3 \n 2 3 1
    # Output: 3 1 2
    # A values: [2, 3, 1]
    # Explanation in problem:
    # 3 entered. At that moment, A_3 = 1 student is in the room (student 3 itself? No, "A_i students in the classroom when student i entered").
    # Let's re-evaluate the sample.
    # If 3 enters first: At that moment, 0 people were already there. Total in room = 1. So A_3 should be 1?
    # But the input says A_3 = 1. Wait, the indices in input are A_1, A_2, A_3.
    # So A_1 = 2, A_2 = 3, A_3 = 1.
    # This means:
    # - When student 1 entered: 2 people in room.
    # - When student 2 entered: 3 people in room.
    # - When student 3 entered: 1 person in room.
    # If student 3 entered first, total students = 3. So at that moment, room has 1 person? That implies only 1 person entered before 3. But there are 2 others (student 1 and 2).
    # So student 3 cannot have entered before 1 and 2.
    # Contradiction?
    # Let's re-read the problem statement extremely carefully.
    # "A_i students in the classroom when student number i entered the classroom (including student number i)."
    # "From these records, reconstruct the order in which the students entered the classroom."
    # Sample: 2 3 1 for students 1, 2, 3 respectively.
    # This means:
    # When student 1 entered: 2 people in room. (So 1 person was already there).
    # When student 2 entered: 3 people in room. (So 2 people were already there).
    # When student 3 entered: 1 person in room. (So 0 people were already there).
    # This implies:
    # - Student 3 entered first.
    # - Student 1 entered second.
    # - Student 2 entered third.
    # Order: 3, 1, 2.
    # Check:
    # When 3 enters: Room has {3} -> size 1. Matches A_3 = 1.
    # When 1 enters: Room has {3, 1} -> size 2. Matches A_1 = 2.
    # When 2 enters: Room has {3, 1, 2} -> size 3. Matches A_2 = 3.
    # YES.
    # So the order is strictly increasing with A_i?
    # Wait, in my previous reasoning I thought smallest A_i enters first.
    # Here: A_3 = 1 (smallest) enters first. A_1 = 2 enters second. A_2 = 3 enters last.
    # Yes, so the order is sorted by A_i ascending?
    # Let's check the indices.
    # A array: [A_1, A_2, ..., A_N] where A[i] is the value for student i.
    # Sample: A = [2, 3, 1].
    # Sorted A: [1, 2, 3] corresponding to students with A=1, A=2, A=3.
    # Students with A=1 is student 3.
    # Students with A=2 is student 1.
    # Students with A=3 is student 2.
    # Order: 3, 1, 2.
    # So the algorithm is:
    # For each student i, find their A_i.
    # Sort students by A_i ascending.
    # If A_i are distinct (given), the order is unique.
    
    # Implementation:
    # Create a list of (A_i, i)
    # Sort by A_i
    # Extract i's
    # Print them
    
    students = []
    for i in range(1, N + 1):
        students.append((A[i-1], i))
    
    students.sort(key=lambda x: x[0])
    
    # The result is the list of indices in sorted order
    result = [student[1] for student in students]
    
    print(" ".join(map(str, result)))

solve()
```

## PAIR 175  (task mbpp/101)

### A
```python
def kth_element(nums, k):
    return nums[k - 1]

assert kth_element([12,3,5,7,19], 2) == 3
```

### B
```python
def kth_element(arr: list[int], k: int) -> int:
    return arr[k - 1]

assert kth_element([12, 3, 5, 7, 19], 2) == 3
```

## PAIR 176  (task mbpp/2)

### A
```python
def similar_elements(*lists):
    """
    Returns a set of elements common to all provided lists.
    """
    if not lists:
        return set()
    
    # Start with the first list as the candidate set
    common_elements = set(lists[0])
    
    # Iterate through the remaining lists
    for list_item in lists[1:]:
        # Find the intersection of the current list with common_elements
        common_elements &= set(list_item)
    
    # Remove duplicates and sort if needed
    return sorted(common_elements)
```

### B
```python
def similar_elements(list1, list2):
    # Sort both lists to ensure consistent results regardless of input order
    list1 = sorted(list1)
    list2 = sorted(list2)
    
    # Find the intersection of both lists
    shared = list(set(list1) & set(list2))
    
    return sorted(shared)
```

## PAIR 177  (task mbpp/420)

### A
```python
def cube_Sum(n):
    """
    Calculate the sum of cubes of the first n even natural numbers.
    Example: cube_Sum(2) -> 2^3 + 4^3 = 8 + 64 = 72
    
    The sequence of even numbers is 2, 4, 6, 8, ...
    The k-th even number is 2*k.
    """
    if n <= 0:
        return 0
    
    total = 0
    for k in range(1, n + 1):
        even_number = 2 * k
        total += even_number ** 3
    return total
```

### B
```python
def cube_Sum(n):
    """
    Computes the sum of cubes of the first n even natural numbers.
    
    The first n even natural numbers are: 2, 4, 6, ..., 2*n
    Their cubes sum is: sum((2*k)**3 for k in range(1, n+1))
    """
    return sum((2*k)**3 for k in range(1, n + 1))
```

## PAIR 178  (task mbpp/605)

### A
```python
def prime_num(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

# Example tests
assert prime_num(13) == True
assert prime_num(14) == False
assert prime_num(7) == True
assert prime_num(1) == False
```

### B
```python
def prime_num(n):
    """Check if a given integer is a prime number."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
```

## PAIR 179  (task mbpp/120)

### A
```python
from typing import List, Tuple

def max_product_tuple(numbers: List[Tuple[int, int]]) -> int:
    """
    Find the maximum absolute product between numbers in pairs of tuples
    within the given list.

    Args:
        numbers: List of tuples, each containing two integers.

    Returns:
        The maximum absolute product found across all valid pairs.
    """
    if not numbers:
        return 0

    max_abs_prod = -float('inf')
    for first_tuple in numbers:
        if len(first_tuple) < 2:
            return 0
        first_val, second_val = first_tuple

        # Consider pairs: (first, first) -> 0, (first, second), (second, first), (second, second)
        # But based on common interpretations, we consider (first, second) only once
        # since the product of (a,b) equals (b,a) in absolute value.
        pair_prod = abs(first_val * second_val)
        if pair_prod > max_abs_prod:
            max_abs_prod = pair_prod

    return max_abs_prod
```

### B
```python
from typing import List, Tuple

def max_product_tuple(numbers: List[List[int]]) -> int:
    """
    Find the maximum absolute product between numbers in pairs of tuples within the given list.
    
    Args:
        numbers: A list of tuples, where each tuple contains two integers.
        
    Returns:
        The maximum absolute product between any two numbers in any pair of tuples.
        Only considers pairs within the same tuple (as specified by "pairs of tuples").
        
    Example:
        For inputs [(2, 7), (2, 6), (1, 8), (4, 9)], the result is 36.
        Pairs: (2,7)->14, (2,6)->12, (1,8)->8, (4,9)->36. 
        Absolute products: [14, 12, 8, 36] -> max = 36.
    """
    max_product = 0
    for t in numbers:
        if len(t) >= 2:
            a, b = t[0], t[1]
            product = abs(a * b)
            if product > max_product:
                max_product = product
    return max_product
```

## PAIR 180  (task mbpp/733)

### A
```python
def find_first_occurrence(arr, num):
    """Find the index of the first occurrence of num in a sorted array."""
    left, right = 0, len(arr) - 1
    result = -1

    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == num:
            result = mid
            right = mid - 1  # Try to find an earlier occurrence on the left
        elif arr[mid] < num:
            left = mid + 1
        else:
            right = mid - 1

    return result
```

### B
```python
def find_first_occurrence(nums, target):
    left, right = 0, len(nums) - 1
    index = -1

    while left <= right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        elif nums[mid] > target:
            right = mid - 1
        else:
            index = mid
            right = mid - 1  # try to find a later occurrence on the left

    return index if index != -1 else None
```

## PAIR 181  (task mbpp/392)

### A
```python
def get_max_sum(n):
    # Memoization dictionary to store results of subproblems
    memo = {}

    def f(x):
        if x <= 1:
            return x  # Base case: f(1) = 1, and for x <= 1 sum is just x
        if x in memo:
            return memo[x]

        # Compute recursively: sum over n/2, n/3, n/4, n/5
        sum_val = f(x // 2) + f(x // 3) + f(x // 4) + f(x // 5)
        # Add the current value x itself, which is always chosen over the sum
        result = max(sum_val, x)
        memo[x] = result
        return result

    return f(n)
```

### B
```python
def get_max_sum(n: int) -> int:
    """
    Calculate the maximum sum possible using the recurrence:
    f(n) = max( f(n/2) + f(n/3) + f(n/4) + f(n/5), n )
    
    This is implemented using a memoization dictionary.
    For small n, we use the base case n itself.
    For larger n, we recursively compute the max of the options.
    """
    memo = {}
    
    def solve(val: int) -> int:
        if val <= 1:
            return val
        if val in memo:
            return memo[val]
        
        res = val  # Option 1: take the value itself
        a = solve(val // 2)
        b = solve(val // 3)
        c = solve(val // 4)
        d = solve(val // 5)
        
        res = max(res, a + b + c + d)
        memo[val] = res
        return res
    
    return solve(n)
```

## PAIR 182  (task mbpp/628)

### A
```python
def replace_spaces(text: str) -> str:
    """
    Replaces all spaces in the input string with '%20'.
    
    :param text: The input string containing spaces.
    :return: A new string with all spaces replaced by '%20'.
    """
    return text.replace(" ", "%20")
```

### B
```python
def replace_spaces(s: str) -> str:
    # Replace spaces with '%20'
    result = s.replace(" ", "%20")
    return result
```

## PAIR 183  (task apps/4128)

### A
```python
import sys

def solve():
    # Read all input at once
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    t = int(next(iterator))

    results = []
    for _ in range(t):
        n = int(next(iterator))
        # We need to find number of pairs (a, b) such that:
        # a + b = n, a > 0, b > 0, a > b
        # Since a = n - b, we have:
        # n - b > b => 2b < n => b < n/2
        # Also b > 0
        # So b can range from 1 to floor((n-1)/2)
        # The count is simply floor((n-1)/2)
        
        ans = (n - 1) // 2
        results.append(str(ans))

    sys.stdout.write('\n'.join(results) + '\n')

if __name__ == '__main__':
    solve()
```

### B
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    if not data:
        return
    
    t = int(data[0])
    results = []
    
    idx = 1
    for _ in range(t):
        if idx >= len(data):
            break
        n = int(data[idx])
        idx += 1
        
        # We need to find number of pairs (a, b) such that:
        # a + b = n, a > b, a > 0, b > 0
        # Substituting b = n - a:
        # a > n - a => 2a > n => a > n/2
        # Also 0 < a < n (since b > 0)
        # So a can be any integer from floor(n/2) + 1 to n - 1
        # Count = (n - 1) - (floor(n/2) + 1) + 1 = n - floor(n/2) - 1
        
        if n % 2 == 1:
            # Odd n: floor(n/2) = (n-1)//2
            # Count = n - (n-1)//2 - 1 = (n+1)//2 - 1 = (n-1)//2
            count = (n - 1) // 2
        else:
            # Even n: floor(n/2) = n//2
            # Count = n - n//2 - 1
            count = n - n // 2 - 1
            
        results.append(str(count))
    
    sys.stdout.write('\n'.join(results) + '\n')

if __name__ == "__main__":
    solve()
```

## PAIR 184  (task mbpp/784)

### A
```python
def mul_even_odd(lst):
    evens = [x for x in lst if x % 2 == 0]
    odds = [x for x in lst if x % 2 != 0]
    if not evens or not odds:
        return 0
    return evens[0] * odds[0]

assert mul_even_odd([1,3,5,7,4,1,6,8])==4
```

### B
```python
def mul_even_odd(nums):
    evens = [x for x in nums if x % 2 == 0]
    odds = [x for x in nums if x % 2 == 1]
    
    return evens[0] * odds[0]
```

## PAIR 185  (task mbpp/579)

### A
```python
def find_dissimilar(t1: tuple, t2: tuple) -> set:
    """
    Return the set of elements present in either tuple but not in the other.

    Returns a set to handle unordered output and avoid duplicates.
    """
    return set(t1) ^ set(t2)  # XOR of the two set representations
```

### B
```python
from typing import Tuple, Set

def find_dissimilar(t1: Tuple[int, ...], t2: Tuple[int, ...]) -> Set[int]:
    return set(t1) ^ set(t2)
```

## PAIR 186  (task mbpp/614)

### A
```python
def cummulative_sum(tup_list):
    total = 0
    for tup in tup_list:
        total += sum(tup)
    return total
```

### B
```python
def cummulative_sum(tuple_list):
    result = 0
    for tup in tuple_list:
        result += sum(tup)
    return result
```

## PAIR 187  (task mbpp/455)

### A
```python
def check_monthnumb_number(n):
    """
    Check whether the given month number contains 31 days or not.
    Returns True if the month has 31 days, False otherwise.
    """
    return n in [1, 3, 5, 7, 8, 10, 12]
```

### B
```python
def check_monthnumb_number(month_num):
    """
    Check whether the given month number contains 31 days.
    
    Returns True if the month has 31 days, False otherwise.
    """
    # Month numbers with 31 days
    has_31_days = [1, 3, 5, 7, 8, 10, 12]
    
    return month_num in has_31_days
```

## PAIR 188  (task apps/4269)

### A
```python
def solve():
    s = input().strip()
    if s[1] == s[2] or s[2] == s[3] or s[0] == s[1]:
        print("Bad")
    else:
        print("Good")

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    s = sys.stdin.readline().strip()
    
    # Check if there are any two consecutive digits that are the same
    if s[0] == s[1] or s[1] == s[2] or s[2] == s[3]:
        print("Bad")
    else:
        print("Good")

if __name__ == "__main__":
    main()
```

## PAIR 189  (task mbpp/766)

### A
```python
def pair_wise(lst):
    """Return a list of all consecutive pairs in the list."""
    return [(lst[i], lst[i + 1]) for i in range(len(lst) - 1)]
```

### B
```python
def pair_wise(items):
    return [(items[i], items[i + 1]) for i in range(len(items) - 1)]
```

## PAIR 190  (task apps/4006)

### A
```python
def count_reachable(n: int) -> int:
    """
    Count the number of different numbers reachable from n by repeatedly applying f.
    f(x):
      - compute x + 1
      - remove trailing zeros
      - return the remaining number
    """
    if n == 0:
        # Special case: f(0) -> 1 -> ... -> infinite, but problem says 1 <= n <= 10^9
        return 0

    # Since 1 <= n <= 10^9, we can simulate the process.
    # We need to track the current number, its "root" (number that f(root)+1 would end up as),
    # and avoid cycles.
    #
    # Key observation:
    # Let root be the number such that f(root) = next_number and next_number has no trailing zeros.
    # Then for any x in the reachable chain from root, f(x) = next_number.
    # So the entire chain collapses into just next_number.
    # Thus, any number in the reachable set is either:
    #   - the root itself, or
    #   - some number that eventually leads to the root.
    #
    # Actually, the reachable set from x is the set of all y such that y can be reached from x.
    # But since f is a function, the reachable set is just {x, f(x), f(f(x)), ...}.
    # However, note that f is not injective but also not surjective on general integers.
    # But we only need to count the size of the set {x, f(x), f(f(x)), ...}.
    #
    # Important: We can't just follow the chain forever because it might cycle.
    # But given n <= 10^9, the sequence will eventually stop increasing and become constant.
    # Why? Because after removing trailing zeros, the number decreases or stabilizes.
    # Specifically, if x has trailing zeros, x+1 has at most one trailing zero (since x ends in non-zero? Wait).
    #
    # Let's trace carefully:
    # x ends in 9 -> x+1 = ...910 -> trailing zero -> remove -> ...91
    # x ends in 1..8 -> x+1 = ...x+1 (no trailing zero)
    #
    # The number of trailing zeros can only decrease or stay same, but since we remove trailing zeros,
    # the number strictly decreases unless it becomes constant.
    # Actually, the number of trailing zeros can stay the same only if adding 1 increases trailing zeros?
    # Example: 900 -> 901 (no trailing zeros), so count decreases.
    # Example: 100 -> 101 (count 0).
    # So the sequence is strictly decreasing until it reaches a number with no trailing zeros.
    #
    # Therefore, the sequence must converge to a number x with no trailing zeros.
    # Let that be the root.
    #
    # So we can simulate until the current number has no trailing zeros.
    # Since n <= 10^9, this will take very few steps (at most ~15-20 for 10^9, maybe up to ~50 for 10^100, but here 10^9).
    #
    # Algorithm:
    #   current = n
    #   visited = []
    #   while True:
    #       next_val = compute_next(current)
    #       if next_val is None:  # Should not happen given problem constraints
    #           next_val = None
    #       if next_val == current:
    #           break
    #       if next_val in visited:
    #           # Cycle detected
    #           # Remove all previously visited nodes to avoid infinite loop? 
    #           # But we need to count the size of the cycle too?
    #           # Actually, if we hit a visited node, the sequence will eventually repeat.
    #           # We should remove the visited nodes to prevent infinite loop and to continue from the next unvisited?
    #           # But the problem asks for the number of different numbers reachable from n.
    #           # If we hit a visited node, we can stop and output the count so far?
    #           # Not necessarily, because the sequence might loop but we already counted the nodes.
    #           # Actually, if we hit a visited node, the sequence will cycle, but we have already counted all unique nodes.
    #           # So we can break and output the count.
    #           break
    #       visited.append(next_val)
    #       current = next_val

    current = n
    visited = set()
    while current not in visited:
        visited.add(current)
        current = compute_next(current)

    return len(visited)


def compute_next(x: int) -> int:
    """Compute f(x): x+1, then remove trailing zeros."""
    x += 1
    while x % 10 == 0:
        x //= 10
    return x


def main():
    import sys
    # Read all input from stdin
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    try:
        n = int(input_data)
    except ValueError:
        return

    count = count_reachable(n)
    print(count)


if __name__ == "__main__":
    main()
```

### B
```python
def solve():
    import sys
    
    # Increase recursion depth for deep trees if necessary
    sys.setrecursionlimit(2000000)
    
    input = sys.stdin.read
    data = input().split()
    
    if not data:
        return
    
    n = int(data[0])
    
    reachable = set()
    visited = set()
    queue = [n]
    
    while queue:
        x = queue.pop(0)
        if x in visited:
            continue
        visited.add(x)
        reachable.add(x)
        
        if x == 1:
            # Once we hit 1, the next step will always be 2
            # But since we use a queue, we will naturally generate 2 next time
            # However, to ensure correctness with the "while trailing zeros" rule,
            # let's just let the simulation run. The queue approach handles it.
            pass
        
        # Compute f(x)
        # Add 1, then remove trailing zeros
        x = x + 1
        while x % 10 == 0:
            x //= 10
        
        queue.append(x)
    
    print(len(reachable))

if __name__ == "__main__":
    solve()
```

## PAIR 191  (task apps/4444)

### A
```python
def main():
    s, t = input().split()
    print(t + s)

if __name__ == "__main__":
    main()
```

### B
```python
def solve() -> None:
    import sys
    input = sys.stdin.read
    data = input().strip().split()
    assert len(data) == 2, "Input must contain exactly two strings"
    S, T = data[0], data[1]
    print(T + S)

if __name__ == "__main__":
    solve()
```

## PAIR 192  (task apps/4360)

### A
```python
import sys

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    # N is the first integer
    N = int(input_data[0])
    
    # The rest are A_i values
    # We expect N integers starting from index 1
    A = []
    for i in range(1, N + 1):
        A.append(int(input_data[i]))
    
    # Calculate the sum of inverses
    sum_inv = 0.0
    for x in A:
        sum_inv += 1.0 / x
    
    # Calculate the multiplicative inverse of the sum of inverses
    result = 1.0 / sum_inv
    
    # Print with sufficient precision
    print(result)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    input = sys.stdin.read().split()
    n = int(input[0])
    a = []
    for i in range(n):
        a.append(int(input[i + 1]))
    
    # Compute sum of inverses
    inv_sum = 0
    for x in a:
        if x > 0:  # Problem guarantees positive integers
            inv_sum += 1.0 / x

    # Compute multiplicative inverse of the sum
    result = 1.0 / inv_sum
    
    # Print with sufficient precision
    print(result)

if __name__ == "__main__":
    main()
```

## PAIR 193  (task mbpp/557)

### A
```python
def toggle_string(s):
    return ''.join(char.lower() if char.isupper() else char.upper() for char in s)
```

### B
```python
def toggle_string(s):
    if not s:
        return ""
    return s.swapcase()
```

## PAIR 194  (task apps/4325)

### A
```python
import sys

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    
    if len(input_data) < 3:
        return
    
    N = int(input_data[0])
    X = int(input_data[1])
    T = int(input_data[2])
    
    # Calculate number of batches needed (ceiling division)
    # Total capacity in one batch is X pieces
    # Batches needed = ceil(N / X)
    batches = (N + X - 1) // X
    
    # Total time is number of batches * time per batch
    print(batches * T)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    input_data = sys.stdin.read().strip().split()
    if len(input_data) < 3:
        return
    n, x, t = map(int, input_data)
    # Each batch takes T minutes regardless of how many pieces it can make (up to X)
    # Number of batches needed: ceil(N / X)
    batches_needed = (n + x - 1) // x
    minutes = batches_needed * t
    print(minutes)

if __name__ == "__main__":
    main()
```

## PAIR 195  (task mbpp/722)

### A
```python
def filter_data(data, min_height, min_weight):
    """
    Filters a dictionary of students to only include those who meet the 
    minimum height and weight requirements.
    
    Parameters:
    data (dict): Dictionary with student names as keys and (height, weight) as values
    min_height (float): Minimum acceptable height
    min_weight (float): Minimum acceptable weight
    
    Returns:
    dict: Dictionary containing only students meeting the minimum criteria
    """
    return {name: student for name, student in data.items() if student[0] >= min_height and student[1] >= min_weight}
```

### B
```python
def filter_data(student_dict, min_height, min_weight):
    """
    Filter students based on minimal height and weight thresholds.
    
    Parameters:
    student_dict (dict): Dictionary with student names as keys and (height, weight) as values
    min_height (float): Minimum height threshold
    min_weight (float): Minimum weight threshold
    
    Returns:
    dict: Dictionary containing only students who meet both thresholds
    """
    filtered_dict = {}
    for name, (height, weight) in student_dict.items():
        if height >= min_height and weight >= min_weight:
            filtered_dict[name] = (height, weight)
    return filtered_dict
```

## PAIR 196  (task mbpp/600)

### A
```python
def is_Even(n):
    """
    Check whether the given number is even or not.

    Returns:
        bool: True if the number is even, False otherwise.
    """
    return n % 2 == 0
```

### B
```python
def is_Even(number):
    """Check if a number is even."""
    return number % 2 == 0
```

## PAIR 197  (task mbpp/90)

### A
```python
def len_log(words):
    """
    Returns the length of the longest word in the list.
    
    Parameters:
    words (list of str): List of words
    
    Returns:
    int: Length of the longest word
    """
    if not words:
        return 0
    
    longest_word = max(words, key=len)
    return len(longest_word)
```

### B
```python
def len_log(words):
    """Return the length of the longest word in the list."""
    if not words:
        return 0
    return max(len(word) for word in words)
```

## PAIR 198  (task mbpp/247)

### A
```python
def lps(s):
    """
    Find the length of the longest palindromic subsequence in the given string.
    Uses the Longest Common Subsequence (LCS) dynamic programming approach
    where we transform the problem into finding the LCS of s and its reverse.
    """
    n = len(s)
    if n == 0:
        return 0

    # Reverse of the input string
    rev_s = s[::-1]

    # Create DP table
    # dp[i][j] stores the length of LCS of s[:i] and rev_s[:j]
    dp = [[0] * (n + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if s[i - 1] == rev_s[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[n][n]
```

### B
```python
def lps(s: str) -> int:
    n = len(s)
    if n == 0:
        return 0
    
    dp = [[0] * n for _ in range(n)]
    
    for i in range(n):
        dp[i][i] = 1
    
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 + dp[i + 1][j - 1]
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    
    return dp[0][n - 1]
```

## PAIR 199  (task apps/4334)

### A
```python
def solve():
    # Read S and T from the first line
    line1 = input().split()
    s = line1[0]
    t = line1[1]

    # Read A and B from the second line
    line2 = input().split()
    a = int(line2[0])
    b = int(line2[1])

    # Read U from the third line
    u = input().strip()

    # Takahashi throws one ball with string U away.
    # If A balls have string S and B balls have string T,
    # the number of balls with string S becomes A - 1 if U == S, else A.
    if u == s:
        s_count = a - 1
    else:
        s_count = a

    # Similarly for T: B - 1 if U == T, else B.
    if u == t:
        t_count = b - 1
    else:
        t_count = b

    # Print the result with a space in between
    print(s_count, t_count)


if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    # Read the input line by line (S T)
    line1 = sys.stdin.readline().strip()
    parts1 = line1.split()
    S, T = parts1[0], parts1[1]

    # Read the next line (A B)
    line2 = sys.stdin.readline().strip()
    parts2 = line2.split()
    A, B = int(parts2[0]), int(parts2[1])

    # Read the final input (U)
    line3 = sys.stdin.readline().strip()
    U = line3

    # Takahashi chooses one ball with string U and removes it.
    # Count how many balls left with string S and T.
    count_S = A - (1 if S == U else 0)
    count_T = B - (1 if T == U else 0)

    # Output the counts separated by a space
    print(count_S, count_T)

if __name__ == "__main__":
    main()
```

