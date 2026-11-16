# CASE 2: FALSE_DIFFERENT  (pair 56, task apps/4134, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both meet-in-the-middle: enumerate half paths storing xor counts per cell, then match from the other end (recursion vs bitmask enumeration).
d_phi=0.958  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|linear # linear|memo|nest1 # dict   slope b=0.99376910451013 (lines 0.99376910451013, time 0.9189412369963982)
Fingerprint B: O(exp)|none # none|-|nest2 # counter   slope b=4.4776224123837 (lines 4.4776224123837, time None)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
There is a rectangular grid of size $n \times m$. Each cell has a number written on it; the number on the cell ($i, j$) is $a_{i, j}$. Your task is to calculate the number of paths from the upper-left cell ($1, 1$) to the bottom-right cell ($n, m$) meeting the following constraints:

  You can move to the right or to the bottom only. Formally, from the cell ($i, j$) you may move to the cell ($i, j + 1$) or to the cell ($i + 1, j$). The target cell can't be outside of the grid.  The xor of all the numbers on the path from the cell ($1, 1$) to the cell ($n, m$) must be equal to $k$ (xor operation is the bitwise exclusive OR, it is represented as '^' in Java or C++ and "xor" in Pascal). 

Find the number of such paths in the given grid.


-----Input-----

The first line of the input contains three integers $n$, $m$ and $k$ ($1 \le n, m \le 20$, $0 \le k \le 10^{18}$) — the height and the width of the grid, and the number $k$.

The next $n$ lines contain $m$ integers each, the $j$-th element in the $i$-th line is $a_{i, j}$ ($0 \le a_{i, j} \le 10^{18}$).


-----Output-----

Print one integer — the number of paths from ($1, 1$) to ($n, m$) with xor sum equal to $k$.


-----Examples-----
Input
3 3 11
2 1 5
7 10 0
12 6 4

Output
3

Input
3 4 2
1 3 3 3
0 3 3 2
3 0 1 1

Output
5

Input
3 4 1000000000000000000
1 3 3 3
0 3 3 2
3 0 1 1

Output
0



-----Note-----

All the paths from the first example:   $(1, 1) \rightarrow (2, 1) \rightarrow (3, 1) \rightarrow (3, 2) \rightarrow (3, 3)$;  $(1, 1) \rightarrow (2, 1) \rightarrow (2, 2) \rightarrow (2, 3) \rightarrow (3, 3)$;  $(1, 1) \rightarrow (1, 2) \rightarrow (2, 2) \rightarrow (3, 2) \rightarrow (3, 3)$. 

All the paths from the second example:   $(1, 1) \rightarrow (2, 1) \rightarrow (3, 1) \rightarrow (3, 2) \rightarrow (3, 

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (39 chars):
10 1 1023
1
2
4
8
16
32
64
128
256
512

--- size 512 (14858 chars):
5120 1 1023
8
2
2
64
512
256
128
64
1
32
32
512
64
8
4
32
512
32
2
1
32
64
16
32
32
512
32
256
2
512
128
2
8
32
1
128
2
512
16
16
1
256
256
1
16
512
256
2
64
16
32
2
128
2
2
16
8
1
256
1
256
16
16
128
128
1
16
1
256
128
64
2
128
1
256
4
128
2
4
4
64
8
8
128
32
256
32
512
4
2
4
512
64
2
256
512
16
64
--- size 131072 (580448 chars):
200000 1 1023
16
16
256
8
2
8
4
4
128
512
128
4
512
512
16
4
16
1
512
4
64
8
16
64
2
8
128
32
8
2
8
512
512
8
4
8
32
128
32
64
8
512
64
512
512
32
256
1
16
1
4
2
4
32
256
2
1
64
1
2
1
512
128
512
256
16
512
512
2
2
512
4
32
8
4
512
2
1
512
512
128
1
4
128
128
256
64
16
64
16
64
2
64
16
8
1
64
8
8
16

## Program A
```python
def go_up_to_down(w, h, value, steps):
    value ^= matrix[h][w]
    if steps == half_steps:
        if value not in counts[h][w]:
            counts[h][w][value] = 0

        counts[h][w][value] += 1
        return

    if w < width - 1:
        go_up_to_down(w + 1, h, value, steps + 1)
    if h < height - 1:
        go_up_to_down(w, h + 1, value, steps + 1)


def go_down_to_up(w, h, value, steps, count_ways):
    if steps == width + height - 2 - half_steps:
        if (value ^ res_find) in counts[h][w]:
            count_ways += counts[h][w][value ^ res_find]
        return count_ways

    delta = 0
    if w > 0:
        delta += go_down_to_up(w - 1, h, value ^ matrix[h][w], steps + 1, count_ways)
    if h > 0:
        delta += go_down_to_up(w, h - 1, value ^ matrix[h][w], steps + 1, count_ways)

    return count_ways + delta


height, width, res_find = [int(num) for num in input().split()]
matrix = []

for h in range(height):
    row = [int(num) for num in input().split()]
    matrix.append(row)

counts = [[dict()] * width for h in range(height)]
half_steps = (width + height - 2) // 2

go_up_to_down(0, 0, 0, 0)
count_ways = go_down_to_up(width - 1, height - 1, 0, 0, 0)

print(count_ways)
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=123 max_rec=6 
  traced size=2: status=ok lines=227 max_rec=11 
  traced size=4: status=ok lines=437 max_rec=21 
  traced size=8: status=ok lines=857 max_rec=41 
  traced size=16: status=ok lines=1697 max_rec=81 
  traced size=32: status=ok lines=3377 max_rec=161 
  traced size=64: status=ok lines=6737 max_rec=321 
  traced size=128: status=ok lines=13457 max_rec=641 
  traced size=256: status=ok lines=26897 max_rec=1281 
  traced size=512: status=ok lines=53777 max_rec=2561 
  traced size=1024: status=ok lines=107537 max_rec=5121 
  traced size=2048: status=ok lines=215057 max_rec=10241 
  traced size=4096: status=ok lines=430097 max_rec=20481 
  traced size=8192: status=ok lines=860177 max_rec=40961 
  untraced time (size:seconds): 1:2.74e-05 2:4.06e-05 4:6.96e-05 8:1.23e-04 16:2.28e-04 32:4.85e-04 64:9.72e-04 128:1.94e-03 256:4.31e-03 512:8.17e-03 1024:1.62e-02 2048:3.25e-02 4096:7.80e-02 8192:1.78e-01 16384:3.94e-01 32768:5.44e-01 65536:5.56e-01 131072:5.62e-01


## Program B
```python
from collections import*
n, m, k = map(int, input().split())
b = [[int(v) for v in input().split()] for _ in range(n)]
if m < n:
    a = [[b[j][i] for j in range(n)] for i in range(m)]
    b = a
    m, n = n, m
cntrs = [Counter() for _ in range(n)]
d = (n + m-1) // 2
for i in range(1<<d):
    ones = bin(i).count('1')
    z = d - ones
    if ones >= n or z >= m: continue
    xor = b[0][0]
    x, y = 0, 0
    for j in range(d):
        if i&(1<<j):
            x += 1
        else:
            y += 1
        xor ^= b[x][y]
    cntrs[x][xor] += 1
sm = 0
sleft = n + m - 2 - d
for i in range(1<<sleft):
    ones = bin(i).count('1')
    z = sleft - ones
    if ones >= n or z >= m: continue
    xor = b[n-1][m-1]
    x, y = n-1, m-1
    for j in range(sleft):
        if i&(1<<j):
            x -= 1
        else:
            y -= 1
        xor ^= b[x][y]
    xor ^= b[x][y] ^ k
    sm += cntrs[x][xor]
print(sm)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=283 max_rec=0 
  traced size=2: status=ok lines=6305 max_rec=0 
  traced size=4: status=cap lines=1500001 max_rec=0 
  untraced time (size:seconds): 1:5.09e-05 2:5.40e-04 4:5.38e-01


# CASE 5: FALSE_DIFFERENT  (pair 78, task apps/4002, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both per-row knapsack DP over (picked count, mod k) then combine rows by DP over mod k.
d_phi=0.450  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n^2)|none # none|-|nest3 # -   slope b=2.321511356765505 (lines 2.321511356765505, time 0.7962873836694087)
Fingerprint B: O(exp)|none # none|-|nest3 # -   slope b=6.074788634594869 (lines 6.074788634594869, time 0.852466549726697)
Ladder used: 'nat' (the task test inputs themselves, size = number of tokens); sizes [4, 5, 6, 9, 11, 12, 13, 18, 28, 63]

## Task statement (truncated)
You are given a matrix $a$ of size $n \times m$ consisting of integers.

You can choose no more than $\left\lfloor\frac{m}{2}\right\rfloor$ elements in each row. Your task is to choose these elements in such a way that their sum is divisible by $k$ and this sum is the maximum.

In other words, you can choose no more than a half (rounded down) of elements in each row, you have to find the maximum sum of these elements divisible by $k$.

Note that you can choose zero elements (and the sum of such set is $0$).


-----Input-----

The first line of the input contains three integers $n$, $m$ and $k$ ($1 \le n, m, k \le 70$) — the number of rows in the matrix, the number of columns in the matrix and the value of $k$. The next $n$ lines contain $m$ elements each, where the $j$-th element of the $i$-th row is $a_{i, j}$ ($1 \le a_{i, j} \le 70$).


-----Output-----

Print one integer — the maximum sum divisible by $k$ you can obtain.


-----Examples-----
Input
3 4 3
1 2 3 4
5 2 2 2
7 1 1 4

Output
24

Input
5 5 4
1 2 4 2 1
3 5 1 2 4
1 5 7 1 2
3 8 7 1 2
8 4 7 1 6

Output
56



-----Note-----

In the first example, the optimal answer is $2$ and $4$ in the first row, $5$ and $2$ in the second row and $7$ and $4$ in the third row. The total sum is $2 + 4 + 5 + 2 + 7 + 4 = 24$.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 4 (8 chars):
1 1 2
1

--- size 12 (25 chars):
3 3 70
1 1 1
1 1 1
1 1 1

--- size 63 (181 chars):
10 6 55
15 17 49 38 7 61
60 22 27 46 21 65
33 51 2 33 36 69
14 54 24 36 51 9
36 61 38 38 46 64
51 20 38 4 19 2
47 34 65 43 56 65
5 39 31 59 27 9
17 47 13 33 57 51
48 22 53 69 28 68


## Program A
```python

"""

70*70*70
70*70*70

dp[num][k] = ?

"""

import math
from sys import stdin

n,m,k = map(int,stdin.readline().split())

a = []
for i in range(n):
    tmp = list(map(int,stdin.readline().split()))
    a.append(tmp)

maxlis = []

for i in range(n):

    tdp = [[float("-inf")] * k for i in range(m//2+1)]
    tdp[0][0] = 0
    
    for j in range(m):
        for x in range(len(tdp)-2,-1,-1):
            for y in range(k):
                tdp[x+1][(y+a[i][j])%k] = max(tdp[x+1][(y+a[i][j])%k] , tdp[x][y] + a[i][j])
    
    udp = [float("-inf")] * k
    for x in range(len(tdp)):
        for y in range(k):
            udp[y] = max(udp[y] , tdp[x][y])

    maxlis.append(udp)


dp = maxlis[0]

for i in range(1,len(maxlis)):

    now = maxlis[i]
    ndp = [float("-inf")] * k

    for x in range(k):
        for y in range(k):
            ndp[(x+y)%k] = max(ndp[(x+y)%k] , dp[x]+now[y])
    dp = ndp

#print (maxlis)
print (dp[0])
```
Trace of A on ladder 'nat':
  traced size=4: status=ok lines=30 max_rec=0 
  traced size=5: status=ok lines=59 max_rec=0 
  traced size=6: status=ok lines=69 max_rec=0 
  traced size=9: status=ok lines=165 max_rec=0 
  traced size=11: status=ok lines=16390 max_rec=0 
  traced size=12: status=ok lines=22085 max_rec=0 
  traced size=13: status=ok lines=591 max_rec=0 
  traced size=18: status=ok lines=417 max_rec=0 
  traced size=28: status=ok lines=956 max_rec=0 
  traced size=63: status=ok lines=80396 max_rec=0 
  untraced time (size:seconds): 4:1.50e-05 5:2.13e-05 6:2.37e-05 9:4.01e-05 11:3.58e-03 12:4.79e-03 13:1.27e-04 18:9.01e-05 28:2.10e-04 63:1.90e-02


## Program B
```python
n, m, k = list(map(int, input().split()))
mat = [list(map(int, input().split())) for i in range(n)]
inf = 1 << 30
modulars = [[-inf]*(k) for i in range(n)]

for index in range(n):
    a = mat[index]
    dp = [[[-inf]*k for i in range(m//2+1)]for _ in range(m+1)]
    #dp[index][picked][mod] = index番目まで見てそのうちpicked個取ってmodular(mod k) になる時の最大値
    dp[0][0][0] = 0
    for i in range(1, m+1):
        v = a[i-1]
        for picked in range(m//2+1):
            for mod in range(k):
                if picked >= 1:
                    dp[i][picked][mod] = max(dp[i][picked][mod],dp[i-1][picked][mod], dp[i-1][picked-1][(mod-v) % k]+v)
                else:
                    dp[i][picked][mod] = max(dp[i][picked][mod],dp[i-1][picked][mod])

    for mod in range(k):
        modulars[index][mod] = max(dp[m][picked][mod]
                                   for picked in range(m//2+1))

dp = [[-inf]*(k) for i in range(n+1)]
dp[0][0] = 0
#dp[n][mod] = n番目まで見て総和がmodの時の最大値
for i in range(1, n+1):
    for mod in range(k):
        dp[i][mod] = max(dp[i-1][(mod-prevmod) % k] +
                         modulars[i-1][prevmod]for prevmod in range(k))

ans = dp[n][0]
print(ans)
```
Trace of B on ladder 'nat':
  traced size=4: status=ok lines=83 max_rec=0 
  traced size=5: status=ok lines=174 max_rec=0 
  traced size=6: status=ok lines=202 max_rec=0 
  traced size=9: status=ok lines=341 max_rec=0 
  traced size=11: status=ok lines=53655 max_rec=0 
  untraced time (size:seconds): 4:2.11e-05 5:3.12e-05 6:3.58e-05 9:5.15e-05 11:1.92e-03 12:2.81e-03 13:1.40e-04 18:1.16e-04 28:2.64e-04 63:1.21e-02


# CASE 8: FALSE_DIFFERENT  (pair 175, task apps/4408, io=stdio)
LLM labeller said: same=1 level=None confidence=low reason: Both are knapsack-style DP distributing cards among players with joy h; A per favorite color, B global dp[players][cards] table.
d_phi=0.544  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest2 # dict   slope b=0.9839754060169054 (lines 0.9839754060169054, time 1.0413035223925886)
Fingerprint B: O(n^2)|none # none|-|nest3 # counter   slope b=1.9947428856992417 (lines 1.9947428856992417, time 2.0464811748457548)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
There are $n$ players sitting at the card table. Each player has a favorite number. The favorite number of the $j$-th player is $f_j$.

There are $k \cdot n$ cards on the table. Each card contains a single integer: the $i$-th card contains number $c_i$. Also, you are given a sequence $h_1, h_2, \dots, h_k$. Its meaning will be explained below.

The players have to distribute all the cards in such a way that each of them will hold exactly $k$ cards. After all the cards are distributed, each player counts the number of cards he has that contains his favorite number. The joy level of a player equals $h_t$ if the player holds $t$ cards containing his favorite number. If a player gets no cards with his favorite number (i.e., $t=0$), his joy level is $0$.

Print the maximum possible total joy levels of the players after the cards are distributed. Note that the sequence $h_1, \dots, h_k$ is the same for all the players.


-----Input-----

The first line of input contains two integers $n$ and $k$ ($1 \le n \le 500, 1 \le k \le 10$) — the number of players and the number of cards each player will get.

The second line contains $k \cdot n$ integers $c_1, c_2, \dots, c_{k \cdot n}$ ($1 \le c_i \le 10^5$) — the numbers written on the cards.

The third line contains $n$ integers $f_1, f_2, \dots, f_n$ ($1 \le f_j \le 10^5$) — the favorite numbers of the players.

The fourth line contains $k$ integers $h_1, h_2, \dots, h_k$ ($1 \le h_t \le 10^5$), where $h_t$ is the joy level of a player if he gets exactly $t$ cards with his favorite number written on them. It is guaranteed that the condition $h_{t - 1} < h_t$ holds for each $t \in [2..k]$.


-----Output-----

Print one integer — the maximum possible total joy levels of the players among all possible card distributions.


-----Exampl

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (34 chars):
3 3
9 9 9 9 9 9 9 9 9
1 2 3
1 2 3

--- size 512 (13968 chars):
1536 3
9 9 9 9 9 9 9 9 9
2 3 5 8 9 10 11 12 13 17 18 19 20 21 22 23 24 25 26 30 31 32 33 37 39 40 42 43 44 45 49 50 52 55 57 60 61 62 63 69 70 71 72 73 76 77 79 80 81 82 83 84 87 88 89 90 91 92 93 99 100 101 102 103 104 105 106 107 108 111 112 114 116 117 118 119 121 122 123 124 125 127 128 129 130 
--- size 131072 (221504 chars):
22222 3
1 2 3
1 2 3
1 2 3
1 2 3
9 9 9 9 9 9 9 9 9
9 9 9 9 9 9 9 9 9
9 9 9 9 9 9 9 9 9
9 9 9 9 9 9 9 9 9
9 9 9 9 9 9 9 9 9
1 2 3
1 2 3
1 2 3
9 9 9 9 9 9 9 9 9
1 2 3
1 2 3
1 2 3
9 9 9 9 9 9 9 9 9
1 2 3
1 2 3
9 9 9 9 9 9 9 9 9
1 2 3
9 9 9 9 9 9 9 9 9
1 2 3
9 9 9 9 9 9 9 9 9
1 2 3
1 2 3
9 9 9 9 9 9 9 9 

## Program A
```python
def solve():
    n, k = list(map(int, input().split()))
    c = list(map(int, input().split()))
    f = list(map(int, input().split()))
    h = list(map(int, input().split()))
    cnt = {}
    for i in c:
        cnt[i] = cnt.get(i, 0) + 1
    likecolor = {}
    for i in range(n):
        likecolor.setdefault(f[i], []).append(i)
        cnt[f[i]] = cnt.get(f[i], 0)
    ans = 0
    for key, v in list(likecolor.items()):
        n1 = len(v)
        if cnt[key] >= n1 * k:
            ans += n1 * h[k - 1]
            continue
        dp = [[-float("INF")] * (cnt[key]+1) for _ in range(n1 + 1)]
        dp[0][0] = 0
        for i in range(n1):
            j = i + 1
            for e in range(cnt[key] + 1):
                dp[j][e] = max(dp[j][e], dp[i][e])
                for w in range(e + 1, min(cnt[key] + 1, e + k + 1)):
                    dp[j][w] = max(dp[i][e] + h[w - e - 1], dp[j][w])
        ans += dp[n1][cnt[key]]
    print(ans)


solve()
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=85 max_rec=1 
  traced size=2: status=ok lines=139 max_rec=1 
  traced size=4: status=ok lines=237 max_rec=1 
  traced size=8: status=ok lines=453 max_rec=1 
  traced size=16: status=ok lines=895 max_rec=1 
  traced size=32: status=ok lines=1749 max_rec=1 
  traced size=64: status=ok lines=3487 max_rec=1 
  traced size=128: status=ok lines=6933 max_rec=1 
  traced size=256: status=ok lines=13855 max_rec=1 
  traced size=512: status=ok lines=27669 max_rec=1 
  traced size=1024: status=ok lines=55327 max_rec=1 
  traced size=2048: status=ok lines=110623 max_rec=1 
  traced size=4096: status=ok lines=221205 max_rec=1 
  traced size=8192: status=ok lines=442399 max_rec=1 
  traced size=16384: status=ok lines=884767 max_rec=1 
  untraced time (size:seconds): 1:2.57e-05 2:3.04e-05 4:4.20e-05 8:6.60e-05 16:1.12e-04 32:2.07e-04 64:3.84e-04 128:7.41e-04 256:1.48e-03 512:2.91e-03 1024:6.09e-03 2048:1.25e-02 4096:2.52e-02 8192:5.00e-02 16384:1.03e-01 32768:2.31e-01 65536:5.15e-01


## Program B
```python

from collections import Counter
from queue import Queue
import sys
import math
import os.path
sys.setrecursionlimit(10**9)
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
def ni():
    return map(int, input().split())
def nio(offset):
    return map(lambda x: int(x) + offset, input().split())
def nia():
    return list(map(int, input().split()))
def toString(aList, sep=" "):
    return sep.join(str(x) for x in aList)
def mapInvertIndex(aList):
    return {k: v for v, k in enumerate(aList)}
def sortId(arr):
    return sorted(range(arr), key=lambda k: arr[k])
n, k = ni()
c = nia()
f = nia()
h = nia()
h.insert(0,0)
cc = Counter(c)
cf = Counter(f)
n1 = n+1
k1 = k+1
nk1 = n*k+1
dp = [[0]*nk1 for _ in range(n1)]
for ni in range(1,n1):
    for ki in range(1,nk1):
        mficount = min(k,ki) + 1        
        for kii in range(mficount):
            # log(ni,ki, kii, dp[ni][ki], dp[ni-1][ki-kii] + h[kii])
            dp[ni][ki] = max(dp[ni][ki], dp[ni-1][ki-kii] + h[kii])
res = 0
for fk,fv in cf.items():
    res += dp[fv][cc[fk]]
print(res)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=327 max_rec=1 
  traced size=2: status=ok lines=1215 max_rec=1 
  traced size=4: status=ok lines=4773 max_rec=1 
  traced size=8: status=ok lines=19017 max_rec=1 
  traced size=16: status=ok lines=76017 max_rec=1 
  traced size=32: status=ok lines=304065 max_rec=1 
  traced size=64: status=ok lines=1216353 max_rec=1 
  untraced time (size:seconds): 1:7.68e-05 2:2.16e-04 4:7.68e-04 8:3.03e-03 16:1.21e-02 32:4.87e-02 64:2.01e-01 128:8.52e-01


# CASE 11: MISSED_DIFFERENT  (pair 20, task apps/4436, io=stdio)
LLM labeller said: same=0 level=complexity confidence=low reason: A finds one divisor pair up to sqrt(n) then factors a or b; B builds the full divisor list and tries all divisor pairs with membership check.
d_phi=0.042  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # set,sort   slope b=1.0609666702602947 (lines 1.0609666702602947, time 0.9101418103654924)
Fingerprint B: O(n)|none # none|-|nest2 # set,sort   slope b=1.057211120890646 (lines 1.057211120890646, time 0.9959052121767233)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
You are given one integer number $n$. Find three distinct integers $a, b, c$ such that $2 \le a, b, c$ and $a \cdot b \cdot c = n$ or say that it is impossible to do it.

If there are several answers, you can print any.

You have to answer $t$ independent test cases.


-----Input-----

The first line of the input contains one integer $t$ ($1 \le t \le 100$) — the number of test cases.

The next $n$ lines describe test cases. The $i$-th test case is given on a new line as one integer $n$ ($2 \le n \le 10^9$).


-----Output-----

For each test case, print the answer on it. Print "NO" if it is impossible to represent $n$ as $a \cdot b \cdot c$ for some distinct integers $a, b, c$ such that $2 \le a, b, c$.

Otherwise, print "YES" and any possible such representation.


-----Example-----
Input
5
64
32
97
2
12345

Output
YES
2 4 8 
NO
NO
NO
YES
3 5 823

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (19 chars):
5
64
32
97
2
12345

--- size 512 (8715 chars):
2560
32
64
64
2
12345
12345
2
2
64
97
97
12345
2
32
32
97
12345
97
64
64
97
2
97
97
97
12345
97
12345
64
12345
2
64
32
97
64
2
64
12345
97
97
64
12345
12345
64
97
12345
12345
64
2
97
97
64
2
64
64
97
32
64
12345
64
12345
97
97
2
2
64
97
64
12345
2
2
64
2
64
12345
32
2
64
32
32
2
32
32
2
97
12345
97

--- size 131072 (680453 chars):
200000
97
97
12345
32
64
32
32
32
2
12345
2
32
12345
12345
97
32
97
64
12345
32
2
32
97
2
64
32
2
97
32
64
32
12345
12345
32
32
32
97
2
97
2
32
12345
2
12345
12345
97
12345
64
97
64
32
64
32
97
12345
64
64
2
64
64
64
12345
2
12345
12345
97
12345
12345
64
64
12345
32
97
32
32
12345
64
64
12345
12345


## Program A
```python
import sys
input = sys.stdin.readline

def factors(n):
	ret = set()
	for i in range(2, int(n**.5) + 1):
		if n%i == 0:
			ret.add(i)
			ret.add(n//i)
	return ret

def solve(n):
	for i in range(2, int(n**.5)+1):
		if n%i == 0 and i != n//i:
			a, b = i, n//i
			fa, fb = factors(a), factors(b)
			# option 1
			if len(fa) > 0:
				for fac in fa:
					if len(set([fac, a//fac, b])) == 3:
						return [fac, a//fac, b]
			# option 2
			if len(fb) > 0:
				for fac in fb:
					if len(set([fac, b//fac, a])) == 3:
						return [fac, b//fac, a]
	return 'NO'


for _ in range(int(input())):
	n = int(input())
	ans = solve(n)
	if ans == 'NO':
		print('NO')
	else:
		print('YES')
		print(*sorted(ans))
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=289 max_rec=1 
  traced size=2: status=ok lines=296 max_rec=1 
  traced size=4: status=ok lines=948 max_rec=1 
  traced size=8: status=ok lines=1698 max_rec=1 
  traced size=16: status=ok lines=3925 max_rec=1 
  traced size=32: status=ok lines=8646 max_rec=1 
  traced size=64: status=ok lines=17066 max_rec=1 
  traced size=128: status=ok lines=38267 max_rec=1 
  traced size=256: status=ok lines=73270 max_rec=1 
  traced size=512: status=ok lines=145035 max_rec=1 
  traced size=1024: status=ok lines=299268 max_rec=1 
  traced size=2048: status=ok lines=584234 max_rec=1 
  traced size=4096: status=ok lines=1163549 max_rec=1 
  untraced time (size:seconds): 1:3.77e-05 2:4.86e-05 4:9.48e-05 8:1.48e-04 16:3.29e-04 32:6.44e-04 64:1.29e-03 128:2.64e-03 256:5.25e-03 512:1.04e-02 1024:2.09e-02 2048:4.09e-02 4096:8.39e-02 8192:1.65e-01 16384:3.29e-01 32768:6.54e-01 65536:8.10e-01 131072:8.17e-01


## Program B
```python
from functools import reduce
def factors(n):
    k = sorted(list(set(reduce(list.__add__,
                     ([i,n//i] for i in range(1,int(n**0.5+1)) if n%i == 0)))))
    return k[1:]
t = int(input())
for _ in range(0,t):
    n = int(input())
    f = factors(n)
    if len(f) < 3:
        print('NO')
    else:
        ans = 'NO'
        a,b,c = -1,-1,-1
        for i in range(0,len(f)):
            for j in range(i+1,len(f)):
                 temp = n//f[i]
                 temp //= f[j]
                 if temp in f and temp != f[i] and temp != f[j]:
                     a,b,c = f[i],f[j],temp
                     ans = 'YES'
                     break
            if ans == 'YES':
                break
        if ans == 'YES':
            print(ans)
            print(a,b,c)
        else:
            print(ans)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=275 max_rec=1 
  traced size=2: status=ok lines=285 max_rec=1 
  traced size=4: status=ok lines=914 max_rec=1 
  traced size=8: status=ok lines=1736 max_rec=1 
  traced size=16: status=ok lines=3763 max_rec=1 
  traced size=32: status=ok lines=8294 max_rec=1 
  traced size=64: status=ok lines=16487 max_rec=1 
  traced size=128: status=ok lines=36264 max_rec=1 
  traced size=256: status=ok lines=69923 max_rec=1 
  traced size=512: status=ok lines=138271 max_rec=1 
  traced size=1024: status=ok lines=284771 max_rec=1 
  traced size=2048: status=ok lines=558074 max_rec=1 
  traced size=4096: status=ok lines=1110620 max_rec=1 
  untraced time (size:seconds): 1:5.50e-05 2:7.18e-05 4:1.44e-04 8:2.38e-04 16:5.13e-04 32:1.03e-03 64:2.09e-03 128:4.23e-03 256:8.42e-03 512:1.67e-02 1024:3.36e-02 2048:6.63e-02 4096:1.32e-01 8192:2.64e-01 16384:5.27e-01 32768:1.06e+00


# CASE 14: MISSED_DIFFERENT  (pair 88, task apps/4477, io=stdio)
LLM labeller said: same=0 level=formula_vs_iteration confidence=high reason: A: enumerates digit-repeated numbers 1..9999 summing digits; B: closed form 10*(d-1)+len*(len+1)/2.
d_phi=0.042  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest2 # -   slope b=0.9973164898388582 (lines 0.9973164898388582, time 0.6633775829596652)
Fingerprint B: O(n)|none # none|-|nest1 # -   slope b=0.9994178500459822 (lines 0.9994178500459822, time 0.6673400395179455)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
There is a building consisting of $10~000$ apartments numbered from $1$ to $10~000$, inclusive.

Call an apartment boring, if its number consists of the same digit. Examples of boring apartments are $11, 2, 777, 9999$ and so on.

Our character is a troublemaker, and he calls the intercoms of all boring apartments, till someone answers the call, in the following order:

  First he calls all apartments consisting of digit $1$, in increasing order ($1, 11, 111, 1111$).  Next he calls all apartments consisting of digit $2$, in increasing order ($2, 22, 222, 2222$)  And so on. 

The resident of the boring apartment $x$ answers the call, and our character stops calling anyone further.

Our character wants to know how many digits he pressed in total and your task is to help him to count the total number of keypresses.

For example, if the resident of boring apartment $22$ answered, then our character called apartments with numbers $1, 11, 111, 1111, 2, 22$ and the total number of digits he pressed is $1 + 2 + 3 + 4 + 1 + 2 = 13$.

You have to answer $t$ independent test cases.


-----Input-----

The first line of the input contains one integer $t$ ($1 \le t \le 36$) — the number of test cases.

The only line of the test case contains one integer $x$ ($1 \le x \le 9999$) — the apartment number of the resident who answered the call. It is guaranteed that $x$ consists of the same digit.


-----Output-----

For each test case, print the answer: how many digits our character pressed in total.


-----Example-----
Input
4
22
9999
1
777

Output
13
90
1
66

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (129 chars):
36
1
2
3
4
5
6
7
8
9
11
22
33
44
55
66
77
88
99
111
222
333
444
555
666
777
888
999
1111
2222
3333
4444
5555
6666
7777
8888
9999

--- size 512 (64294 chars):
18432
55
7
5
888
8888
3333
1111
1
666
333
888
55
22
666
333
8
1
444
999
111
555
555
333
6666
8
5555
7
55
333
4
4444
7
111
222
1
8888
8888
1
88
6666
7
888
222
666
5
5555
5
6
111
44
1
8888
4
8888
99
88
5555
3333
2
222
1
8888
2222
999
6
2222
4
9999
33
5555
5
11
22
1111
77
44
4444
333
7777
444
22
7
33
1
--- size 131072 (700155 chars):
200000
222
222
7777
55
7
66
11
9
2222
2222
22
222
22
111
3
33
888
66
222
1111
5
77
5555
444
77
5
66
44
11
44
666
2222
444
888
77
777
333
9999
4
222
4
11
7
11
555
7777
5
2
1111
4
8
4
2222
6666
222
7
8
22
666
77
22
8
1
5555
2
33
5555
5555
8888
1111
111
1111
99
1111
7
888
99
66
1
1111
66
66
88
888
7
44

## Program A
```python
#   ==========     //\\       //||     ||====//||
#       ||        //  \\        ||     ||   // ||
#       ||       //====\\       ||     ||  //  ||
#       ||      //      \\      ||     || //   ||
#   ========== //        \\  ========  ||//====|| 
#  code


def solve():
    x = int(input())
    ans = 0
    ok = 0

    for i in range(1, 10):
        n = 0
        for j in range(4):
            n = n * 10 + i
            ans += (j + 1)
            if n == x:
                ok = 1
                break
        if ok:
            break
    print(ans)

def main():
    t = 1
    t = int(input())
    for _ in range(t):
        solve()

def __starting_point():
    main()
__starting_point()
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=3680 max_rec=1 
  traced size=2: status=ok lines=7232 max_rec=1 
  traced size=4: status=ok lines=14468 max_rec=1 
  traced size=8: status=ok lines=31272 max_rec=1 
  traced size=16: status=ok lines=60160 max_rec=1 
  traced size=32: status=ok lines=116136 max_rec=1 
  traced size=64: status=ok lines=232156 max_rec=1 
  traced size=128: status=ok lines=466144 max_rec=1 
  traced size=256: status=ok lines=934908 max_rec=1 
  traced size=512: status=cap lines=1500001 max_rec=1 
  untraced time (size:seconds): 1:1.29e-04 2:2.46e-04 4:4.79e-04 8:9.87e-04 16:1.92e-03 32:3.75e-03 64:7.48e-03 128:1.49e-02 256:2.98e-02 512:5.96e-02 1024:1.20e-01 2048:2.39e-01 4096:4.79e-01 8192:6.47e-01 16384:6.47e-01 32768:6.48e-01 65536:6.46e-01 131072:6.49e-01


## Program B
```python
t=int(input())
for _ in range(t):
    x=input()
    a=int(x[0])
    b=len(x)
    print(10*(a-1)+(b*(b+1))//2)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=182 max_rec=0 
  traced size=2: status=ok lines=362 max_rec=0 
  traced size=4: status=ok lines=722 max_rec=0 
  traced size=8: status=ok lines=1442 max_rec=0 
  traced size=16: status=ok lines=2882 max_rec=0 
  traced size=32: status=ok lines=5762 max_rec=0 
  traced size=64: status=ok lines=11522 max_rec=0 
  traced size=128: status=ok lines=23042 max_rec=0 
  traced size=256: status=ok lines=46082 max_rec=0 
  traced size=512: status=ok lines=92162 max_rec=0 
  traced size=1024: status=ok lines=184322 max_rec=0 
  traced size=2048: status=ok lines=368642 max_rec=0 
  untraced time (size:seconds): 1:7.20e-05 2:1.33e-04 4:2.57e-04 8:5.07e-04 16:1.01e-03 32:2.02e-03 64:4.13e-03 128:8.19e-03 256:1.62e-02 512:3.25e-02 1024:6.47e-02 2048:1.30e-01 4096:2.60e-01 8192:3.51e-01 16384:3.88e-01 32768:3.62e-01 65536:3.59e-01 131072:3.56e-01


# CASE 17: MISSED_DIFFERENT  (pair 141, task apps/4104, io=stdio)
LLM labeller said: same=0 level=paradigm confidence=low reason: A evals the expression then adjusts per operator with extra offset by scanning following digits; B parses numbers one pass with a sign/factor accumulator.
d_phi=0.001  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # -   slope b=1.0010794810853054 (lines 1.0010794810853054, time 1.0368022041742606)
Fingerprint B: O(n)|none # none|-|nest1 # -   slope b=0.9983264855631256 (lines 0.9983264855631256, time 0.9955008042538918)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]

## Task statement (truncated)
One very experienced problem writer decided to prepare a problem for April Fools Day contest. The task was very simple - given an arithmetic expression, return the result of evaluating this expression. However, looks like there is a bug in the reference solution...


-----Input-----

The only line of input data contains the arithmetic expression. The expression will contain between 2 and 10 operands, separated with arithmetic signs plus and/or minus. Each operand will be an integer between 0 and 255, inclusive.


-----Output-----

Reproduce the output of the reference solution, including the bug.


-----Examples-----
Input
8-7+6-5+4-3+2-1-0

Output
4

Input
2+2

Output
-46

Input
112-37

Output
375

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (20 chars):
97+67+12+9+42+45+13

--- size 128 (2433 chars):
97+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+4
--- size 8192 (155649 chars):
97+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+45+1397+67+12+9+42+4

## Program A
```python
s = input()
val = eval(s)
for i in range(len(s)):
    if s[i] ==  '+':
        j = i + 1
        c = -5
        while j < len(s) and s[j] != '+' and s[j] != '-':
            c *= 10
            j += 1
        val += c
    elif s[i] == '-':
        j = i + 1
        c = 3
        while j < len(s) and s[j] != '+' and s[j] != '-':
            c *= 10
            j += 1
        val += c
print(val)
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=112 max_rec=0 
  traced size=2: status=ok lines=226 max_rec=0 
  traced size=4: status=ok lines=454 max_rec=0 
  traced size=8: status=ok lines=910 max_rec=0 
  traced size=16: status=ok lines=1822 max_rec=0 
  traced size=32: status=ok lines=3646 max_rec=0 
  traced size=64: status=ok lines=7294 max_rec=0 
  traced size=128: status=ok lines=14590 max_rec=0 
  traced size=256: status=ok lines=29182 max_rec=0 
  traced size=512: status=ok lines=58366 max_rec=0 
  traced size=1024: status=ok lines=116734 max_rec=0 
  traced size=2048: status=error lines=2 max_rec=0 err=RecursionError('maximum recursion depth exceeded during compilation')
  traced size=4096: status=error lines=2 max_rec=0 err=RecursionError('maximum recursion depth exceeded during compilation')
  traced size=8192: status=error lines=2 max_rec=0 err=RecursionError('maximum recursion depth exceeded during compilation')
  untraced time (size:seconds): 1:4.57e-05 2:5.56e-05 4:7.70e-05 8:1.16e-04 16:2.03e-04 32:3.86e-04 64:7.56e-04 128:1.50e-03 256:3.07e-03 512:6.34e-03 1024:1.29e-02


## Program B
```python
s = [ord(c) - 48 for c in input()]
r, t, f = 0, 0, 1
for x in s:
    if x < 0:
        r += f * t
        f = -4 - x
        t = 0
    t = t * 10 + x
print(r + f * t)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=98 max_rec=0 
  traced size=2: status=ok lines=192 max_rec=0 
  traced size=4: status=ok lines=380 max_rec=0 
  traced size=8: status=ok lines=756 max_rec=0 
  traced size=16: status=ok lines=1508 max_rec=0 
  traced size=32: status=ok lines=3012 max_rec=0 
  traced size=64: status=ok lines=6020 max_rec=0 
  traced size=128: status=ok lines=12036 max_rec=0 
  traced size=256: status=ok lines=24068 max_rec=0 
  traced size=512: status=ok lines=48132 max_rec=0 
  traced size=1024: status=ok lines=96260 max_rec=0 
  traced size=2048: status=ok lines=192516 max_rec=0 
  traced size=4096: status=ok lines=385028 max_rec=0 
  traced size=8192: status=ok lines=770052 max_rec=0 
  untraced time (size:seconds): 1:1.38e-05 2:1.76e-05 4:2.61e-05 8:4.27e-05 16:7.48e-05 32:1.38e-04 64:2.65e-04 128:5.19e-04 256:1.03e-03 512:2.06e-03 1024:4.13e-03 2048:8.25e-03 4096:1.65e-02 8192:3.28e-02


# CASE 20: MISSED_DIFFERENT  (pair 181, task apps/4040, io=stdio)
LLM labeller said: same=0 level=other confidence=low reason: A simulates jumps with platforms right-aligned then shifted left greedily; B checks a total-length bound and lays platforms left-packed with up to d-1 gaps.
d_phi=0.001  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # -   slope b=1.0070685255916398 (lines -1.6092450654021745e-16, time 1.0070685255916398)
Fingerprint B: O(n)|none # none|-|nest1 # -   slope b=1.00364623823334 (lines -4.807838191315526e-17, time 1.00364623823334)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]

## Task statement (truncated)
There is a river of width $n$. The left bank of the river is cell $0$ and the right bank is cell $n + 1$ (more formally, the river can be represented as a sequence of $n + 2$ cells numbered from $0$ to $n + 1$). There are also $m$ wooden platforms on a river, the $i$-th platform has length $c_i$ (so the $i$-th platform takes $c_i$ consecutive cells of the river). It is guaranteed that the sum of lengths of platforms does not exceed $n$.

You are standing at $0$ and want to reach $n+1$ somehow. If you are standing at the position $x$, you can jump to any position in the range $[x + 1; x + d]$. However you don't really like the water so you can jump only to such cells that belong to some wooden platform. For example, if $d=1$, you can jump only to the next position (if it belongs to the wooden platform). You can assume that cells $0$ and $n+1$ belong to wooden platforms.

You want to know if it is possible to reach $n+1$ from $0$ if you can move any platform to the left or to the right arbitrary number of times (possibly, zero) as long as they do not intersect each other (but two platforms can touch each other). It also means that you cannot change the relative order of platforms.

Note that you should move platforms until you start jumping (in other words, you first move the platforms and then start jumping).

For example, if $n=7$, $m=3$, $d=2$ and $c = [1, 2, 1]$, then one of the ways to reach $8$ from $0$ is follow:

 [Image] The first example: $n=7$. 


-----Input-----

The first line of the input contains three integers $n$, $m$ and $d$ ($1 \le n, m, d \le 1000, m \le n$) — the width of the river, the number of platforms and the maximum distance of your jump, correspondingly.

The second line of the input contains $m$ integers $c_1, c_2, \dots, c_m$ ($1 \le c_i \le 

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (10 chars):
2 2 1
1 1

--- size 256 (1032 chars):
512 2 1
1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 
--- size 65536 (262155 chars):
131072 2 1
1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1

## Program A
```python
n, m, d = list(map(int, input().split()))

lengths = list(map(int, input().split()))
poses = [n + 1] * (m + 1)
index = m - 1
while index >= 0:
    poses[index] = poses[index + 1] - lengths[index]
    index -= 1

#print(poses)

cur = 0
ind = 0
result = True
while cur < n + 1:
    if cur + d >= n + 1:
        break
    if ind == m:
        result = False
        break
    if cur + d <= poses[ind]:
        poses[ind] = cur + d
        cur = cur + d + lengths[ind] - 1
        ind += 1
    else:
        cur = cur + d

if result:
    print("YES")
    poses.append(0)
    lengths.append(0)
    lengths.append(1)
    res = []
    for ind, it in enumerate(poses[:-1]):
        for _ in range(it - poses[ind - 1] - lengths[ind - 1]):
            res.append('0')
        for _ in range(lengths[ind]):
            res.append(str(ind + 1))
    print(" ".join(res))
else:
    print("NO")
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=52 max_rec=0 
  traced size=2: status=ok lines=35 max_rec=0 
  traced size=4: status=ok lines=35 max_rec=0 
  traced size=8: status=ok lines=35 max_rec=0 
  traced size=16: status=ok lines=35 max_rec=0 
  traced size=32: status=ok lines=35 max_rec=0 
  traced size=64: status=ok lines=35 max_rec=0 
  traced size=128: status=ok lines=35 max_rec=0 
  traced size=256: status=ok lines=35 max_rec=0 
  traced size=512: status=ok lines=35 max_rec=0 
  traced size=1024: status=ok lines=35 max_rec=0 
  traced size=2048: status=ok lines=35 max_rec=0 
  traced size=4096: status=ok lines=35 max_rec=0 
  traced size=8192: status=ok lines=35 max_rec=0 
  traced size=16384: status=ok lines=35 max_rec=0 
  traced size=32768: status=ok lines=35 max_rec=0 
  traced size=65536: status=ok lines=35 max_rec=0 
  untraced time (size:seconds): 1:1.68e-05 2:1.58e-05 4:1.74e-05 8:1.75e-05 16:1.56e-05 32:1.91e-05 64:2.64e-05 128:3.85e-05 256:6.27e-05 512:1.08e-04 1024:1.97e-04 2048:3.81e-04 4096:7.42e-04 8192:1.46e-03 16384:2.93e-03 32768:5.92e-03 65536:1.26e-02


## Program B
```python
n,m,d = map(int,input().split())
c = list(map(int,input().split()))
sc = sum(c)
if sc + (len(c)+ 1) * (d - 1) < n:
    print("NO")
else:
    print("YES")
    ko = n - sc
    for i in range(m):
        if ko != 0:
            if ko >= d - 1:
                print("0 " * (d -1 ), end = "")
                ko -= d -1
            else:
                print("0 " * (ko ), end = "")
                ko = 0
        print((str(i + 1) + " ") * c[i], end = "")
    print("0 " * (ko ), end = "")
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=14 max_rec=0 
  traced size=2: status=ok lines=14 max_rec=0 
  traced size=4: status=ok lines=14 max_rec=0 
  traced size=8: status=ok lines=14 max_rec=0 
  traced size=16: status=ok lines=14 max_rec=0 
  traced size=32: status=ok lines=14 max_rec=0 
  traced size=64: status=ok lines=14 max_rec=0 
  traced size=128: status=ok lines=14 max_rec=0 
  traced size=256: status=ok lines=14 max_rec=0 
  traced size=512: status=ok lines=14 max_rec=0 
  traced size=1024: status=ok lines=14 max_rec=0 
  traced size=2048: status=ok lines=14 max_rec=0 
  traced size=4096: status=ok lines=14 max_rec=0 
  traced size=8192: status=ok lines=14 max_rec=0 
  traced size=16384: status=ok lines=14 max_rec=0 
  traced size=32768: status=ok lines=14 max_rec=0 
  traced size=65536: status=ok lines=14 max_rec=0 
  untraced time (size:seconds): 1:1.47e-05 2:1.47e-05 4:1.50e-05 8:1.63e-05 16:1.80e-05 32:2.20e-05 64:2.82e-05 128:4.17e-05 256:6.62e-05 512:1.15e-04 1024:2.10e-04 2048:4.06e-04 4096:7.87e-04 8192:1.55e-03 16384:3.11e-03 32768:6.21e-03 65536:1.33e-02
