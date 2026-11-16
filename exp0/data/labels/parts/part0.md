## PAIR 0  (task mbpp/762)

### A
```python
def check_monthnumber_number(month):
    if month == 4 or month == 6 or month == 9 or month == 11:
        return True
    return False
```

### B
```python
def check_monthnumber_number(month):
    if month in [4, 6, 9, 11]:
        return True
    return False
```

## PAIR 1  (task apps/4117)

### A
```python
import sys
from collections import Counter

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    iterator = iter(input_data)
    
    try:
        n_str = next(iterator)
        N = int(n_str)
    except StopIteration:
        return

    L = []
    for _ in range(N):
        try:
            l_val_str = next(iterator)
            L.append(int(l_val_str))
        except StopIteration:
            break
    
    # Count lengths and their frequencies
    length_counts = Counter(L)
    
    triangle_count = 0
    
    for i in range(N):
        l_i = L[i]
        count_i = length_counts[l_i]
        
        for j in range(i + 1, N):
            l_j = L[j]
            if l_j == l_i:
                continue  # Cannot choose different lengths
            
            count_j = length_counts[l_j]
            
            for k in range(j + 1, N):
                l_k = L[k]
                if l_k == l_i or l_k == l_j:
                    continue  # Must be all different lengths
                
                count_k = length_counts[l_k]
                
                # Check triangle inequality: a + b > c (where c is the largest)
                if l_i + l_j > l_k and l_i + l_k > l_j and l_j + l_k > l_i:
                    triangle_count += 1
    
    print(triangle_count)

if __name__ == "__main__":
    solve()
```

### B
```python
from sys import stdin

def solve():
    # Read all input from stdin
    lines = stdin.read().strip().split('\n')
    if not lines:
        return
    n = int(lines[0])
    L = list(map(int, lines[1].split()))

    triangle_count = 0

    # Sort the lengths to avoid recomputing for sorted versions
    L = sorted(L)

    # Precompute indices for each length in O(1)
    # To speed up, we can use a frequency array but N is small (100),
    # so direct iteration is fine.
    # Since we need distinct lengths, we can just iterate through triples and check.
    # With N=100, O(N^3) is 10^6, which is acceptable.
    # However, we can do O(N^2) by sorting first, then checking combinations.

    # Let's iterate through all triplets (i, j, k) with i < j < k
    # But first, to make it efficient enough and clean:
    # We'll iterate over indices. Since the array is sorted, 
    # if L[i] == L[j] or L[j] == L[k], they don't count (distinct lengths).

    # Actually, since N <= 100, O(N^3) is perfectly fine and simplest.
    # 100^3 = 1,000,000 operations, well within Python's limits for this problem.

    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                # Check distinct lengths
                if L[i] == L[j] or L[j] == L[k] or L[i] == L[k]:
                    continue
                
                # Check triangle inequality
                # In a sorted triangle (a <= b <= c), we only need a + b > c
                if L[i] + L[j] > L[k]:
                    triangle_count += 1

    print(triangle_count)

if __name__ == "__main__":
    solve()
```

## PAIR 2  (task mbpp/736)

### A
```python
def left_insertion(arr, value):
    """
    Find the leftmost insertion point for `value` in a sorted list.
    
    Parameters:
    arr (list): Sorted list of numbers
    value (int or float): The value to insert
    
    Returns:
    int: The index of the leftmost position where value can be inserted
    """
    low = 0
    high = len(arr)
    
    while low < high:
        mid = (low + high) // 2
        if arr[mid] < value:
            low = mid + 1
        else:
            high = mid
            
    return low
```

### B
```python
def left_insertion(arr, val):
    left = 0
    right = len(arr)
    while left < right:
        mid = (left + right) // 2
        if arr[mid] < val:
            left = mid + 1
        else:
            right = mid
    return left
```

## PAIR 3  (task mbpp/224)

### A
```python
def count_Set_Bits(n):
    """Count the number of set bits (1s) in the binary representation of n."""
    return bin(n).count('1')
```

### B
```python
def count_Set_Bits(n: int) -> int:
    """Return the number of set bits (1s) in the binary representation of n."""
    if n < 0:
        return n.bit_count()
    return n.bit_count()
```

## PAIR 4  (task apps/4179)

### A
```python
def solve():
    # Read N, M, C
    n_m_c = input().split()
    N, M, C = int(n_m_c[0]), int(n_m_c[1]), int(n_m_c[2])

    # Read B array
    b = list(map(int, input().split()))

    # Read A for each code
    codes = []
    for _ in range(N):
        row = list(map(int, input().split()))
        codes.append(row)

    count = 0
    for code in codes:
        # Compute weighted sum + C
        s = sum(a * b for a, b in zip(code, b)) + C
        if s > 0:
            count += 1

    print(count)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    # Read all tokens from stdin
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return

    # Parse N, M, C
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
        M = int(next(iterator))
        C = int(next(iterator))
        
        # Parse B array
        B = [int(next(iterator)) for _ in range(M)]
        
        # Read A for each code (N codes, each with M integers)
        A = []
        for _ in range(N):
            row = [int(next(iterator)) for _ in range(M)]
            A.append(row)
    except StopIteration:
        return

    # Count how many codes satisfy A_i dot B + C > 0
    count = 0
    for code in A:
        score = sum(code[i] * B[i] for i in range(M)) + C
        if score > 0:
            count += 1

    print(count)

if __name__ == "__main__":
    main()
```

## PAIR 5  (task mbpp/799)

### A
```python
def left_rotate(num, d):
    if num == 0:
        return 0
    return ((num << d) | ((num >> (32 - d)) & 0xFFFFFFFF)) % (2**32)
```

### B
```python
def left_rotate(num, d):
    """
    Rotate a 32-bit integer left by d bits.
    
    Assumes num and d are integers, and we consider num as a 32-bit two's complement 
    integer (so shifting left by >= 32 wraps around).
    
    :param num: A 32-bit signed integer (assumed to be treated as unsigned for rotation).
    :param d: Number of bits to rotate left.
    :return: Rotated 32-bit integer.
    """
    if d == 0:
        return num
    # Use modulo 32 for the rotation amount to wrap around properly for 32-bit integers
    d = d % 32
    # Ensure d is within [0, 32)
    if d >= 32:
        d -= 32
    # For signed interpretation, if num is negative, shifting left by 32 or more bits wraps to a positive 
    # value in two's complement. However, for rotation, we interpret num as an unsigned 32-bit value.
    # In Python, we can do this by masking with 0xFFFFFFFF if we want to treat it as unsigned.
    # But since the test case uses 16 and 2, let's just do a standard left shift with mask.
    return ((num << d) & 0xFFFFFFFF) | ((num & 0xFFFFFFFF) >> (32 - d))
```

## PAIR 6  (task apps/4153)

### A
```python
import sys
from collections import Counter

def solve():
    s = sys.stdin.readline().strip()
    if not s:
        return

    # Count occurrences of '0' (red) and '1' (blue)
    count_red = Counter(s)['0']
    count_blue = Counter(s)['1']

    # We can pair each blue with a red cube, so the maximum number of pairs is min(red, blue)
    pairs = min(count_red, count_blue)

    # Total cubes removed = 2 * pairs
    print(2 * pairs)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    s = sys.stdin.read().strip()
    if not s:
        return
    n = len(s)
    
    # Count total red and blue cubes
    red = s.count('0')
    blue = s.count('1')
    
    # Maximum cubes that can be removed is 2 * min(red, blue)
    # This is because each operation removes exactly one red and one blue,
    # and operations can only happen between adjacent colors.
    max_removed = 2 * min(red, blue)
    print(max_removed)

if __name__ == "__main__":
    solve()
```

## PAIR 7  (task apps/4494)

### A
```python
s = input()
# Alternate between ABC and ARC starting from ARC (last was ABC)
if s == "ABC":
    print("ARC")
else:
    print("ABC")
```

### B
```python
S = input()

if S == "ABC":
    print("ARC")
else:  # S == "ARC"
    print("ABC")
```

## PAIR 8  (task mbpp/95)

### A
```python
def Find_Min_Length(lists):
    if not lists or not isinstance(lists, list):
        raise TypeError("Input must be a non-empty list of lists.")
    return min(len(x) for x in lists)
```

### B
```python
def Find_Min_Length(lists):
    if not lists:
        return 0
    lengths = [len(lst) for lst in lists]
    return min(lengths)
```

## PAIR 9  (task mbpp/8)

### A
```python
def square_nums(nums):
    return [num**2 for num in nums]
```

### B
```python
def square_nums(nums):
    return [x * x for x in nums]
```

## PAIR 10  (task mbpp/88)

### A
```python
def freq_count(lst):
    freq = {}
    for item in lst:
        freq[item] = freq.get(item, 0) + 1
    return freq
```

### B
```python
from collections import Counter

def freq_count(nums):
    return dict(Counter(nums))
```

## PAIR 11  (task mbpp/309)

### A
```python
def maximum(a, b):
    return a if a > b else b
```

### B
```python
def maximum(x, y):
    return x if x > y else y
```

## PAIR 12  (task mbpp/754)

### A
```python
def extract_index_list(l1, l2, l3):
    """
    Find common elements between three lists l1, l2, and l3.
    An element is common if it appears in all three lists at the same index.

    Args:
        l1 (list): First list of integers
        l2 (list): Second list of integers
        l3 (list): Third list of integers

    Returns:
        list: List of common elements
    """
    if not l1 and not l2 and not l3:
        return []

    # Find indices where all three lists have the same element
    common_elements = []
    for i in range(min(len(l1), len(l2), len(l3))):
        if l1[i] == l2[i] == l3[i]:
            common_elements.append(l1[i])

    return common_elements
```

### B
```python
def extract_index_list(l1, l2, l3):
    """
    Find elements that are common to all three lists under the same index.
    
    An element is considered common if it appears in all three lists at the 
    same position (i.e., l1[i] == l2[i] == l3[i]).
    
    Args:
        l1, l2, l3: Lists of elements (integers).
    
    Returns:
        List containing common elements at matching indices, in order.
    """
    common = []
    for i in range(min(len(l1), len(l2), len(l3))):
        if l1[i] == l2[i] == l3[i]:
            common.append(l1[i])
    return common
```

## PAIR 13  (task apps/4385)

### A
```python
import sys

def solve():
    try:
        lines = sys.stdin.read().split()
    except Exception:
        return

    if len(lines) < 6:
        return

    a, b, c, d, e = map(int, lines[:5])
    k = int(lines[5])

    # Check all pairs (i, j) where i < j
    # Since coordinates are a, b, c, d, e and a < b < c < d < e,
    # we just need to check distances between all pairs.
    impossible = False
    
    # We can check by sorting the list of coordinates (they are already sorted)
    antennas = [a, b, c, d, e]
    
    for i in range(len(antennas)):
        for j in range(i + 1, len(antennas)):
            dist = antennas[j] - antennas[i]
            if dist > k:
                impossible = True
                break
        if impossible:
            break
    
    if impossible:
        print(":(")
    else:
        print("Yay!")

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    # Read all integers from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Convert to integers
    a = int(input_data[0])
    b = int(input_data[1])
    c = int(input_data[2])
    d = int(input_data[3])
    e = int(input_data[4])
    k = int(input_data[5])

    # All coordinates in ascending order: a < b < c < d < e
    antennas = [a, b, c, d, e]
    
    # Iterate through all pairs of antennas (i, j) with i < j
    for i in range(5):
        for j in range(i + 1, 5):
            distance = antennas[j] - antennas[i]
            if distance > k:
                print(":(")
                return
    print("Yay!")

if __name__ == "__main__":
    main()
```

## PAIR 14  (task mbpp/292)

### A
```python
def find(a, b):
    return a // b
```

### B
```python
import math

def find(a, b):
    """Find the quotient of two numbers rounded down to the nearest integer."""
    return math.floor(a / b)
```

## PAIR 15  (task apps/4368)

### A
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    if not data:
        return
    N = int(data[0])
    K = int(data[1])

    # Number of digits in base K = floor(log_K(N)) + 1
    # Equivalent to while K^i <= N, increment i, then subtract 1 from count
    digits = 0
    power = 1
    while power <= N:
        power *= K
        digits += 1

    print(digits)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    if len(input_data) < 2:
        return
    N = int(input_data[0])
    K = int(input_data[1])

    if N == 0:
        print(1)
        return

    digits = 0
    temp = N
    while temp > 0:
        temp //= K
        digits += 1
    print(digits)

if __name__ == "__main__":
    solve()
```

## PAIR 16  (task mbpp/172)

### A
```python
def count_occurance(s):
    count = s.count('std')
    return count
```

### B
```python
def count_occurance(s):
    return s.count('std')
```

## PAIR 17  (task mbpp/725)

### A
```python
import re

def extract_quotation(text):
    """
    Extracts all strings enclosed in double quotation marks " " from the input text.
    
    Args:
        text (str): Input string to process.
        
    Returns:
        List[str]: List of extracted quoted strings.
    """
    pattern = r'"([^"]*)"'
    return re.findall(pattern, text)
```

### B
```python
import re

def extract_quotation(s: str) -> list[str]:
    """Extract all strings that are enclosed in double quotes in the given string."""
    return re.findall(r'"([^"]*)"', s)
```

## PAIR 18  (task mbpp/804)

### A
```python
def is_product_even(numbers):
    if not numbers:
        return False
    product = 1
    for num in numbers:
        product *= num
        if product % 2 == 0:
            return True
    return product % 2 == 0
```

### B
```python
def is_product_even(numbers):
    product = 1
    for n in numbers:
        product *= n
    return product % 2 == 0
```

## PAIR 19  (task apps/4115)

### A
```python
def solve():
    s = input()
    n = len(s)
    # For each position i, we can match s[i] with s[n-1-i].
    # If they are different, one character must be changed.
    # Count pairs (i, n-1-i) where s[i] != s[n-1-i].
    ans = 0
    for i in range(n // 2):
        if s[i] != s[n - 1 - i]:
            ans += 1
    print(ans)

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    s = input()
    n = len(s)
    hugs = 0
    # Compare characters from both ends moving inward
    for i in range(n // 2):
        if s[i] != s[n - 1 - i]:
            # One mismatch, need 1 hug to fix it
            hugs += 1
    print(hugs)

solve()
```

## PAIR 20  (task mbpp/68)

### A
```python
def is_Monotonic(arr):
    if not arr:
        return True
    
    first = arr[0]
    is_non_decreasing = True
    is_non_increasing = True
    
    for i in range(1, len(arr)):
        if arr[i] < first:
            is_non_decreasing = False
        if arr[i] > first:
            is_non_increasing = False
        
        first = arr[i]
    
    if is_non_decreasing and is_non_increasing:
        return True
    elif is_non_decreasing or is_non_increasing:
        return True
    
    return False
```

### B
```python
def is_Monotonic(arr):
    if len(arr) < 2:
        return True
    ascending = True
    descending = True
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            descending = False
        elif arr[i] < arr[i + 1]:
            ascending = False
    if (ascending and descending) or (ascending and ascending) or (descending and descending):
        return True
    return False
```

## PAIR 21  (task mbpp/273)

### A
```python
def substract_elements(t1: tuple, t2: tuple) -> tuple:
    return tuple(a - b for a, b in zip(t1, t2))
```

### B
```python
def substract_elements(t1: tuple, t2: tuple):
    """
    Takes two tuples and subtracts the elements of the first tuple by 
    the elements of the second tuple with the same index.

    :param t1: First tuple of numbers
    :param t2: Second tuple of numbers
    :return: New tuple with elements calculated as t1[i] - t2[i]
    """
    result = tuple(t1[i] - t2[i] for i in range(len(t1)))
    return result
```

## PAIR 22  (task apps/4485)

### A
```python
import sys

def main():
    # Read all input from stdin
    input_data = sys.stdin.read().split()

    if not input_data:
        return

    iterator = iter(input_data)

    # Read N and M
    try:
        n = int(next(iterator))
        m = int(next(iterator))
    except StopIteration:
        return

    # Use adjacency list: island_index -> list of islands it connects to
    adj = [[] for _ in range(n + 1)]
    
    for _ in range(m):
        a = int(next(iterator))
        b = int(next(iterator))
        adj[a].append(b)
        adj[b].append(a)  # Undirected graph

    # Cat starts at Island 1, wants to reach Island N using exactly 2 boat services
    # BFS from 1, track how many edges taken (1st or 2nd)
    from collections import deque

    q = deque([1])
    dist = [-1] * (n + 1)
    dist[1] = 0

    visited_count = 0  # to ensure we use exactly 2 edges
    
    possible = False
    while q:
        u = q.popleft()
        current_dist = dist[u]

        # If we reached N with exactly 2 edges
        if u == n and current_dist == 2:
            possible = True
            break

        for v in adj[u]:
            if v != dist[u]:  # avoid going back
                if dist[v] == -1:
                    dist[v] = current_dist + 1
                    q.append(v)
                    # If we reached N with 2 edges via another branch
                    if u == n and current_dist == 1:
                        possible = True
                        break
    if dist[n] != -1 and dist[n] == 2:
        possible = True
    else:
        # Re-verify logic: check if we can reach N with exactly 2 edges
        # Try BFS again to track path length explicitly
        q = deque([1])
        dist = [10**9] * (n + 1)
        dist[1] = 0
        possible = False
        
        while q:
            u = q.popleft()
            current_len = dist[u]
            
            if u == n and current_len == 2:
                possible = True
                break
                
            for v in adj[u]:
                if v != dist[u]:
                    if dist[v] > current_len + 1:
                        dist[v] = current_len + 1
                        q.append(v)
        
        # Re-check if N is reachable via path of length exactly 2
        possible = (dist[n] == 2)

    if possible:
        print("POSSIBLE")
    else:
        print("IMPOSSIBLE")

if __name__ == '__main__':
    main()
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
        N = int(next(iterator))
        M = int(next(iterator))
    except StopIteration:
        return

    # Build adjacency list
    adj = [[] for _ in range(N + 1)]
    edges = []
    for _ in range(M):
        a = int(next(iterator))
        b = int(next(iterator))
        edges.append((a, b))
        adj[a].append(b)
        adj[b].append(a)

    # Check if there's a cycle of length exactly 2 using edges
    # That is, find two distinct edges (u, v) and (v, w) or (v, w) and (u, v)
    # such that the path u -> v -> w or v -> w -> u exists? 
    # Actually, we want: a path from 1 -> x -> N using two edges.
    # That is, 1 -> x, then x -> N.
    # So we just need to know if there exists an x such that (1, x) and (x, N) are both edges.
    
    found = False
    for (u, v) in edges:
        if u == 1:
            if v == N:
                # This would be 1 -> N directly, but problem says it's impossible.
                # However, per constraints (a_i, b_i) != (1, N), so we won't get this case.
                pass
            else:
                # 1 -> v, now check if v -> N exists
                if v in adj[N]:
                    found = True
                    break
        # Similarly, check if there's another x such that 1 -> x and N -> x (since graph is undirected)
        # Actually the condition is symmetric: does there exist x such that 1->x and x->N?
        # Because edges are bidirectional in the graph, (1, x) exists iff x exists on a path from 1 to N via x.
        # Wait, the graph is undirected as constructed.
        # So 1 -> x -> N is valid iff edges (1, x) and (x, N) exist.
        # Our loop checks (1, x) and checks if x is adjacent to N.
        # We iterate over all edges. If edge is (1, x), we check x in adj[N].
        # But we also need to consider the other direction? 
        # No, because edges are undirected, if (1, x) exists, then (x, 1) exists too.
        # But our adj list stores both directions.
        # The condition "1 -> x -> N" means we need an edge 1->x and an edge x->N.
        # Since adj is built symmetrically, we can just check if any x has edge to 1 and edge to N.
        
    # Let's re-iterate more carefully:
    # We need to find if there exists an x such that adj[1][0] == x and adj[x][0] == N? 
    # Actually, since adj is symmetric, checking adj[1] for N is enough.
    # But to be safe and clear:
    # For each x in 2..N-1:
    #   if 1 is connected to x and x is connected to N, then POSSIBLE.
    
    # Simpler: build the graph, then run BFS/DFS from 1 to see which nodes are reachable.
    # But that doesn't directly give 1->x->N.
    
    # Correct logic:
    # We need to know if there is any vertex x (distinct from 1 and N) such that:
    #   1 is connected to x AND x is connected to N.
    # In an undirected graph, 1->x and x->N is the same as N->x and x->1.
    # So we can just check:
    #   Is x adjacent to 1? and is x adjacent to N?
    # If yes, then 1 -> x -> N is a path of length 2.
    
    # So we can do:
    # For x from 2 to N-1:
    #   if 1 in adj[x] and N in adj[x]:
    #       found = True; break
    
    # But doing this per x is O(N) which is fine for N=200,000.
    # Alternatively, since graph is small, we can just check neighbors of 1 and neighbors of N.
    
    neighbors_of_1 = adj[1]
    neighbors_of_N = adj[N]
    
    if set(neighbors_of_1).intersection(neighbors_of_N):
        found = True
    
    if found:
        print("POSSIBLE")
    else:
        print("IMPOSSIBLE")

solve()
```

## PAIR 23  (task mbpp/800)

### A
```python
def remove_all_spaces(s):
    return s.replace(" ", "")
```

### B
```python
def remove_all_spaces(s):
    return s.replace(' ', '')
```

## PAIR 24  (task mbpp/397)

### A
```python
def median_numbers(a, b, c):
    return sorted([a, b, c])[1]
```

### B
```python
def median_numbers(a, b, c):
    numbers = [a, b, c]
    sorted_numbers = sorted(numbers)
    if len(sorted_numbers) == 1:
        return float(sorted_numbers[0])
    elif len(sorted_numbers) == 2:
        return sorted_numbers[0] + sorted_numbers[1]
    else:
        return float(sorted_numbers[1])
```

## PAIR 25  (task mbpp/807)

### A
```python
def first_odd(numbers):
    for num in numbers:
        if num % 2 != 0:
            return num
    return None

assert first_odd([1, 3, 5]) == 1
assert first_odd([2, 4, 6]) is None
assert first_odd([1, 2, 3]) == 1
```

### B
```python
def first_odd(nums):
    for num in nums:
        if num % 2 != 0:
            return num
    return None
```

## PAIR 26  (task apps/4224)

### A
```python
def solve():
    import sys
    input = sys.stdin.read
    data = input().split()
    
    if not data:
        return
    
    N = int(data[0])
    A = list(map(int, data[1:]))
    
    if not A:
        print(0)
        return
    
    # Count factors of 2 for each number
    # a_i = 2^k * odd_part, where odd_part is odd
    # Each time we divide by 2, we reduce the exponent of 2 by 1.
    # Each time we multiply by 3, the odd part stays the same (multiplication by 3 doesn't change the number of 2s).
    # So for each number, we can reduce its power of 2 by at most its count of factors of 2.
    
    total_ops = 0
    for x in A:
        # Count how many times x is divisible by 2
        while x % 2 == 0:
            x //= 2
            total_ops += 1
    
    print(total_ops)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    idx = 0

    n = int(data[idx])
    idx += 1

    a = []
    for i in range(n):
        a.append(int(data[idx]))
        idx += 1

    # Simulate the process using a greedy approach:
    # Since we want to maximize total operations, and we can choose independently
    # for each element whether to multiply by 3 or divide by 2 (subject to integrality),
    # this is equivalent to: for each prime factor of the target power of 2,
    # decide whether to "split" the 2s into more 3s (multiply by 3) or keep them as 2s.
    #
    # Actually, a simpler view:
    # For any a_i = 2^k * 3^m, we can convert 3^m * 2^k into 3^{m+1} * 2^{k-1}
    # (multiply by 3, divide by 2).
    # We can repeat this until we cannot do it.
    #
    # So for each number a_i, we:
    #   1. Factor out all 2s, giving a_i = 2^k * odd_part.
    #   2. We can perform operations that turn a 2 into a 3 and reduce the exponent of 2 by 1.
    #      Effectively, we can pair up each 2 with a 3 we create.
    #   3. The total number of such pairs we can form is min(k, number_of_3s_available_in_a_i).
    #      But wait, we can also convert a 3 into a 2 (divide by 3, multiply by 2) only if we have a 3.
    #      However, the operation is: multiply by 3, divide by 2. This increases the power of 3
    #      and decreases the power of 2.
    #
    # Actually, let's think in terms of prime factorization.
    # Let a_i = 2^k * 3^m * other_primes.
    # We can perform an operation if the number is even and divisible by 3? No.
    # Operation: a_i = 3 * (a_i / 2)
    # So a_i must be divisible by 2 but after division by 2, we must be able to multiply by 3.
    # The constraint "value must be an integer" is satisfied if original a_i is divisible by 2.
    # After dividing by 2, we get a_i/2. Then we multiply by 3: a_i = 3 * a_i/2.
    # So the operation changes the exponent of 2 from k to k-1, and the exponent of 3 from m to m+1.
    #
    # We can perform this operation as long as a_i is divisible by 2.
    # But we also have the constraint that we can only do this if the resulting number is an integer,
    # which is guaranteed if we start with even numbers. However, after many operations,
    # we might end up with odd numbers where we can't apply the operation on the '2' side anymore.
    #
    # Actually, observe that the '2' exponent decreases by 1 per operation, while the '3' exponent increases by 1.
    # So the total number of operations we can do on a_i is limited by the total number of 2s we can create,
    # which is bounded by the initial exponent of 2 (since we cannot create 2s from 3s or anything else;
    # we only turn 2s into 3s, and we can turn 3s into 2s if we have a 3).
    #
    # Wait, we can also divide by 3 and multiply by 2 if the number is divisible by 3?
    # The problem says: "For every i, perform one of the following: 'divide a_i by 2' and 'multiply a_i by 3'."
    # It does NOT allow dividing by 3. So we cannot directly turn a 3 into a 2.
    # We can only turn a 2 into a 3 (and reduce the power of 2).
    #
    # So for each a_i:
    #   - We can have some 2s, some 3s.
    #   - We can apply operation: (3, 2) -> (1, 3). This consumes a 2 and creates a 3.
    #   - Since we cannot create a 2 from a 3, the total number of 2s we ever have will never increase.
    #   - Therefore, the maximum number of operations on a_i is exactly the total number of 2s in a_i.
    #     Why? Because each operation reduces the count of 2s by 1, and we can keep doing it as long as there is at least one 2.
    #     But wait, we can also create 3s, which might be needed for future operations? No,
    #     because there's no way to create a 2 from a 3. The only way to get rid of 2s is to convert them to 3s.
    #     So the total number of 2s is non-increasing, and we can convert as many 2s as possible into 3s.
    #     Since we can do this as long as there's a 2, the limit is simply the total count of 2s.
    #
    # Let's verify with sample: a = {5, 2, 4}
    # 5 = 2^0 * 5^1: no 2s -> 0 operations
    # 2 = 2^1 * 2^0: one 2 -> 1 operation
    # 4 = 2^2 * 2^0: two 2s -> 2 operations
    # Total = 0 + 1 + 2 = 3. Matches sample output.
    #
    # Another check: a = {6} = 2^1 * 3^1
    # 6 has one 2 -> we can do 6 -> 3*3 = 9. Operations: 1.
    # Can we do more? From 9, no 2s, so stop. Total 1.
    #
    # Another check: a = {12} = 2^2 * 3^1
    # 12 -> 6 -> 3*3 = 9. Two operations. Correct.
    #
    # So the algorithm is: for each number, count the exponent of 2, sum them up, and print the total.

    total_ops = 0

    for x in a:
        k = 0
        while x % 2 == 0:
            k += 1
            x //= 2
        total_ops += k

    print(total_ops)

if __name__ == "__main__":
    solve()
```

## PAIR 27  (task mbpp/170)

### A
```python
def sum_range_list(nums, start, end):
    if start < 0:
        start = 0
    if end >= len(nums):
        end = len(nums) - 1
    if start > end:
        return 0
    
    return sum(nums[start:end+1])
```

### B
```python
def sum_range_list(nums, start, end):
    start = max(0, start)
    end = min(len(nums) - 1, end)
    return sum(nums[i] for i in range(start, end + 1))
```

## PAIR 28  (task mbpp/728)

### A
```python
def sum_list(list1, list2):
    """
    Takes two lists of the same length and returns the element-wise sum.
    """
    return [a + b for a, b in zip(list1, list2)]
```

### B
```python
def sum_list(a_list, b_list):
    if len(a_list) != len(b_list):
        raise ValueError("Input lists must have the same length")
    return [x + y for x, y in zip(a_list, b_list)]
```

## PAIR 29  (task apps/4436)

### A
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    idx = 0
    
    t = int(data[idx])
    idx += 1
    
    results = []
    
    for _ in range(t):
        n = int(data[idx])
        idx += 1
        
        # We need to find three distinct integers a, b, c >= 2 such that a*b*c = n.
        # Since n <= 10^9, we can iterate to find factors.
        # We'll iterate from smallest possible factors.
        
        found = False
        answer_parts = []
        
        # Try to find factors in increasing order
        # To avoid checking permutations, we can assume w.l.o.g. a <= b <= c
        # But since we just need any valid triplet, we can iterate more flexibly.
        
        # Approach:
        # Try to find one factor a from 2 to n^(1/3) (roughly)
        # Actually, a must be at least cube root of n to leave space for two >=2 factors.
        # Let's iterate a from 2 up to int(n**(1/3)) or slightly more to be safe,
        # but we must ensure we cover all possibilities.
        
        # Better strategy:
        # Find the smallest factor a (>=2)
        # Then find the largest factor c (>= n/a)
        # If c != n/a, try to find b such that b*c = n/a and b != a, b != c
        
        # Optimization:
        # Since we want distinct a,b,c, let's fix a and c first?
        # Actually, simplest is:
        # a in [2, n]
        # b in [a+1, n]
        # c = n / (a*b)
        # But we want distinct and c must be integer >= 2.
        
        # Since n <= 10^9, we can do:
        # Find smallest factor a of n (>= 2)
        # Then find largest factor c of (n/a) (>= a+1 or just >= b)
        # Then check if c is valid
        
        # But we need to avoid duplicates. Let's just iterate a and then c.
        
        # Let's try:
        # Iterate a from 2 to n (but stop when a*a*a > n roughly)
        # Actually, we can iterate a from 2 up to int(n**(1/3)) + 2
        # Then find c = n // a
        # Then iterate b from a+1 to int((n/a)^(1/2)) + 1
        # Check if c % b == 0 and c != b and b != a and c > 2
        
        # But this is not quite right because b could be larger than n/a^(1/2).
        # Instead, let's do:
        # a from 2 to int(n**(1/3))
        # Then c = n // a
        # Then b must be a factor of c and b != a, b != c, b >= 2
        
        # But this misses cases where a is not a cube root.
        
        # Correct generic approach:
        # Find smallest factor a of n (>= 2)
        # Then find largest factor c of n (>= a+1) such that c > a
        # Actually simpler:
        # a from 2 to int(n**(1/2))
        #   for each a, try to find b and c such that a*b*c = n, distinct, >=2
        #   b from a+1 to int(sqrt(n/a))
        #   check if (n/(a*b)) % b == 0 and ...
        
        # Given n up to 10^9, O(sqrt(n)) per test case is acceptable (sqrt(10^9) = 31622, t=100 => 3*10^6 ops).
        
        # Let's implement the nested loop:
        
        a_start = 2
        a_end = int(n**0.5) + 2  # Just for safety, actually we need up to cube root?
        # Wait, if a*b*c = n and a <= b <= c, then a*a*a <= n => a <= n^(1/3).
        # So we can limit a to int(n**(1/3)) + 2.
        
        limit = int(n**(1/3)) + 2
        
        for a in range(a_start, limit + 1):
            if n % a != 0:
                continue
            
            c_part = n // a
            # Now we need b such that b * c = c_part, b != a, b != c, b >= 2
            # Since c_part = n/a, and a >= 2, c_part <= n/2
            # Also we need b >= a (to avoid duplicates and maintain order)
            
            # Iterate b from a to int((c_part)**0.5) + 1
            # But we need to ensure b != a and b != c
            
            b_min = a
            b_max = int((c_part)**0.5) + 1
            
            for b in range(b_min, b_max + 1):
                if c_part % b != 0:
                    continue
                
                c = c_part // b
                
                # Check constraints: distinct, >= 2
                if b < 2 or c < 2:
                    continue
                
                if b == a or b == c or a == c:
                    continue
                
                # All good
                found = True
                answer_parts.append(str(a))
                answer_parts.append(str(b))
                answer_parts.append(str(c))
                break  # found a valid triplet
            if found:
                break
        
        if found:
            results.append("YES")
            results.append(" ".join(answer_parts))
        else:
            results.append("NO")
    
    print("\n".join(results))

if __name__ == "__main__":
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
    cases = data[1:]
    
    results = []
    
    for i in range(t):
        n = int(cases[i])
        
        # We need a, b, c >= 2 distinct integers such that a * b * c = n.
        # Try smallest possible factors in increasing order.
        # Since a < b < c, we can iterate a from 2 up to cube_root(n).
        # But since n <= 10^9, cube_root is around 1000. This is fast enough.
        
        limit = int(n ** (1/3)) + 2  # slightly above cube root
        
        found = False
        res = [0, 0, 0]
        
        # Try a as a possible factor
        for a in range(2, limit):
            if n % a != 0:
                continue
            
            rem = n // a
            # Now find two distinct factors b, c from rem such that b < c and b * c = rem
            # Also a, b, c must be distinct.
            # Since a < b < c, we have a * b < c * b = rem => b < sqrt(rem)
            b_limit = int(rem ** (1/2)) + 1
            
            # Iterate b from 2 up to b_limit
            for b in range(2, b_limit + 1):
                if rem % b == 0:
                    c = rem // b
                    # Check distinctness: a, b, c must be different
                    if a != b and a != c and b != c:
                        res = [a, b, c]
                        found = True
                        break
            if found:
                break
        
        if found:
            results.append("YES " + " ".join(map(str, res)))
        else:
            results.append("NO")

    print('\n'.join(results))

if __name__ == "__main__":
    solve()
```

## PAIR 30  (task mbpp/232)

### A
```python
def larg_nnum(lst, n):
    """Return the n largest items from the list as a set."""
    if n <= 0 or n > len(lst):
        return set()
    
    return set(sorted(lst)[-n:])
```

### B
```python
def larg_nnum(lst, n):
    """Return a list containing the n largest items from the list."""
    if n <= 0:
        return []
    return sorted(lst, reverse=True)[:n]
```

## PAIR 31  (task apps/4318)

### A
```python
def main():
    N = int(input())
    H = list(map(int, input().split()))

    # There is always at least one inn that can see the ocean (the westmost one).
    # Count from the westmost mountain.
    count = 1
    prev_height = H[0]

    for i in range(1, N):
        if H[i] >= prev_height:
            count += 1
            prev_height = H[i]

    print(count)

if __name__ == "__main__":
    main()
```

### B
```python
def solve():
    n_str = input().strip()
    if not n_str:
        return
    n = int(n_str)
    
    h = list(map(int, input().strip().split()))
    
    count = 0
    for i in range(n):
        can_see_ocean = True
        for j in range(i + 1):
            if h[j] > h[i]:
                can_see_ocean = False
                break
        if can_see_ocean:
            count += 1
    print(count)

solve()
```

## PAIR 32  (task apps/4274)

### A
```python
def main():
    # Read integers N and M from standard input
    import sys
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return

    N = int(input_data[0])
    M = int(input_data[1])

    # Check if Takahashi's submission passes all N test cases
    # He has passed M cases; if M == N, he gets an AC verdict.
    if M == N:
        print("Yes")
    else:
        print("No")


if __name__ == "__main__":
    main()
```

### B
```python
N, M = map(int, input().split())

if M == N:
    print("Yes")
else:
    print("No")
```

## PAIR 33  (task mbpp/788)

### A
```python
def new_tuple(items, key):
    result = tuple(items)
    return result + (key,)
```

### B
```python
def new_tuple(string_list, string):
    result = tuple(string_list) + (string,)
    return result
```

## PAIR 34  (task mbpp/405)

### A
```python
def check_tuplex(tup, x):
    return x in tup
```

### B
```python
def check_tuplex(t, elem):
    return elem in t
```

## PAIR 35  (task mbpp/805)

### A
```python
def max_sum_list(nums):
    """Return the list of numbers with the highest sum."""
    if not nums:
        return []

    max_val = nums[0]
    max_sum = 0

    for num in nums:
        current_sum = sum(num)
        if current_sum > max_sum:
            max_val = num
            max_sum = current_sum

    return max_val
```

### B
```python
def max_sum_list(nums):
    # Handle empty input case
    if not nums:
        return []

    # Sort lists by their sum in descending order
    sorted_lists = sorted(nums, key=lambda x: sum(x), reverse=True)
    return sorted_lists[0]
```

## PAIR 36  (task apps/4241)

### A
```python
import sys

def solve():
    lines = sys.stdin.read().split()
    if len(lines) < 2:
        return
    S = lines[0]
    T = lines[1]

    n = len(S)
    m = len(T)

    min_changes = float('inf')

    # Iterate over all possible starting positions in S where T can start
    for i in range(n - m + 1):
        # Count differences between S[i:] and T
        count = sum(a != b for a, b in zip(S[i:], T))
        min_changes = min(min_changes, count)

    print(min_changes)

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    S = input()
    T = input()
    
    n, m = len(S), len(T)
    
    min_changes = float('inf')
    
    # Try all starting positions in S where T could match
    for i in range(n - m + 1):
        # Compute Hamming distance for substring S[i : i+m] and T
        distance = 0
        for j in range(m):
            if S[i + j] != T[j]:
                distance += 1
        
        min_changes = min(min_changes, distance)
    
    print(min_changes)

if __name__ == "__main__":
    solve()
```

## PAIR 37  (task apps/4297)

### A
```python
import sys

def main():
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    n = int(input_data)
    
    # The minimum positive integer divisible by both 2 and N is N itself if N is even.
    # If N is odd, the smallest such integer is 2 * N.
    if n % 2 == 0:
        print(n)
    else:
        print(n * 2)

if __name__ == "__main__":
    main()
```

### B
```python
N = int(input())
print((N * 2) if N % 2 == 1 else N)
```

## PAIR 38  (task mbpp/61)

### A
```python
def count_Substrings(s: str) -> int:
    """Count substrings where the sum of digits equals the length of the substring."""
    count = 0
    n = len(s)
    
    # Iterate over all possible substrings using two pointers
    for length in range(1, n + 1):
        for i in range(n - length + 1):
            sub = s[i : i + length]
            # Convert substring to sum of its digits
            digit_sum = sum(int(c) for c in sub)
            
            if digit_sum == length:
                count += 1
    
    return count
```

### B
```python
def count_Substrings(s: str) -> int:
    n = len(s)
    count = 0
    for start in range(n):
        current_sum = 0
        for end in range(start, n):
            current_sum += int(s[end])
            if current_sum == (end - start + 1):
                count += 1
    return count
```

## PAIR 39  (task apps/4391)

### A
```python
import sys
from typing import List

def solve() -> None:
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    iterator = iter(input_data)
    
    try:
        n = int(next(iterator))
        k = int(next(iterator))
        
        a = []
        for _ in range(n):
            a.append(int(next(iterator)))
    except StopIteration:
        return

    # Precompute prefix sums
    # prefix[i] = sum(a[0]...a[i-1]) for i > 0
    # prefix[0] = 0
    prefix_sum = [0] * (n + 1)
    for i in range(n):
        prefix_sum[i + 1] = prefix_sum[i] + a[i]
    
    # The sum of a segment from index x to y (0-indexed) is prefix_sum[y+1] - prefix_sum[x]
    # Length of segment is y - x + 1
    # We want to maximize (prefix_sum[y+1] - prefix_sum[x]) / (y - x + 1)
    # where 0 <= x < y+1 <= n, and (y+1) - x >= k => y+1 >= x + k
    
    n_1 = len(a)
    
    # Initialize max_avg with the last element's average (k=n case)
    # But to be safe and general, we can check all valid segments.
    # Since n <= 5000, O(n^2) is acceptable (2.5e7 ops roughly in Python might be tight but acceptable given constraints and constant factor).
    # Let's implement O(n^2) to be safe against any specific edge cases or Python overhead.
    
    max_avg = float('-inf')
    
    # Iterate over all valid end positions (inclusive 1-based index for prefix sum, so 1 to n)
    # And start positions (inclusive 1-based, but mapped to 0-based logic below)
    # Segment defined by [start, end] inclusive (0-based)
    # Length = end - start + 1 >= k
    
    # We can iterate over length from k to n
    for length in range(k, n + 1):
        current_avg = float('-inf')
        
        # Iterate over all starting positions
        for i in range(n - length + 1):
            end_idx = i + length - 1
            # Sum of subarray a[i:end_idx+1]
            # = prefix_sum[end_idx+1] - prefix_sum[i]
            segment_sum = prefix_sum[end_idx + 1] - prefix_sum[i]
            avg = segment_sum / length
            if avg > current_avg:
                current_avg = avg
        
        if current_avg > max_avg:
            max_avg = current_avg
            
    print(f"{max_avg:.17f}")

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    iterator = iter(input_data)
    
    try:
        n = int(next(iterator))
        k = int(next(iterator))
        
        # Read the sequence of temperatures
        a = []
        for _ in range(n):
            a.append(int(next(iterator)))
    except StopIteration:
        return

    # The maximum possible sum for n elements is n * 5000 = 25,000,000
    # Double this for 64-bit integer precision.
    MAX_SUM = n * 5000 * 2
    
    # Compute prefix sums
    # P[i] = sum(a[0]...a[i-1]), so sum(a[x...y]) = P[y+1] - P[x]
    P = [0] * (n + 1)
    current_sum = 0
    for i in range(n):
        current_sum += a[i]
        P[i+1] = current_sum
    
    # Function to compute range sum [x, y] (1-based indices in problem, 0-based in list)
    # The problem uses 1-based indexing: segment from x to y means elements a[x-1]...a[y-1]
    # In our 0-based list 'a', this corresponds to indices i from x-1 to y-1.
    # Sum = P[y] - P[x-1] where x, y are 1-based.
    def get_segment_sum(x, y):
        return P[y] - P[x-1]
    
    # We need to maximize (sum[x...y] / y - x + 1)
    # Since the denominator increases with y-x, for a fixed length (y-x+1 = L),
    # the sum grows linearly with length, so the average is bounded by the max element.
    # However, with k constraint, we can iterate over all valid lengths L from k to n.
    # For a fixed length L, we want to find a window of size L with maximum average.
    # Since n <= 5000, an O(n^2) solution is acceptable.
    
    max_avg = 0.0
    
    # Iterate over all possible lengths L from k to n
    for length in range(k, n + 1):
        # We want to find max avg of any window of size 'length'
        # We can use a sliding window optimization, but for n=5000, simple O(n^2) is fine.
        # Let's implement O(n) sliding window within this loop to avoid TLE if n was larger.
        
        # Initialize first window of length 'length'
        window_sum = get_segment_sum(1, 1 + length - 1)
        current_avg = window_sum / length
        
        max_avg = max(max_avg, current_avg)
        
        # Slide the window
        for i in range(length, n):
            # Remove left element, add new element
            window_sum = window_sum - a[i - length] + a[i]
            current_avg = window_sum / length
            max_avg = max(max_avg, current_avg)
            
    # Output the result with sufficient precision
    print(f"{max_avg:.10f}")

if __name__ == "__main__":
    solve()
```

## PAIR 40  (task mbpp/226)

### A
```python
def odd_values_string(s: str) -> str:
    result = []
    for i, char in enumerate(s):
        if i % 2 == 0:
            result.append(char)
    return ''.join(result)
```

### B
```python
def odd_values_string(s):
    return ''.join(ch for i, ch in enumerate(s) if i % 2 == 0)
```

## PAIR 41  (task mbpp/459)

### A
```python
def remove_uppercase(s: str) -> str:
    result = []
    for char in s:
        if char.islower():
            result.append(char)
        elif char.isdigit():
            result.append(char)
        else:
            continue
    return "".join(result)
```

### B
```python
def remove_uppercase(s):
    result = []
    for char in s:
        if char.islower() or char == '_':
            result.append(char)
    return ''.join(result)
```

## PAIR 42  (task apps/4184)

### A
```python
def solve():
    # Read N
    import sys
    input = sys.stdin.read
    data = input().split()

    if not data:
        return

    iterator = iter(data)
    try:
        N = int(next(iterator))
        W = []
        for _ in range(N - 1):
            W.append(int(next(iterator)))
        # Note: the input format says W_1 ... W_{N-1} W_N
        # The loop above only reads N-1 values.
        # However, based on the sample input "3 \n 1 2 3", N=3, so W should have 3 elements.
        # But the constraints say: N, then N-1 values? 
        # Re-reading constraints: "W_1 W_2 ... W_{N-1} W_N"
        # That means there are N integers total after N.
        # My loop reads N-1 times. Need to read N-1 more? No, the slice range(N) will do it.
        # Actually, data will have N+1 elements: N, W1...WN-1, WN.
        # So after next(iterator) for N, we have N items remaining in data? 
        # No, data is a list of strings.
        # Let's reconstruct properly.

    except StopIteration:
        return

    # Re-approach reading:
    data_list = data
    if len(data_list) < N + 1:
        return  # Should not happen based on constraints

    N = int(data_list[0])
    weights = [int(x) for x in data_list[1:]]

    # Now weights has N elements
    # Find best T in range [1, N-1]
    best_diff = float('inf')

    # Compute prefix sums
    # S1(T) = sum(weights[1:T+1]) (1-indexed)
    # S2(T) = sum(weights[T+1:])
    # Equivalently: S1(T) = prefix_sum[T] (where prefix_sum[i] = sum(weights[:i]))
    # But let's be careful with 0-based indexing.
    # Weights are 0-indexed in Python: weight[0] to weight[N-1]
    # T is 1 to N-1 (inclusive).
    # Group 1: indices 0 to T-1 (weights[0]...weights[T-1])
    # Group 2: indices T to N-1 (weights[T]...weights[N-1])
    # Note: T is 1-based, so if T=1, Group 1 is empty? 
    # Problem says "weights with indices not greater than T". 
    # If T=1, indices <= 1 is just index 1. 
    # In 1-based: indices 1, 2, ..., T go to Group 1.
    # In 0-based: indices 0, 1, ..., T-1 go to Group 1.
    # If T=1, range is 0 to 0, so one element. 
    # Is it possible T=0? No, 1 <= T < N. Minimum T=1.
    # Group 1 has weights[0]...weights[T-1]. 
    # If T=1, Group 1 = [weight[0]], Group 2 = [weight[1]...].
    # Wait, sample: N=3, W=[1,2,3]. T=2.
    # Group 1: indices 1 to 2 (1-based) -> weights[0], weights[1] -> 1+2=3.
    # Group 2: index 3 (1-based) -> weights[2] -> 3.
    # This matches: T=2 means split after the second element.
    # So Group 1 range: [0, T-1], Group 2 range: [T, N-1].
    # T ranges from 1 to N-1.

    # Precompute prefix sums for efficiency
    prefix = [0] * N  # prefix[i] = sum(weights[:i])
    current_sum = 0
    for i in range(N):
        current_sum += weights[i]
        prefix[i] = current_sum

    # Iterate T from 1 to N-1
    for T in range(1, N):
        # Group 1 sum: prefix[T-1]
        s1 = prefix[T-1]
        # Group 2 sum: total_sum - s1
        total = prefix[N-1]
        s2 = total - s1
        diff = abs(s1 - s2)
        if diff < best_diff:
            best_diff = diff

    print(best_diff)


solve()
```

### B
```python
def solve():
    # Read N
    import sys
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    W = list(map(int, input_data[1:]))
    
    # Compute prefix sum
    prefix_sum = [0] * (N + 1)
    for i in range(N):
        prefix_sum[i+1] = prefix_sum[i] + W[i]
    
    # Iterate over all possible splits at T from 1 to N-1
    # S1 = sum(W[1..T]), S2 = sum(W[T+1..N])
    min_diff = float('inf')
    
    for T in range(1, N):
        S1 = prefix_sum[T]
        S2 = prefix_sum[N] - prefix_sum[T]
        diff = abs(S1 - S2)
        if diff < min_diff:
            min_diff = diff
            
    print(min_diff)

if __name__ == "__main__":
    solve()
```

## PAIR 43  (task apps/4180)

### A
```python
N = int(input())
if N % 1000 == 0:
    print(0)
else:
    print(1000 - (N % 1000))
```

### B
```python
def main():
    n = int(input())
    if n % 1000 == 0:
        print(0)
    else:
        print(1000 - (n % 1000))

if __name__ == "__main__":
    main()
```

## PAIR 44  (task mbpp/3)

### A
```python
def is_not_prime(n):
    if n < 2:
        return True
    if n == 2:
        return False
    if n % 2 == 0:
        return True
    
    i = 3
    while i * i <= n:
        if n % i == 0:
            return True
        i += 2
    return False
```

### B
```python
def is_not_prime(num):
    if num <= 1:
        return True
    if num == 2:
        return False
    if num % 2 == 0:
        return True
    i = 3
    while i * i <= num:
        if num % i == 0:
            return True
        i += 2
    return False
```

## PAIR 45  (task mbpp/79)

### A
```python
def word_len(word):
    return len(word) % 2
```

### B
```python
def word_len(word):
    """
    Returns whether the length of the word is odd or not.

    Args:
        word (str): The word to check the length of.

    Returns:
        bool: True if the word length is odd, False if even.
    """
    return len(word) % 2 == 1
```

## PAIR 46  (task apps/4253)

### A
```python
import sys

def main():
    r = int(sys.stdin.readline().strip())
    area = 3 * (r ** 2)
    print(area)

if __name__ == "__main__":
    main()
```

### B
```python
r = int(input())
a = r * r * 3
print(a)
```

## PAIR 47  (task mbpp/578)

### A
```python
def interleave_lists(l1, l2, l3):
    """Interleave three lists of the same length into a single flat list."""
    return [x for i in range(len(l1)) for x in [l1[i], l2[i], l3[i]]]
```

### B
```python
def interleave_lists(list1, list2, list3):
    result = []
    for l1, l2, l3 in zip(list1, list2, list3):
        result.append(l1)
        result.append(l2)
        result.append(l3)
    return result
```

## PAIR 48  (task apps/4321)

### A
```python
def solve():
    import sys
    input = sys.stdin.read
    data = input().split()
    n = int(data[0])
    k = int(data[1])

    for _ in range(k):
        if n % 10 != 0:
            n -= 1
        else:
            n //= 10

    print(n)

solve()
```

### B
```python
def solve():
    n, k = map(int, input().split())
    
    # Simulate the process
    for _ in range(k):
        if n % 10 != 0:
            n -= 1
        else:
            n //= 10
    
    print(n)

if __name__ == "__main__":
    solve()
```

## PAIR 49  (task mbpp/419)

### A
```python
def round_and_sum(numbers):
    total = sum(round(n) for n in numbers)
    return total * len(numbers)

assert round_and_sum([22.4, 4.0, -16.22, -9.10, 11.00, -12.22, 14.20, -5.20, 17.50]) == 243
```

### B
```python
def round_and_sum(numbers):
    rounded_numbers = [round(num) for num in numbers]
    total_sum = sum(rounded_numbers)
    length = len(rounded_numbers)
    return total_sum * length

assert round_and_sum([22.4, 4.0, -16.22, -9.10, 11.00, -12.22, 14.20, -5.20, 17.50])==243
```

