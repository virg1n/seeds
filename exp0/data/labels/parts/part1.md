## PAIR 50  (task mbpp/242)

### A
```python
def count_charac(s):
    """Count the total number of characters in a string."""
    return len(s)

assert count_charac("python programming") == 18
```

### B
```python
def count_charac(text: str) -> int:
    return len(text)

assert count_charac("python programming") == 18
```

## PAIR 51  (task apps/4177)

### A
```python
s = input()
print(''.join(["x"] * len(s)))
```

### B
```python
s = input()
x = 'x'
result = x * len(s)
print(result)
```

## PAIR 52  (task mbpp/66)

### A
```python
def pos_count(numbers):
    """Count the number of positive numbers in the list."""
    return sum(1 for x in numbers if x > 0)
```

### B
```python
def pos_count(numbers):
    """Count the number of positive integers in a list."""
    return sum(1 for x in numbers if x > 0)
```

## PAIR 53  (task mbpp/803)

### A
```python
import math

def is_perfect_square(num):
    """
    Check if the given number is a perfect square.
    
    A number is a perfect square if it is equal to the square of an integer.
    We use integer square root for precision and safety.
    """
    if num < 0:
        return False
    root = int(math.isqrt(num))
    return root * root == num
```

### B
```python
def is_perfect_square(n: int) -> bool:
    """
    Check if a given number n is a perfect square.
    
    Args:
        n (int): The number to check
        
    Returns:
        bool: True if n is a perfect square, False otherwise
    """
    if n < 0:
        return False
    root = int(n ** 0.5)
    return root * root == n
```

## PAIR 54  (task mbpp/116)

### A
```python
def tuple_to_int(t: tuple[int]) -> int:
    return int("".join(str(x) for x in t))
```

### B
```python
def tuple_to_int(t):
    if not t:
        return 0
    return int("".join(str(n) for n in t))
```

## PAIR 55  (task mbpp/255)

### A
```python
from itertools import combinations_with_replacement

def combinations_colors(colors, n):
    """
    Generates all combinations with repetition of colors.
    
    Args:
        colors (list): List of color names.
        n (int): Length of each combination tuple.
    
    Returns:
        list: List of tuples, each representing a combination.
    """
    return [tuple(combo) for combo in combinations_with_replacement(colors, n)]
```

### B
```python
from itertools import combinations_with_replacement

def combinations_colors(colors, n):
    return [tuple(c) for c in combinations_with_replacement(colors, n)]
```

## PAIR 56  (task mbpp/283)

### A
```python
def validate(n):
    if n < 0:
        return False
    s = str(n)
    frequency = {str(d): 0 for d in range(10)}
    for c in s:
        d = int(c)
        frequency[str(d)] += 1
    
    return all(frequency[str(d)] <= d for d in range(10))
```

### B
```python
def validate(n: int) -> bool:
    if n < 0:
        return False

    str_n = str(n)
    freq = {}
    for digit in str_n:
        d = int(digit)
        freq[d] = freq.get(d, 0) + 1

    for d, count in freq.items():
        if count > d:
            return False

    return True
```

## PAIR 57  (task apps/4473)

### A
```python
def solve():
    import sys
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        t = int(next(iterator))
    except StopIteration:
        return

    results = []
    for _ in range(t):
        a = int(next(iterator))
        b = int(next(iterator))
        k = int(next(iterator))

        # Pattern repeats every 2 jumps: +a, -b
        # If k is even: k/2 pairs -> each pair contributes a - b
        # If k is odd: (k-1)/2 pairs -> each pair contributes a - b, then + a
        # This can be simplified as:
        # If k % 2 == 0: result = (k // 2) * (a - b)
        # If k % 2 != 0: result = (k // 2) * (a - b) + a

        pairs = k // 2
        if k % 2 != 0:
            result = pairs * (a - b) + a
        else:
            result = pairs * (a - b)

        results.append(str(result))

    sys.stdout.write('\n'.join(results) + '\n')

solve()
```

### B
```python
def solve():
    import sys

    # Read all lines from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        t = int(next(iterator))
    except StopIteration:
        return

    results = []
    for _ in range(t):
        a = int(next(iterator))
        b = int(next(iterator))
        k = int(next(iterator))

        # Each pair of jumps (right then left) net distance is 0.
        # If k is even: k/2 pairs of (a, b) -> total 0.
        # If k is odd: (k-1)/2 pairs -> 0, plus one extra 'right' jump of 'a'.
        # So if k % 2 == 0: answer is 0
        # If k % 2 != 0: answer is a
        # However, wait! Let's re-verify the logic based on the problem description.
        # Sequence: +a, -b, +a, -b, ...
        # If k is odd, the last jump is +a. The sum is a.
        # If k is even, the last jump is -b, and since they cancel out in pairs, sum is 0.
        # But the example says:
        # k=3 (odd), output 8 (which is +a). Correct.
        # k=4 (even), output 198? WAIT. 
        # Example 2: 100 1 4 -> 100 - 1 + 100 - 1 = 198.
        # My logic "pairs cancel to 0" implies 100-1 + 100-1 = 196? 
        # No, the jump 2 is -1. The jump 4 is -1. 
        # Sequence: +100, -1, +100, -1.
        # Sum = 100 - 1 + 100 - 1 = 198.
        # My previous deduction "even means 0" was wrong because the jumps are not symmetric around 0.
        # Jump 1: +a
        # Jump 2: -b
        # Jump 3: +a
        # Jump 4: -b
        # ...
        # Jump k: if k is even -> -b
        # If k is odd -> +a
        # Therefore:
        # Sum = (k // 2) * (a - b) + (a if k % 2 != 0 else 0)
        # Let's re-evaluate Example 2: k=4, a=100, b=1.
        # Pairs: 2 pairs. (100 - 1) * 2 = 196. Plus no extra a. Total 196?
        # But example output says 198.
        # Wait, let's re-read the example note carefully.
        # "In the second query frog jumps 100 to the right, 1 to the left, 100 to the right and 1 to the left so the answer is 100 - 1 + 100 - 1 = 198."
        # Calculation: 100 - 1 = 99; 99 + 100 = 199; 199 - 1 = 198.
        # My formula (k//2)*(a-b) + (a if odd else 0) gives:
        # (4//2)*(100-1) + 0 = 2 * 99 = 198.
        # Ah, I see. I thought the pairs cancel to 0, but here the "left" jump (-b) is subtracted from the previous total.
        # Actually, let's look at the pattern again.
        # k=1: a
        # k=2: a - b
        # k=3: a - b + a = 2a - b
        # k=4: a - b + a - b = 2a - 2b = 2(a-b)
        # k=5: 2(a-b) + a
        # So the formula is correct:
        # if k % 2 == 1: answer = a + (k // 2) * (a - b)
        # else: answer = (k // 2) * (a - b)

        # Let's re-check Example 1: 5 2 3
        # k=3 (odd): 5 + (1)*(5-2) = 5 + 3 = 8. Correct.
        # Example 2: 100 1 4
        # k=4 (even): (2)*(100-1) = 2*99 = 198. Correct.
        # Example 3: 1 10 5
        # k=5 (odd): 1 + (2)*(1-10) = 1 + 2*(-9) = 1 - 18 = -17. Correct.
        # Example 4: 10^9 1 6
        # k=6 (even): (3)*(10^9 - 1) = 3 * (999999999) = 2999999997. Correct.
        # Example 5: 1 1 10^9
        # k=10^9 (even? No, even is always true for even numbers, 10^9 is even).
        # Wait, 1,000,000,000 is even? Yes.
        # So formula: (500000000) * (1-1) = 0. Correct.
        # Example 6: 1 1 999999999
        # k is odd (999999999). Formula: 1 + (499999999)*(0) = 1. Correct.

        # Implementation Plan:
        # Calculate k//2 * (a - b)
        # If k is odd, add a.
        # Print result.

        pairs = (k // 2) * (a - b)
        if k % 2 != 0:
            result = pairs + a
        else:
            result = pairs

        results.append(str(result))

    print('\n'.join(results))

if __name__ == "__main__":
    solve()
```

## PAIR 58  (task apps/4423)

### A
```python
def solve():
    # Read N
    n_str = input().strip()
    N = int(n_str)

    # Read N lines of restaurant data
    restaurants = []  # List of tuples (city, score, id)
    for i in range(N):
        s_p = input().strip().split()
        city = s_p[0]
        score = int(s_p[1])
        restaurants.append((city, score, i + 1))  # id = i+1

    # Sort restaurants:
    # 1. By city name ascending (lexicographically)
    # 2. By score descending
    restaurants.sort(key=lambda r: (r[0], -r[1]))

    # Print IDs in order
    for r in restaurants:
        print(r[2])

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def main():
    input = sys.stdin.read
    data = input().splitlines()
    idx = 0

    if not data:
        return

    N = int(data[idx].strip())
    idx += 1

    lines = []
    while idx < len(data):
        parts = data[idx].split()
        S = parts[0]
        P = int(parts[1])
        lines.append((S, P))
        idx += 1

    # Create list of (city, score, id) for restaurants
    # ids are 1-based, so we will use index + 1
    restaurants = []
    for s, p in lines:
        restaurants.append((s, p, len(restaurants) + 1))

    # Sort:
    # 1. cities in lexicographical order
    # 2. descending order of score
    restaurants.sort(key=lambda x: (-x[1], x[0]))

    # Sort by city first to get lexicographical order of city names
    # Then within each city, by score descending
    restaurants.sort(key=lambda x: (x[0], -x[1]))

    print(*(r[2] for r in restaurants))

if __name__ == '__main__':
    main()
```

## PAIR 59  (task mbpp/70)

### A
```python
def get_equal(tuples):
    if not tuples:
        return True
    length = len(tuples[0])
    return all(len(t) == length for t in tuples)
```

### B
```python
def get_equal(tuples):
    if not tuples:
        return True
    first_tuple = tuples[0]
    for t in tuples[1:]:
        if len(t) != len(first_tuple):
            return False
    return True
```

## PAIR 60  (task mbpp/751)

### A
```python
def check_min_heap(arr):
    n = len(arr)
    for i in range(n):
        # Heap property: parent <= child
        for i in range(n // 2):
            left = 2 * i + 1
            right = 2 * i + 2
            if left < n and arr[i] > arr[left]:
                return False
            if right < n and arr[i] > arr[right]:
                return False
    return True

# Example test
assert check_min_heap([1, 2, 3, 4, 5, 6]) == True
```

### B
```python
def check_min_heap(arr):
    """
    Checks if the given array represents a valid min-heap.

    A valid min-heap must satisfy:
    - Every parent node is less than or equal to its children.
    - For an array of size n, the index i has children at indices 2*i and 2*i+1.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """
    n = len(arr)
    if n == 0:
        return True
    if n == 1:
        return True

    for i in range(n // 2):
        left = 2 * i + 1
        right = 2 * i + 2

        if (left < n and right < n):
            if not (arr[i] <= arr[left] and arr[i] <= arr[right]):
                return False
        elif left < n:
            if not arr[i] <= arr[left]:
                return False
        elif right < n:
            if not arr[i] <= arr[right]:
                return False

    return True
```

## PAIR 61  (task mbpp/592)

### A
```python
def sum_Of_product(n):
    """
    Calculate the sum of the product of consecutive binomial coefficients.
    
    For example, with n=3:
    Coefficients are 1, 3, 3, 1 (for n=3).
    Consecutive pairs and their products:
    (1, 3) -> 3
    (3, 3) -> 9
    (3, 1) -> 3
    Sum = 3 + 9 + 3 = 15
    
    Args:
        n (int): A non-negative integer
        
    Returns:
        int: The sum of the product of consecutive binomial coefficients
        
    Raises:
        ValueError: If n is not a non-negative integer
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    
    # For n = 0, there are no consecutive pairs, sum is 0
    if n == 0:
        return 0
    
    binomial_coeffs = [1] * (n + 1)
    for i in range(1, n + 1):
        binomial_coeffs[i] = binomial_coeffs[i - 1] * (n - i + 1) // i
    
    total_sum = 0
    for i in range(len(binomial_coeffs) - 1):
        product = binomial_coeffs[i] * binomial_coeffs[i + 1]
        total_sum += product
        
    return total_sum
```

### B
```python
def sum_Of_product(n):
    # Calculate binomial coefficients using math.comb
    # Then sum the product of consecutive coefficients: binomial(n, 0)*binomial(n, 1) + binomial(n, 1)*binomial(n, 2) + ... + binomial(n, n-1)*binomial(n, n)
    from math import comb
    total = 0
    for k in range(n):
        term = comb(n, k) * comb(n, k + 1)
        total += term
    return total
```

## PAIR 62  (task mbpp/720)

### A
```python
def add_dict_to_tuple(tup, d):
    """Add a new key-value pair to the tuple by appending a new item (a dict)."""
    return tup + (d,)
```

### B
```python
def add_dict_to_tuple(tup, dict_to_add):
    return tuple(tup) + (dict_to_add,)
```

## PAIR 63  (task apps/4440)

### A
```python
import math

def solve():
    try:
        line = input().strip()
        if not line:
            return
        L = float(line)
    except ValueError:
        return

    # The maximum volume of a cuboid with a fixed sum of dimensions
    # is achieved when the three dimensions are as equal as possible.
    # Let the dimensions be a, b, c such that a + b + c = L.
    # Then V = a * b * c is maximized when a = b = c = L/3.
    # In that case, V_max = (L/3)^3 = L^3 / 27.
    # This formula holds even for non-integer L.

    volume = L ** 3 / 27
    print(f"{volume:.12f}")

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    line = sys.stdin.readline().strip()
    if not line:
        return
    L = float(line)
    
    # For a given sum of dimensions S, the volume S^3 is maximized when all dimensions are equal.
    # Here, the sum of the three dimensions is fixed at L.
    # Thus, maximum volume = (L / 3)^3.
    
    volume = (L / 3) ** 3
    print(f"{volume:.12f}")

if __name__ == "__main__":
    solve()
```

## PAIR 64  (task apps/4489)

### A
```python
def solve():
    # Read N and the N blue card strings
    n_str = input().strip()
    n = int(n_str)
    blue_cards = [input().strip() for _ in range(n)]

    # Read M and the M red card strings
    m_str = input().strip()
    m = int(m_str)
    red_cards = [input().strip() for _ in range(m)]

    # Compute frequencies of each string in blue and red cards
    from collections import Counter
    blue_freq = Counter(blue_cards)
    red_freq = Counter(red_cards)

    # Iterate over all distinct strings and find the maximum profit
    max_profit = 0
    for s in blue_freq:
        earnings = blue_freq[s]
        loss = red_freq.get(s, 0)
        profit = earnings - loss
        if profit > max_profit:
            max_profit = profit

    # Output the maximum profit
    print(max_profit)


if __name__ == "__main__":
    solve()
```

### B
```python
import sys
from collections import Counter

def solve():
    input = sys.stdin.read().split()
    if not input:
        return
    
    it = iter(input)
    try:
        N = int(next(it))
        s = [next(it) for _ in range(N)]
        M = int(next(it))
        t = [next(it) for _ in range(M)]
    except StopIteration:
        return

    # Count frequency of each string
    blue_counts = Counter(s)
    red_counts = Counter(t)
    
    # For each string S, the earnings = (count in blue) - (count in red)
    max_earnings = 0
    for s in blue_counts:
        max_earnings = max(max_earnings, blue_counts[s] - red_counts[s])
        
    print(max_earnings)

if __name__ == '__main__':
    solve()
```

## PAIR 65  (task mbpp/778)

### A
```python
def pack_consecutive_duplicates(lst):
    """
    Packs consecutive duplicates into sublists.
    Example: [0, 0, 1, 2, 3, 4, 4, 5, 6, 6, 6, 7, 8, 9, 4, 4]
    => [[0, 0], [1], [2], [3], [4, 4], [5], [6, 6, 6], [7], [8], [9], [4, 4]]
    """
    if not lst:
        return []
    result = []
    current = [lst[0]]
    for item in lst[1:]:
        if item == current[-1]:
            current.append(item)
        else:
            result.append(current)
            current = [item]
    result.append(current)
    return result
```

### B
```python
def pack_consecutive_duplicates(nums):
    if not nums:
        return []
    
    result = []
    current = [nums[0]]
    
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1]:
            current.append(nums[i])
        else:
            result.append(current)
            current = [nums[i]]
    
    result.append(current)
    return result
```

## PAIR 66  (task mbpp/94)

### A
```python
def index_minimum(tuples):
    """
    Given a list of tuples, returns the first value of the tuple with the smallest second value.
    
    Args:
        tuples (list[tuple]): List of tuples where each tuple has at least two elements.
        
    Returns:
        str: The first value of the tuple with the smallest second element.
        
    Raises:
        ValueError: If the input list is empty or any tuple has fewer than two elements.
    """
    if not tuples:
        raise ValueError("The list of tuples is empty.")
    
    if any(len(t) < 2 for t in tuples):
        raise ValueError("All tuples must have at least two elements.")
    
    # Find the index of the tuple with the minimum second value
    min_idx = min(range(len(tuples)), key=lambda i: tuples[i][1])
    
    return tuples[min_idx][0]
```

### B
```python
def index_minimum(items):
    if not items:
        raise ValueError("Input list cannot be empty")

    # Find the first tuple with the smallest second element
    min_second = items[0][1]
    result = items[0]

    for i in range(1, len(items)):
        if items[i][1] < min_second:
            min_second = items[i][1]
            result = items[i]

    return result[0]
```

## PAIR 67  (task apps/4454)

### A
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    iterator = iter(data)
    try:
        q = int(next(iterator))
    except StopIteration:
        return
    
    for _ in range(q):
        n = int(next(iterator))
        a = [int(next(iterator)) for _ in range(n)]
        
        # Sort the prices in ascending order
        a.sort()
        
        # We want minimum price p such that sum(p) >= sum(a)
        # Since p is equal for all n goods, sum = p * n
        # So we need p * n >= sum(a) => p >= ceil(sum(a) / n)
        
        total_sum = sum(a)
        # Ceiling division: (x + d - 1) // d
        ans = (total_sum + n - 1) // n
        
        print(ans)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    q = int(next(iterator))

    results = []
    for _ in range(q):
        n = int(next(iterator))
        a = []
        for _ in range(n):
            a.append(int(next(iterator)))

        # If all a[i] are equal, price can be a[0]
        if len(set(a)) == 1:
            results.append(str(min(a)))
        else:
            # We need min P such that P >= average(a)
            # To satisfy P >= average(a), the smallest integer satisfying this is ceil(avg)
            # ceil(avg) = floor(avg) if avg is integer, else floor(avg) + 1
            # Which is same as (sum + (1 if sum % 2 != 0 else 0)) // 1
            s = sum(a)
            # In Python 3: integer division // is floor
            # ceil(a / b) = (a + b - 1) // b for positive integers
            # Here b = 1, so ceil(s / 1) = s
            # Wait, we need P * n >= sum(a) => P >= sum(a) / n
            # So minimum integer P = ceil(sum(a) / n)
            # Which is (sum(a) + n - 1) // n
            # But we must use sum(a) here, not n * sum(a)
            # The condition is: price * n >= sum(a)  => price >= sum(a)/n
            # Minimum integer price = ceil(sum(a)/n) = (sum(a) + n - 1) // n
            min_price = (s + n - 1) // n
            results.append(str(min_price))

    sys.stdout.write('\n'.join(results) + '\n')

if __name__ == "__main__":
    solve()
```

## PAIR 68  (task apps/4216)

### A
```python
def solve():
    import sys
    input = sys.stdin.read
    data = input().strip()
    if not data:
        return
    n = int(data)

    # We need to find min k such that there exists A,B with A*B = n and
    # max(digits(A), digits(B)) == k.
    # This is equivalent to:
    #   min k such that for some factor A of n,
    #   k = max(len(str(A)), len(str(n // A)))
    # So we can iterate over all factors A of n, compute the value,
    # and take the minimum.

    # To be efficient, we only go up to sqrt(n).
    limit = int(n**0.5)
    best = n.bit_length()  # Upper bound: if A=1, B=n, max(digits) = len(str(n))

    # We'll collect all (len(A), len(B)) pairs and track the minimal max(digits).
    # However, we can stop early if the max digits of any factor >= best.
    # But best can be up to ~10 (since N <= 1e10 has at most 10 digits).
    # So we can just iterate all A up to sqrt(n) and compute max digits.

    # Note: N <= 10^10 -> at most 10 digits.
    # If best is 10, we don't need to go beyond 10 iterations.

    k_min = n.bit_length()

    for A in range(1, limit + 1):
        if n % A == 0:
            B = n // A
            dA = len(str(A))
            dB = len(str(B))
            dk = max(dA, dB)
            k_min = min(k_min, dk)

    print(k_min)


if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    import sys
    input = sys.stdin.read
    data = input().strip()
    if not data:
        return
    N = int(data)

    if N == 0:
        # Although constraints say positive integers, handle gracefully
        return 1  # No valid positive factor pair for 0

    # Upper bound on answer:
    # The smallest two-digit number is 10, so F(A,B) >= 2 unless one has 1 digit.
    # The largest two-digit number is 99, so F(A,B) <= 2.
    # If N has >= 2 digits, F(A,B) can be 2.
    # If N has exactly 1 digit, F(A,B) will be 1 unless we split into a 1 and >1 digit number? 
    # Actually, if N has 1 digit, say 5, we can have (5,1) -> F(5,1) = max(1, 1) = 1.
    # So answer is 1 for any single-digit N.

    # If N has 2 or more digits, the answer is at most 2.
    # Example: N=100 (3 digits). (10,10) -> F=2. But wait, sample says N=10000 -> answer 3.
    # Let's trace N=10000:
    # Factors can be 100 and 100 -> both have 3 digits -> F=3.
    # Can we get F=2? We need max(d(A), d(B)) = 2.
    # So either d(A) <= 2 and d(B) <= 2, and A*B = 10000.
    # If A has <= 2 digits, max(A) = 99. Then B = 10000/A must have <= 2 digits.
    # 10000/99 is roughly 101, which has 3 digits. So no.
    # Thus min F is 3.

    # General strategy:
    # Iterate over all possible numbers of digits for A, from min(2, len(str(N))) to len(str(N)).
    # For each number of digits, we iterate A from 1 up to N (or up to N with appropriate bounds).
    # But N can be up to 10^10, so O(sqrt(N)) is needed.

    # We iterate a from 1 to sqrt(N). If a divides N:
    #   Let b = N // a.
    #   Calculate dA = len(str(a)), dB = len(str(b)).
    #   candidate = max(dA, dB).
    #   Update minimum candidate.

    min_f = float('inf')

    for a in range(1, int(N**0.5) + 1):
        if N % a == 0:
            b = N // a
            da = len(str(a))
            db = len(str(b))
            f = max(da, db)
            if f < min_f:
                min_f = f

    print(min_f)


solve()
```

## PAIR 69  (task mbpp/797)

### A
```python
def sum_in_range(l, r):
    total = 0
    for num in range(l, r + 1):
        if num % 2 != 0:
            total += num
    return total
```

### B
```python
def sum_in_range(l, r):
    if l > r:
        return 0
    sum_odd = 0
    for n in range(l, r + 1):
        if n % 2 != 0:
            sum_odd += n
    return sum_odd
```

## PAIR 70  (task apps/4420)

### A
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    if not data:
        return
    
    iterator = iter(data)
    
    t = int(next(iterator))
    
    results = []
    
    for _ in range(t):
        x = int(next(iterator))
        y = int(next(iterator))
        n = int(next(iterator))
        
        # We want maximum k in [0, n] such that k % x == y
        # The smallest non-negative integer with remainder y is y itself.
        # The largest such k <= n is:
        # If y <= n, then k = y + (some multiples of x) that are <= n
        # But since y < x and we want remainder y, we have:
        # k = y + m*x <= n  =>  m*x <= n - y  =>  m <= (n - y) / x
        
        # Since we want maximum k, we compute the maximum m.
        # k_max = y + m_max * x
        # m_max = floor((n - y) / x)
        
        if n - y < 0:
            # According to constraints y <= n, so this branch shouldn't happen
            # but if it did, the problem guarantees existence.
            results.append("0")
        else:
            m_max = (n - y) // x
            k = y + m_max * x
            results.append(k)
    
    print('\n'.join(map(str, results)))

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    t = int(data[0])
    idx = 1
    results = []
    
    for _ in range(t):
        x = int(data[idx])
        y = int(data[idx+1])
        n = int(data[idx+2])
        idx += 3
        
        # k = y + q * x
        # We want maximum k <= n
        # So max q such that q*x + y <= n
        # q*x <= n - y
        # q <= (n - y) // x
        q = (n - y) // x
        k = q * x + y
        
        results.append(str(k))
    
    sys.stdout.write('\n'.join(results) + '\n')

if __name__ == '__main__':
    solve()
```

## PAIR 71  (task apps/4059)

### A
```python
import sys

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    # Parse N
    n = int(input_data[0])
    
    count = 0
    # For each possible value of B from 1 to n-1
    # A can be 1, 2, ..., B such that A * B + C = N
    # => C = N - A*B. For C to be positive, we need N - A*B >= 1 => A*B <= N - 1
    # Also C <= N (since C is positive)
    # Actually simpler: iterate B from 1 up to N-1
    # For a fixed B, A can range from 1 to floor((N-1)/B)
    # Then C = N - A*B is determined uniquely and guaranteed positive.
    
    # Optimization: Iterate B from 1 to N-1, but N can be up to 10^6, so O(N) is fine.
    for b in range(1, n):
        # Max A is (N - 1) // b
        max_a = (n - 1) // b
        # A ranges from 1 to max_a
        for a in range(1, max_a + 1):
            # C = N - a * b
            c = n - a * b
            # Since we iterate a up to (N-1)//b, we know a*b <= N-1, so c >= 1.
            count += 1
            
    print(count)

if __name__ == '__main__':
    solve()
```

### B
```python
def solve():
    # Read N from standard input
    try:
        line = input()
        if not line or not line.strip():
            return
        n = int(line.strip())
    except ValueError:
        return

    # Count tuples (A, B, C) of positive integers such that A * B + C = N
    # Since C = N - A * B and C >= 1, we need:
    # 1 <= A * B <= N - 1
    #
    # For each A from 1 up to N-1:
    #   Let max_B = (N - 1) // A
    #   Then B can range from 1 to max_B (inclusive)
    #   Count = max_B

    if n <= 2:
        # Smallest positive integer sum for A*B+C is 1*1+1 = 2
        # So if n=2 or 3, we check directly via the loop below
        pass

    count = 0
    for a in range(1, n):
        # Max B such that a*B <= n - 1
        max_b = (n - 1) // a
        count += max_b

    print(count)

if __name__ == "__main__":
    solve()
```

## PAIR 72  (task apps/4027)

### A
```python
def solve():
    # Read n from standard input
    line = input()
    if not line:
        return
    
    n = int(line)
    
    # The total sum of 1..n is n * (n + 1) // 2
    # We want to minimize |sum(A) - sum(B)|
    # Let S = total_sum = sum(A) + sum(B)
    # Then |sum(A) - sum(B)| = |(sum(A) - sum(B))|
    # And sum(A) - sum(B) = (sum(A) + sum(B)) - 2 * sum(B) = S - 2*sum(B)
    # So we want to find sum(B) such that |S - 2*sum(B)| is minimized,
    # which means 2*sum(B) should be as close to S as possible.
    # That is, sum(B) should be as close to S/2 as possible.
    
    S = n * (n + 1) // 2
    
    # If S is even, we can split perfectly: sum(B) = S // 2, difference = 0.
    # If S is odd, the closest sum(B) can be is (S-1)//2, giving difference 1.
    # However, we need to check feasibility.
    # Can we always form sum(B) = S // 2?
    # Since we can form any sum from 0 to S using 1..n? 
    # Not exactly any, but for consecutive integers starting from 1,
    # the subset sums can cover the range [0, S] continuously except possibly at odd/even jumps?
    # Actually, with 1..n, the maximum subset sum is S. The set of all subset sums
    # includes 0, and for n >= 1, it includes all integers up to S.
    # Proof: With {1}, we get {0,1}. With {1,2}, we get {0,1,2,3}. By induction,
    # adding i allows us to shift all previous sums by i, thus covering more.
    # So yes, we can always achieve sum(B) = floor(S/2) and ceil(S/2).
    
    if S % 2 == 0:
        print(0)
    else:
        print(1)

if __name__ == '__main__':
    solve()
```

### B
```python
import sys

def solve():
    # Read n from standard input
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    n = int(input_data)

    # Calculate sum of 1 to n
    # Using the formula: sum = n * (n + 1) // 2
    total_sum = n * (n + 1) // 2

    # We want to partition {1, 2, ..., n} into A and B such that |sum(A) - sum(B)| is minimized.
    # Let S_A = sum(A), S_B = sum(B).
    # Note that S_A + S_B = total_sum.
    # Then |S_A - (total_sum - S_A)| = |2*S_A - total_sum|.
    # To minimize this, we need S_A to be as close to total_sum / 2 as possible.
    # Ideally, S_A = floor(total_sum / 2).
    # The difference will be:
    # If total_sum is even: total_sum / 2 is integer -> difference is 0.
    # If total_sum is odd: floor(total_sum / 2) -> difference is (total_sum // 2).
    # In both cases, the minimum difference is total_sum % 2.

    ans = total_sum % 2

    # Print the result
    print(ans)

if __name__ == "__main__":
    solve()
```

## PAIR 73  (task apps/4141)

### A
```python
def main():
    import sys
    input = sys.stdin.read
    data = input().split()
    n = int(data[0])
    a = map(int, data[1:n+1])

    approved = True
    for x in a:
        if x % 2 == 0:
            if x % 3 != 0 and x % 5 != 0:
                approved = False
                break

    print("APPROVED" if approved else "DENIED")

if __name__ == "__main__":
    main()
```

### B
```python
def main():
    # Read the number of integers
    import sys
    input = sys.stdin.read
    data = input().split()

    n = int(data[0])
    a = []
    for i in range(n):
        a.append(int(data[i + 1]))

    approved = True
    for x in a:
        if x % 2 == 0:  # It's an even number
            if x % 3 != 0 and x % 5 != 0:
                approved = False
                break

    if approved:
        print("APPROVED")
    else:
        print("DENIED")

if __name__ == "__main__":
    main()
```

## PAIR 74  (task mbpp/162)

### A
```python
def sum_series(n):
    """
    Calculates the sum of (n - 2*i) for i from 0 up to n // 2.
    
    The series is: n + (n-2) + (n-4) + ... until the term becomes <= 0.
    This is equivalent to the sum of all even numbers from n down to 1,
    where each even number k contributes k if k is even, and 0 if k is odd
    (since the series stops before odd terms).
    
    For n = 6:
    Terms: 6, 4, 2
    Sum = 6 + 4 + 2 = 12
    """
    total = 0
    i = 0
    while n - 2 * i > 0:
        total += n - 2 * i
        i += 1
    return total
```

### B
```python
def sum_series(n):
    """
    Calculate the sum of the arithmetic progression (n-2*i) where i starts at 0
    and continues until n - 2*i < 0.
    """
    current_term = n
    total = 0
    while current_term >= 0:
        total += current_term
        current_term -= 2
    return total
```

## PAIR 75  (task mbpp/270)

### A
```python
def sum_even_and_even_index(nums):
    even_pos = [i for i, num in enumerate(nums) if i % 2 == 0]
    return sum(num for i, num in enumerate(nums) if i % 2 == 0 and num % 2 == 0)

assert sum_even_and_even_index([5, 6, 12, 1, 18, 8]) == 30
```

### B
```python
def sum_even_and_even_index(lst):
    """
    Sum of even numbers at even positions of a list.
    
    Positions are 0-based: index 0, 2, 4, ...
    Only numbers at these indices are summed if they are even.
    """
    return sum(x for i, x in enumerate(lst) if i % 2 == 0 and x % 2 == 0)
```

## PAIR 76  (task mbpp/433)

### A
```python
def check_greater(arr, x):
    return all(element < x for element in arr)
```

### B
```python
def check_greater(nums, value):
    for num in nums:
        if num >= value:
            return False
    return True
```

## PAIR 77  (task apps/4084)

### A
```python
import sys

def solve():
    # Read input from standard input
    line = sys.stdin.read().split()
    if not line:
        return
    n = int(line[0])
    a = int(line[1])
    b = int(line[2])

    # Initial count of blue balls after the first full cycle
    # Each cycle: place 'a' blue balls, then 'b' red balls
    # Total balls per cycle: a + b
    # Blue balls per cycle: a

    cycle_length = a + b

    full_cycles = n // cycle_length
    remainder = n % cycle_length

    # Blue balls from full cycles
    blue_count = full_cycles * a

    # Blue balls from the partial cycle (only if there's a remainder > 0)
    if remainder > 0:
        blue_count += min(a, remainder)

    print(blue_count)

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
    n = int(data[0])
    a = int(data[1])
    b = int(data[2])

    total_per_two = a + b

    # Calculate how many full "AB" cycles fit into N balls
    full_cycles = n // (a + b)
    remainder = n % (a + b)

    blue_in_full_cycles = full_cycles * a
    blue_in_remainder = 0

    if remainder > 0:
        # The first 'remainder' balls correspond to the sequence: A blue, B red
        if remainder <= a:
            blue_in_remainder = remainder
        else:
            blue_in_remainder = a

    print(blue_in_full_cycles + blue_in_remainder)

if __name__ == "__main__":
    solve()
```

## PAIR 78  (task mbpp/17)

### A
```python
def square_perimeter(side_length: float) -> float:
    return 4 * side_length
```

### B
```python
def square_perimeter(side_length: int) -> int:
    return 4 * side_length

assert square_perimeter(10) == 40
```

## PAIR 79  (task mbpp/7)

### A
```python
def find_char_long(s: str) -> set[str]:
    """
    Find all words in a string that are at least 4 characters long.
    
    Words are assumed to be contiguous sequences of alphabetic characters.
    """
    import re
    
    # Find all sequences of alphanumeric characters that are at least 4 characters
    match = re.findall(r'[a-zA-Z0-9]+', s)
    return set(word for word in match if len(word) >= 4)
```

### B
```python
import re

def find_char_long(s: str) -> set:
    words = re.findall(r'\b\w+\b', s)
    return set(word for word in words if len(word) >= 4)
```

## PAIR 80  (task apps/4422)

### A
```python
import sys

def main():
    lines = sys.stdin.read().split()
    N = int(lines[0])
    K = int(lines[1])
    S = lines[2]
    S = [char.lower() if K == i + 1 else char for i, char in enumerate(S)]
    S = "".join(S)
    print(S)

if __name__ == "__main__":
    main()
```

### B
```python
N, K = input().split()
K = int(K)
S = input()

S = S[0 : K - 1] + S[K - 1].lower() + S[K:]
print(S)
```

## PAIR 81  (task mbpp/312)

### A
```python
import math

def volume_cone(r, h):
    """
    Calculate the volume of a cone.
    
    Parameters:
    r (float): Radius of the cone
    h (float): Height of the cone
    
    Returns:
    float: Volume of the cone
    
    Formula: V = (1/3) * pi * r^2 * h
    """
    return (1/3) * math.pi * r**2 * h
```

### B
```python
import math

def volume_cone(base_radius, height):
    """
    Calculate the volume of a cone.
    
    Parameters:
    base_radius (float): The radius of the base
    height (float): The height of the cone
    
    Returns:
    float: The volume of the cone
    """
    return (1/3) * math.pi * (base_radius ** 2) * height
```

## PAIR 82  (task mbpp/161)

### A
```python
def remove_elements(lst, elements):
    return [x for x in lst if not any(e == x for e in elements)]
```

### B
```python
def remove_elements(nums, targets):
    return [x for x in nums if x not in targets]
```

## PAIR 83  (task apps/4502)

### A
```python
import sys

def solve():
    # Read all input from standard input
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    n = int(next(iterator))
    a = []
    for _ in range(n):
        a.append(int(next(iterator)))

    b = []
    # Process each operation
    for x in a:
        b.append(x)
        # Reverse the list in place
        b.reverse()

    # Print the resulting sequence as space-separated integers
    print(*b)

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    n = int(input_data[0])
    a = list(map(int, input_data[1:n+1]))

    b = []
    for x in a:
        b.append(x)
        b.reverse()

    print(*(b))

if __name__ == "__main__":
    solve()
```

## PAIR 84  (task apps/4403)

### A
```python
def solve():
    s = input()
    ans = 0
    for char in s:
        if char == "+":
            ans += 1
        else:
            ans -= 1
    print(ans)

solve()
```

### B
```python
s = input()
ans = 0
for char in s:
    if char == '+':
        ans += 1
    else:
        ans -= 1
print(ans)
```

## PAIR 85  (task apps/4323)

### A
```python
import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        n = int(next(iterator))
        m = int(next(iterator))
    except StopIteration:
        return

    # Store initial sizes and compression info (compression size is a_i)
    # a_i and b_i are already read: initial = a_i, compressed = b_i
    # We need to select a subset to compress such that sum(compressed_i) <= m
    # We want to minimize the number of songs compressed.
    # This is equivalent to: find the smallest k such that there exists a subset
    # of k songs whose compressed sizes sum to at least m - original_total?
    # Actually, let's rephrase:
    # Total size required if no compression = sum(a_i)
    # Total size required if we don't compress a specific subset = sum of a_i for those not compressed
    # We want: sum of sizes (original for uncompressed + compressed for compressed) <= m
    # Sum = (sum of a_i) - (sum of (a_i - b_i) for compressed) <= m
    # So: sum of (a_i - b_i) for compressed >= (sum of a_i) - m
    # Let diff[i] = a_i - b_i
    # We need to find min k such that the sum of k smallest diffs is >= diff_target
    # where diff_target = sum(a_i) - m. If diff_target <= 0, 0 compression needed.

    diffs = []
    total_original = 0
    for _ in range(n):
        a = int(next(iterator))
        b = int(next(iterator))
        diffs.append(a - b)  # savings if compressed
        total_original += a

    target = total_original - m

    if target <= 0:
        print(0)
        return

    # Greedy approach: always compress songs with largest savings (largest diff)
    # This will minimize the number of songs.
    diffs.sort(reverse=True)

    compress_count = 0
    savings_accumulated = 0

    for d in diffs:
        savings_accumulated += d
        compress_count += 1
        if savings_accumulated >= target:
            break

    if savings_accumulated >= target:
        print(compress_count)
    else:
        print("-1")

if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    # Read n and m
    input = sys.stdin.read
    data = input().split()
    iterator = iter(data)
    
    try:
        n = int(next(iterator))
        m = int(next(iterator))
    except StopIteration:
        return

    # Read a_i and b_i for each song
    songs = []
    for _ in range(n):
        a = int(next(iterator))
        b = int(next(iterator))
        songs.append((a, b))
    
    # Greedy strategy: always compress the song that gives the largest reduction
    # This maximizes the space saved per compression step.
    
    reductions = []
    for a, b in songs:
        reductions.append(a - b)
    
    if sum(reductions) > m - sum(b):
        # Even if we compress all songs, total space needed <= m
        print("-1")
        return
    
    # Sort reductions in descending order
    reductions.sort(reverse=True)
    
    compressed_count = 0
    current_space_needed = m  # Initially assume we keep all songs
    for reduction in reductions:
        # Compress this song: we save 'reduction' space, but now we need (sum of initial sizes) - (sum of initial sizes - reduction) = reduction space
        # Wait, let's rethink.
        # Initial space needed: sum(a_i)
        # After compressing this one: sum(a_i) - reduction
        # We want: sum(a_i) - total_reduction >= m
        
        # Current space taken by all original songs: total_original = sum(a_i)
        # If we reduce total_reduction by compressing k songs with total_reduction_k,
        # then total_original - total_reduction_k >= m
        
        # To minimize compressed_count, we greedily pick the song with largest reduction.
        # This is because each compression reduces the required space by 'reduction',
        # so larger reduction means closer to meeting m.
        
        # Let's verify logic:
        # total_original = S
        # After k compressions with reductions r1, r2, ..., rk
        # total_original - sum(r_i) >= m
        # sum(r_i) <= S - m
        
        # To minimize k, we should use the largest r_i first.
        
        # Optimization: instead of tracking sums which might be large, we can just
        # check if remaining original sizes - m can be covered by top K reductions.
        
        if total_original < m:
            print("-1")
            return
        
        # Count how many of the largest reductions can cover (total_original - m)
        remaining_needed = total_original - m
        compressed_count = 0
        
        for i in range(n - 1, -1, -1):
            if reductions[i] >= remaining_needed:
                compressed_count += 1
                remaining_needed = 0
                break
        
        if remaining_needed == 0:
            break
            
    print(compressed_count)

# Actually, the above logic has a flaw in my thought process.
# Correct approach:
# 1. Calculate sum of all a_i.
# 2. If sum(a_i) <= m initially, print 0.
# 3. If even after compressing all songs (total reductions > 0) the remaining sum <= m, but we need to check if we can cover the gap.
#    Actually simpler: 
#    Total reduction needed = sum(a_i) - m
#    If sum(a_i) <= m, output 0.
#    Else, sort reductions descending.
#    Accumulate reductions. If accumulated reduction >= total_reduction_needed, output count.
#    Wait, "accumulated reduction" means sum of (a - b). 
#    But we must also respect that for a specific song i, we can only compress it once.
#    Since each song is distinct, and reducing song i saves (a_i - b_i), 
#    the total space freed is indeed sum of reductions of chosen songs.
#    So we just need sum of (a_i - b_i) for chosen songs >= sum(a_i) - m.
#    And we want to minimize the count.
#    This is exactly: sort reductions descending, sum until sum >= total_needed.

# But wait, example 1:
# 4 21
# 10 8 -> diff 2
# 7 4 -> diff 3
# 3 1 -> diff 2
# 5 4 -> diff 1
# Total needed: (10+7+3+5) - 21 = 25 - 21 = 4
# Sort diffs: 3, 2, 2, 1
# Take 3: 3 < 4
# Take 2: 3+2=5 >= 4. Count=2. Correct.

# Example 2:
# 4 16
# 10 8 -> 2
# 7 4 -> 3
# 3 1 -> 2
# 5 4 -> 1
# Total needed: (10+7+3+5) - 16 = 25 - 16 = 9
# Sort: 3, 2, 2, 1
# Take 3, 2: 3+2=5 < 9
# Take 2: 5+2=7 < 9
# Take 1: 7+1=8 < 9
# Sum of all diffs = 8 < 9. Impossible -> -1. Correct.

# So algorithm:
# 1. Calculate total_original = sum(a_i)
# 2. If total_original <= m: print 0
# 3. Compute diffs = a_i - b_i
# 4. Sort diffs descending
# 5. accumulated = 0
# 6. For d in diffs:
#      accumulated += d
#      if accumulated >= total_original - m:
#          print(len(diffs_so_far))
#          return
# 7. If not reached, print -1

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    n = int(next(iterator))
    m = int(next(iterator))
    
    a_list = []
    diffs = []
    
    total_original = 0
    for _ in range(n):
        a_i = int(next(iterator))
        b_i = int(next(iterator))
        a_list.append(a_i)
        diffs.append(a_i - b_i)
        total_original += a_i
    
    if total_original <= m:
        print(0)
        return
    
    total_reduction_needed = total_original - m
    
    diffs.sort(reverse=True)
    
    needed = 0
    for d in diffs:
        needed += d
        if needed >= total_reduction_needed:
            print(len(diffs) - i - 1) # wait, need to track count properly
            return
    
    # Re-scan to get correct count or just print -1
    # Actually the loop above is confusing because of the index variable scope.
    # Let's rewrite cleanly.
    pass

# Rewrite clean version
def solve_clean():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    n = int(next(iterator))
    m = int(next(iterator))
    
    a_list = []
    diffs = []
    total_original = 0
    
    for _ in range(n):
        a_i = int(next(iterator))
        b_i = int(next(iterator))
        a_list.append(a_i)
        diffs.append(a_i - b_i)
        total_original += a_i
        
    if total_original <= m:
        print(0)
        return
    
    total_reduction_needed = total_original - m
    
    diffs.sort(reverse=True)
    
    count = 0
    current_reduction = 0
    for d in diffs:
        count += 1
        current_reduction += d
        if current_reduction >= total_reduction_needed:
            print(count)
            return
            
    print("-1")

# Main block
if __name__ == "__main__":
    solve_clean()
```

## PAIR 86  (task apps/4183)

### A
```python
import sys

def solve():
    # Read all integers from input
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    N = int(input_data[0])
    T = [int(x) for i, x in enumerate(input_data[1:1 + N])]

    # To return to upward position, total elapsed time must be a multiple of every T_i.
    # LCM of a set of numbers can be very large, so we use Python's built-in
    # functools.reduce to compute it safely with large integers.
    from functools import reduce
    import math

    def lcm(a, b):
        return a * b // math.gcd(a, b)

    return reduce(lcm, T)

if __name__ == "__main__":
    print(solve())
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
    T = []
    for i in range(1, N + 1):
        T.append(int(data[i]))

    # The i-th clock points upward every Ti seconds.
    # The hand points upward again at LCM(T1, T2, ..., TN) seconds.
    # We need to compute the least common multiple of N numbers.
    import math

    lcm = 1
    for t in T:
        # math.lcm exists in Python 3.9+, but to be safe for older versions:
        lcm = (lcm * t) // math.gcd(lcm, t)

    print(lcm)

if __name__ == "__main__":
    solve()
```

## PAIR 87  (task apps/4230)

### A
```python
def solve():
    import sys

    # Read all input from stdin
    input_data = sys.stdin.read().split()

    if not input_data:
        return

    iterator = iter(input_data)
    
    try:
        X = int(next(iterator))
        N = int(next(iterator))
    except StopIteration:
        return

    p_set = set()
    for _ in range(N):
        try:
            val = int(next(iterator))
            p_set.add(val)
        except StopIteration:
            break

    # Find the integers not in p_set that are nearest to X
    # We want the integer with minimum |val - X|
    # If multiple have same distance, choose the smallest val
    candidates = []
    for v in range(-5000, 5001):  # Sufficiently wide range covering X=100
        if v not in p_set:
            candidates.append(v)

    # candidates are naturally sorted ascending because we iterate from -5000 to 5000
    best = None
    min_diff = None

    for v in candidates:
        diff = abs(v - X)
        if min_diff is None or diff < min_diff:
            min_diff = diff
            best = v
        elif diff == min_diff:
            # If distances are equal, choose the smaller integer
            if v < best:
                best = v

    print(best)


if __name__ == "__main__":
    solve()
```

### B
```python
import sys

def solve():
    input = sys.stdin.read().split()
    if not input:
        return
    
    iterator = iter(input)
    
    try:
        X = int(next(iterator))
        N = int(next(iterator))
    except StopIteration:
        return
    
    p = set()
    for _ in range(N):
        p.add(int(next(iterator)))
    
    candidates = []
    for i in range(-101, 102):  # range is small enough because X <= 100
        diff = abs(i - X)
        if i not in p:
            candidates.append((diff, i))
    
    # Find minimum diff
    best_diff = float('inf')
    best_i = 0
    
    # If no candidates are available (X is 0 or -100 or something not in candidate range), handle gracefully
    if not candidates:
        print(0)
        return

    # Sort candidates by diff, then by value ascending
    candidates.sort(key=lambda x: (x[0], x[1]))
    
    _, best_i = candidates[0]
    
    print(best_i)

if __name__ == '__main__':
    solve()
```

## PAIR 88  (task mbpp/271)

### A
```python
def even_Power_Sum(n):
    """
    Calculate the sum of the first n even natural numbers raised to the fifth power.
    """
    total = 0
    for k in range(1, n + 1):
        total += (2 * k) ** 5
    return total
```

### B
```python
def even_Power_Sum(n):
    """
    Returns the sum of the first n even natural numbers raised to the fifth power.
    
    First n even natural numbers are: 2, 4, 6, 8, ..., 2*n
    Each number is then raised to the fifth power, and the results are summed.
    
    Parameters:
    n (int): Number of even natural numbers to sum
    
    Returns:
    int: Sum of the fifth powers of the first n even natural numbers
    
    Raises:
    ValueError: If n is not a non-negative integer
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    
    total = 0
    for i in range(2, 2 * n + 1, 2):
        total += i ** 5
    return total

# Test
assert even_Power_Sum(2) == 1056
```

## PAIR 89  (task apps/4384)

### A
```python
N = int(input())
if N >= 1000:
    print("ABD")
else:
    print("ABC")
```

### B
```python
n = int(input())
print("ABC" if n <= 999 else "ABD")
```

## PAIR 90  (task mbpp/801)

### A
```python
def test_three_equal(x, y, z):
    # Count how many of x, y, and z are the same
    count = 0
    if x == y == z:
        count = 3
    elif x == y or x == z or y == z:
        count = 2
    # If all three are different, count = 0
    return count

assert test_three_equal(1, 1, 1) == 3
assert test_three_equal(1, 2, 3) == 0
assert test_three_equal(1, 1, 2) == 2
assert test_three_equal(1, 2, 1) == 2
assert test_three_equal(1, 1, 1) == 3
```

### B
```python
def test_three_equal(a, b, c):
    if a == b == c:
        return 3
    if a == b or a == c or b == c:
        return 2
    if a != b and b != c and a != c:
        return 0
    return 1
```

## PAIR 91  (task apps/4214)

### A
```python
import sys
import math
from itertools import permutations

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        n_str = next(iterator)
        N = int(n_str)
    except StopIteration:
        return

    towns = []
    for _ in range(N):
        x = int(next(iterator))
        y = int(next(iterator))
        towns.append((x, y))

    total_path_length = 0.0

    # N <= 8, so we can iterate over all permutations
    # A permutation represents an ordering of towns
    for p in permutations(range(N)):
        length = 0.0
        for i in range(N - 1):
            xi, yi = towns[p[i]]
            xj, yj = towns[p[i+1]]
            dx = xi - xj
            dy = yi - yj
            dist = math.hypot(dx, dy)
            length += dist
        total_path_length += length

    average_length = total_path_length / math.factorial(N)
    print(f"{average_length:.10f}")

if __name__ == "__main__":
    solve()
```

### B
```python
import sys
import math
from itertools import permutations

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        N = int(next(iterator))
    except StopIteration:
        return

    X = []
    Y = []
    for _ in range(N):
        x = int(next(iterator))
        y = int(next(iterator))
        X.append(x)
        Y.append(y)

    # Generate all paths (permutations of towns indices)
    path_lengths = []
    for p in permutations(range(N)):
        length = 0.0
        current_x = X[p[0]]
        current_y = Y[p[0]]
        
        for i in range(1, N):
            next_x = X[p[i]]
            next_y = Y[p[i]]
            dx = current_x - next_x
            dy = current_y - next_y
            length += math.sqrt(dx*dx + dy*dy)
            current_x = next_x
            current_y = next_y
        
        path_lengths.append(length)

    avg = sum(path_lengths) / len(path_lengths)
    print(f"{avg:.10f}")

if __name__ == "__main__":
    solve()
```

## PAIR 92  (task apps/4332)

### A
```python
import sys

def solve():
    N_str = sys.stdin.readline().strip()
    N = int(N_str)
    
    n_str = str(N)
    s = sum(int(c) for c in n_str)
    
    if N % s == 0:
        print("Yes")
    else:
        print("No")

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    import sys

    def digit_sum(n: int) -> int:
        s = 0
        while n > 0:
            s += n % 10
            n //= 10
        return s

    n_str = sys.stdin.read().strip()
    if not n_str:
        return
    N = int(n_str)

    if N == 0:
        print("No")
        return

    s_N = digit_sum(N)

    # Check if S(N) divides N
    if s_N == 0:
        # N > 0, so digit sum > 0, not possible
        print("No")
    else:
        if N % s_N == 0:
            print("Yes")
        else:
            print("No")

if __name__ == "__main__":
    solve()
```

## PAIR 93  (task mbpp/282)

### A
```python
def sub_list(a, b):
    if len(a) != len(b):
        raise ValueError("Lists must have equal length")
    return [x - y for x, y in zip(a, b)]
```

### B
```python
def sub_list(lst1, lst2):
    """Subtract two lists element-wise."""
    return [a - b for a, b in zip(lst1, lst2)]
```

## PAIR 94  (task mbpp/760)

### A
```python
def unique_Element(nums):
    # If the list is empty, it technically contains zero distinct elements,
    # so it's not "exactly one". We'll handle non-empty case first.
    if len(nums) == 1:
        return True
    
    # Check if there's more than one distinct element
    distinct_elements = len(set(nums))
    return distinct_elements == 1
```

### B
```python
def unique_Element(lst):
    if len(set(lst)) == 1:
        return True
    return False
```

## PAIR 95  (task apps/4319)

### A
```python
def solve():
    # Read n
    input_data = input().split()
    if not input_data:
        return
    n = int(input_data[0])
    
    # Read the sequence of numbers
    a = list(map(int, input().split()))
    
    stairs = []
    current_stairway_length = 0
    
    for val in a:
        if val == 1:
            if current_stairway_length > 0:
                # If the previous number was also 1, it means a new stairway starts
                stairs.append(current_stairway_length)
                current_stairway_length = 0
            current_stairway_length = 1
        else:
            # Accumulate current stairway length
            current_stairway_length += 1
    
    # Don't forget the last stairway
    stairs.append(current_stairway_length)
    
    print(len(stairs))
    print(*(stairs))

if __name__ == "__main__":
    solve()
```

### B
```python
def solve():
    # Read all tokens from input (handles newlines/spaces automatically)
    from sys import stdin
    input_data = stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    try:
        n = int(next(iterator))
    except StopIteration:
        return

    # Read the sequence of numbers pronounced
    a = []
    for _ in range(n):
        a.append(int(next(iterator)))

    # Algorithm:
    # Iterate through the sequence and count consecutive stairways.
    # A stairway ends when the current number is 1, meaning a new stairway starts.
    # The last number before a 1 completes the previous stairway and is also part of the new one.

    stairways = []
    current_stairway = []

    for num in a:
        if num == 1:
            # Found start of a new stairway
            if current_stairway:
                stairways.append(len(current_stairway))
            current_stairway = [num]
        else:
            # Continuation of current stairway
            current_stairway.append(num)

    # Append the last stairway if any
    if current_stairway:
        stairways.append(len(current_stairway))

    # Output results
    print(len(stairways))
    print(*(stairways))

if __name__ == "__main__":
    solve()
```

## PAIR 96  (task apps/4272)

### A
```python
def main():
    # Read N
    n_str = input()
    n = int(n_str)
    
    # Read S
    s = input()
    
    count = 0
    i = 0
    while i < len(s) - 2:
        if s[i:i+3] == "ABC":
            count += 1
        i += 1
    
    print(count)

if __name__ == "__main__":
    main()
```

### B
```python
def solve():
    n_str = input().strip()
    s = input().strip()

    if len(s) < 3:
        print(0)
        return

    cnt = 0
    for i in range(len(s) - 2):
        if s[i:i+3] == "ABC":
            cnt += 1

    print(cnt)


if __name__ == "__main__":
    solve()
```

## PAIR 97  (task mbpp/111)

### A
```python
def common_in_nested_lists(items):
    """
    Find the common elements in nested lists.
    
    Parameters:
    items (list): A list of lists containing integers
    
    Returns:
    set: A set containing the common elements found in all sublists
    """
    # Find the intersection of all sublists
    result = items[0]
    for sublist in items[1:]:
        result = list(set(result) & set(sublist))
    
    return set(result)
```

### B
```python
def common_in_nested_lists(nested_lists):
    """Find the intersection of elements in all nested lists.
    
    Args:
        nested_lists: List of lists (each inner list may contain any type)
        
    Returns:
        Set of common elements across all nested lists
        
    Examples:
        >>> set(common_in_nested_lists([[12, 18, 23, 25, 45], [7, 12, 18, 24, 28], [1, 5, 8, 12, 15, 16, 18]]))
        {18, 12}
    """
    result = set()
    for item in nested_lists[0]:
        if all(item in inner_list for inner_list in nested_lists):
            result.add(item)
    return result
```

## PAIR 98  (task mbpp/281)

### A
```python
def all_unique(lst):
    """Check if all elements in the list are unique."""
    return len(lst) == len(set(lst))
```

### B
```python
def all_unique(items):
    """Check if all elements in the list are unique."""
    return len(items) == len(set(items))
```

## PAIR 99  (task mbpp/606)

### A
```python
def radian_degree(degrees):
    return degrees * (3.141592653589793 / 180)
```

### B
```python
import math

def radian_degree(angle):
    """Convert degrees to radians."""
    return angle * math.pi / 180.0

# Test assertion
assert radian_degree(90) == 1.5707963267948966
```

