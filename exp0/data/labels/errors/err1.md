# CASE 1: FALSE_DIFFERENT  (pair 21, task apps/4235, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both 2-color the graph by traversal (A stack DFS, B BFS) and orient edges by color.
d_phi=0.344  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # -   slope b=0.7591964140118793 (lines 0.7591964140118793, time 0.6380541474613042)
Fingerprint B: O(1)|none # none|-|nest2 # -   slope b=-1.2888358271175892e-06 (lines -1.2888358271175892e-06, time None)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
You are given a connected undirected graph consisting of $n$ vertices and $m$ edges. There are no self-loops or multiple edges in the given graph.

You have to direct its edges in such a way that the obtained directed graph does not contain any paths of length two or greater (where the length of path is denoted as the number of traversed edges).


-----Input-----

The first line contains two integer numbers $n$ and $m$ ($2 \le n \le 2 \cdot 10^5$, $n - 1 \le m \le 2 \cdot 10^5$) — the number of vertices and edges, respectively.

The following $m$ lines contain edges: edge $i$ is given as a pair of vertices $u_i$, $v_i$ ($1 \le u_i, v_i \le n$, $u_i \ne v_i$). There are no multiple edges in the given graph, i. e. for each pair ($u_i, v_i$) there are no other pairs ($u_i, v_i$) and ($v_i, u_i$) in the list of edges. It is also guaranteed that the given graph is connected (there is a path between any pair of vertex in the given graph).


-----Output-----

If it is impossible to direct edges of the given graph in such a way that the obtained directed graph does not contain paths of length at least two, print "NO" in the first line.

Otherwise print "YES" in the first line, and then print any suitable orientation of edges: a binary string (the string consisting only of '0' and '1') of length $m$. The $i$-th element of this string should be '0' if the $i$-th edge of the graph should be directed from $u_i$ to $v_i$, and '1' otherwise. Edges are numbered in the order they are given in the input.


-----Example-----
Input
6 5
1 5
2 1
1 4
3 1
6 1

Output
YES
10100



-----Note-----

The picture corresponding to the first example: [Image]

And one of possible answers: $\text{of}$

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (51 chars):
10 10
6 8
9 10
10 1
2 10
10 7
3 1
8 1
2 1
4 1
5 10

--- size 512 (23040 chars):
5120 10
2 10
9 10
9 10
8 1
5 10
4 1
2 1
8 1
6 8
3 1
3 1
5 10
8 1
2 10
10 1
3 1
5 10
3 1
9 10
6 8
3 1
8 1
10 7
3 1
3 1
5 10
3 1
4 1
9 10
5 10
2 1
9 10
2 10
3 1
6 8
2 1
9 10
5 10
10 7
10 7
6 8
4 1
4 1
6 8
10 7
5 10
4 1
9 10
8 1
10 7
3 1
9 10
2 1
9 10
9 10
10 7
2 10
6 8
4 1
6 8
4 1
10 7
10 7
2 1
2 1
6 
--- size 131072 (450005 chars):
100000 10
10 7
10 7
4 1
2 10
9 10
2 10
10 1
10 1
2 1
5 10
2 1
10 1
5 10
5 10
10 7
10 1
10 7
6 8
5 10
10 1
8 1
2 10
10 7
8 1
9 10
2 10
2 1
3 1
2 10
9 10
2 10
5 10
5 10
2 10
10 1
2 10
3 1
2 1
3 1
8 1
2 10
5 10
8 1
5 10
5 10
3 1
4 1
6 8
10 7
6 8
10 1
9 10
10 1
3 1
4 1
9 10
6 8
8 1
6 8
9 10
6 8
5 10
2 1

## Program A
```python
n, m = map(int, input().split())
clr = [-1 for i in range(0, n)]
eds = []


def dfs():
    cur = 0
    st = [-1 for i in range(0, n + 1)]
    st[cur] = 0
    cur += 1
    while cur > 0:
        v = st[cur - 1]
        cur -= 1
        for x in g[v]:
            if clr[x] != -1:
                if clr[x] == clr[v]:
                    return False
                continue
            clr[x] = clr[v] ^ 1
            st[cur] = x
            cur += 1
    return True


g = [[] for i in range(0, n)]
for i in range(0, m):
    u, v = map(int, input().split())
    u -= 1
    v -= 1
    g[u].append(v)
    g[v].append(u)
    eds.append((u, v))
clr[0] = 0
if dfs():
    print("YES")
    print("".join("1" if clr[u] < clr[v] else "0" for (u, v) in eds))
else:
    print("NO")
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=158 max_rec=1 
  traced size=2: status=ok lines=272 max_rec=1 
  traced size=4: status=ok lines=311 max_rec=1 
  traced size=8: status=ok lines=452 max_rec=1 
  traced size=16: status=ok lines=585 max_rec=1 
  traced size=32: status=ok lines=1177 max_rec=1 
  traced size=64: status=ok lines=2127 max_rec=1 
  traced size=128: status=ok lines=4031 max_rec=1 
  traced size=256: status=ok lines=7892 max_rec=1 
  traced size=512: status=ok lines=15582 max_rec=1 
  traced size=1024: status=ok lines=30840 max_rec=1 
  traced size=2048: status=ok lines=61575 max_rec=1 
  traced size=4096: status=ok lines=123015 max_rec=1 
  traced size=8192: status=ok lines=245977 max_rec=1 
  traced size=16384: status=ok lines=300136 max_rec=1 
  traced size=32768: status=ok lines=300160 max_rec=1 
  traced size=65536: status=ok lines=300135 max_rec=1 
  traced size=131072: status=ok lines=300114 max_rec=1 
  untraced time (size:seconds): 1:2.86e-05 2:3.20e-05 4:3.34e-05 8:3.76e-05 16:3.83e-05 32:5.58e-05 64:8.41e-05 128:1.58e-04 256:2.81e-04 512:5.47e-04 1024:1.25e-03 2048:2.32e-03 4096:4.60e-03 8192:2.08e-02 16384:2.82e-02 32768:2.37e-02 65536:2.35e-02 131072:2.28e-02


## Program B
```python
graph = [[] for _ in range(200000)]
colors = [0] * 200000
vis = [0] * 200000

def main():
    n, m = map(int, input().split())
    edges = []
    for i in range(m):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        graph[u].append(v)
        graph[v].append(u)
        edges.append((u, v))
    
    colors[0] = 1
    queue = [(0, 1)]
    i = 0
    while i != len(queue):
        for v in graph[queue[i][0]]:
            if not colors[v]:
                colors[v] = 3 - queue[i][1]
                queue.append((v, colors[v]))
        i += 1
    
    ans = ['0'] * m
    for i in range(m):
        if colors[edges[i][0]] == colors[edges[i][1]]:
            print("NO")
            return 0
        if colors[edges[i][0]] == 1:
            ans[i] = '1'
    print("YES")
    print("".join(ans))
    return 0
main()
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=200186 max_rec=1 
  traced size=2: status=ok lines=200194 max_rec=1 
  traced size=4: status=ok lines=200156 max_rec=1 
  traced size=8: status=ok lines=200193 max_rec=1 
  traced size=16: status=ok lines=200132 max_rec=1 
  traced size=32: status=ok lines=200196 max_rec=1 
  traced size=64: status=ok lines=200185 max_rec=1 
  traced size=128: status=ok lines=200157 max_rec=1 
  traced size=256: status=ok lines=200191 max_rec=1 
  traced size=512: status=ok lines=200201 max_rec=1 
  traced size=1024: status=ok lines=200181 max_rec=1 
  traced size=2048: status=ok lines=200165 max_rec=1 
  traced size=4096: status=ok lines=200151 max_rec=1 
  traced size=8192: status=ok lines=200196 max_rec=1 
  traced size=16384: status=ok lines=200172 max_rec=1 
  traced size=32768: status=ok lines=200177 max_rec=1 
  traced size=65536: status=ok lines=200173 max_rec=1 
  traced size=131072: status=ok lines=200169 max_rec=1 
  untraced time (size:seconds): 1:4.54e-02 2:4.63e-02 4:5.04e-02 8:4.76e-02 16:5.33e-02 32:4.73e-02 64:4.49e-02 128:4.20e-02 256:4.72e-02 512:4.98e-02 1024:3.92e-02 2048:4.57e-02 4096:4.38e-02 8192:4.48e-02 16384:4.38e-02 32768:5.57e-02 65536:5.21e-02 131072:4.86e-02


# CASE 4: FALSE_DIFFERENT  (pair 77, task apps/4314, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both drop empty rows and columns and print the remaining grid.
d_phi=0.477  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n^2)|none # none|-|nest2 # -   slope b=1.9263050993284951 (lines 1.9263050993284951, time None)
Fingerprint B: O(n log n)|none # none|-|nest1 # set   slope b=1.2486025134706225 (lines 1.2486025134706225, time None)
Ladder used: 'nat' (the task test inputs themselves, size = number of tokens); sizes [3, 5, 6, 9, 100, 102]

## Task statement (truncated)
There is a grid of squares with H horizontal rows and W vertical columns.
The square at the i-th row from the top and the j-th column from the left is represented as (i, j).
Each square is black or white.
The color of the square is given as an H-by-W matrix (a_{i, j}).
If a_{i, j} is ., the square (i, j) is white; if a_{i, j} is #, the square (i, j) is black.
Snuke is compressing this grid.
He will do so by repeatedly performing the following operation while there is a row or column that consists only of white squares:
 - Operation: choose any one row or column that consists only of white squares, remove it and delete the space between the rows or columns.
It can be shown that the final state of the grid is uniquely determined regardless of what row or column is chosen in each operation.
Find the final state of the grid.

-----Constraints-----
 - 1 \leq H, W \leq 100
 - a_{i, j} is . or #.
 - There is at least one black square in the whole grid.

-----Input-----
Input is given from Standard Input in the following format:
H W
a_{1, 1}...a_{1, W}
:
a_{H, 1}...a_{H, W}

-----Output-----
Print the final state of the grid in the same format as input (without the numbers of rows and columns); see the samples for clarity.

-----Sample Input-----
4 4
##.#
....
##.#
.#.#

-----Sample Output-----
###
###
.##

The second row and the third column in the original grid will be removed.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 3 (6 chars):
1 1
#

--- size 9 (53 chars):
7 6
......
....#.
.#....
..#...
..#...
......
.#..#.

--- size 102 (10108 chars):
100 100
....................................................................................................
....................................................................................................
..........................................................................................

## Program A
```python
h,w=map(int,input().split())
A=[list(input()) for i in range(h)]
answ=[]
ansh=[]
for i in range(h):
  if not all([a=="." for a in A[i]]):
    answ.append(i)
for j in range(w):
  if not all([A[i][j]=="." for i in range(h)]):
    ansh.append(j)
for i in answ:
  for j in ansh:
    print(A[i][j],end="")
  print("\n")
```
Trace of A on ladder 'nat':
  traced size=3: status=ok lines=21 max_rec=0 
  traced size=5: status=ok lines=73 max_rec=0 
  traced size=6: status=ok lines=92 max_rec=0 
  traced size=9: status=ok lines=177 max_rec=0 
  traced size=100: status=ok lines=22748 max_rec=0 
  traced size=102: status=ok lines=20514 max_rec=0 
  untraced time (size:seconds): 3:1.37e-05 5:2.35e-05 6:2.56e-05 9:3.77e-05 100:1.94e-03 102:9.29e-04


## Program B
```python
H, W = map(int, input().split())
A = []
for i in range(H):
    x = input()
    if x.count('#') == 0:
        continue
    A.append(x)

c = set()
for a in A:
    for i in range(W):
        if a[i] == '#':
            c.add(i)

for a in A:
    for i in range(W):
        if i in c:
            print(a[i], end='')
    print()
```
Trace of B on ladder 'nat':
  traced size=3: status=ok lines=21 max_rec=0 
  traced size=5: status=ok lines=81 max_rec=0 
  traced size=6: status=ok lines=102 max_rec=0 
  traced size=9: status=ok lines=200 max_rec=0 
  traced size=100: status=ok lines=16207 max_rec=0 
  traced size=102: status=ok lines=813 max_rec=0 
  untraced time (size:seconds): 3:1.27e-05 5:2.27e-05 6:2.40e-05 9:3.42e-05 100:1.53e-03 102:9.91e-05


# CASE 7: FALSE_DIFFERENT  (pair 120, task apps/4128, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both output (n-1)//2 via parity check on n.
d_phi=0.488  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # set   slope b=0.9627483412863665 (lines 0.9627483412863665, time 0.9574780386625493)
Fingerprint B: O(1)|none # none|-|nest1 # -   slope b=0.02141551897590191 (lines 0.02141551897590191, time None)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
There are two sisters Alice and Betty. You have $n$ candies. You want to distribute these $n$ candies between two sisters in such a way that:  Alice will get $a$ ($a > 0$) candies;  Betty will get $b$ ($b > 0$) candies;  each sister will get some integer number of candies;  Alice will get a greater amount of candies than Betty (i.e. $a > b$);  all the candies will be given to one of two sisters (i.e. $a+b=n$). 

Your task is to calculate the number of ways to distribute exactly $n$ candies between sisters in a way described above. Candies are indistinguishable.

Formally, find the number of ways to represent $n$ as the sum of $n=a+b$, where $a$ and $b$ are positive integers and $a>b$.

You have to answer $t$ independent test cases.


-----Input-----

The first line of the input contains one integer $t$ ($1 \le t \le 10^4$) — the number of test cases. Then $t$ test cases follow.

The only line of a test case contains one integer $n$ ($1 \le n \le 2 \cdot 10^9$) — the number of candies you have.


-----Output-----

For each test case, print the answer — the number of ways to distribute exactly $n$ candies between two sisters in a way described in the problem statement. If there is no way to satisfy all the conditions, print $0$.


-----Example-----
Input
6
7
1
2
3
2000000000
763243547

Output
3
0
0
1
999999999
381621773



-----Note-----

For the test case of the example, the $3$ possible ways to distribute candies are:  $a=6$, $b=1$;  $a=5$, $b=2$;  $a=4$, $b=3$.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (8 chars):
3
1
1
1

--- size 512 (3077 chars):
1536
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
--- size 131072 (400007 chars):
200000
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1

## Program A
```python
from bisect import bisect_left as bl
from bisect import bisect_right as br
from heapq import heappush,heappop
import math
from collections import *
from functools import reduce,cmp_to_key
import sys
input = sys.stdin.readline

M = mod = 998244353
def factors(n):return sorted(set(reduce(list.__add__, ([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0))))
def inv_mod(n):return pow(n, mod - 2, mod)

def li():return [int(i) for i in input().rstrip('\n').split()]
def st():return input().rstrip('\n')
def val():return int(input().rstrip('\n'))
def li2():return [i for i in input().rstrip('\n')]
def li3():return [int(i) for i in input().rstrip('\n')]


for _ in range(val()):
    n = val()
    print(n//2 if n&1 else n//2 - 1)
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=30 max_rec=1 
  traced size=2: status=ok lines=42 max_rec=1 
  traced size=4: status=ok lines=66 max_rec=1 
  traced size=8: status=ok lines=114 max_rec=1 
  traced size=16: status=ok lines=210 max_rec=1 
  traced size=32: status=ok lines=402 max_rec=1 
  traced size=64: status=ok lines=786 max_rec=1 
  traced size=128: status=ok lines=1554 max_rec=1 
  traced size=256: status=ok lines=3090 max_rec=1 
  traced size=512: status=ok lines=6162 max_rec=1 
  traced size=1024: status=ok lines=12306 max_rec=1 
  traced size=2048: status=ok lines=24594 max_rec=1 
  traced size=4096: status=ok lines=49170 max_rec=1 
  traced size=8192: status=ok lines=98322 max_rec=1 
  traced size=16384: status=ok lines=196626 max_rec=1 
  traced size=32768: status=ok lines=393234 max_rec=1 
  untraced time (size:seconds): 1:1.73e-05 2:2.05e-05 4:2.80e-05 8:4.06e-05 16:6.63e-05 32:1.18e-04 64:2.18e-04 128:4.21e-04 256:8.25e-04 512:1.64e-03 1024:3.28e-03 2048:6.62e-03 4096:1.31e-02 8192:2.62e-02 16384:5.26e-02 32768:1.06e-01 65536:2.15e-01 131072:2.20e-01


## Program B
```python
from bisect import *
from collections import *
from itertools import *
import functools
import sys
import math
from decimal import *
from copy import *
from heapq import *
from fractions import *
getcontext().prec = 30
MAX = sys.maxsize
MAXN = 1000010
MOD = 10**9+7
spf = [i for i in range(MAXN)]
spf[0]=spf[1] = -1
def sieve():
    for i in range(2,MAXN,2):
        spf[i] = 2
    for i in range(3,int(MAXN**0.5)+1):
        if spf[i]==i:
            for j in range(i*i,MAXN,i):
                if spf[j]==j:
                    spf[j]=i
def fib(n,m):
    if n == 0:
        return [0, 1]
    else:
        a, b = fib(n // 2)
        c = ((a%m) * ((b%m) * 2 - (a%m)))%m
        d = ((a%m) * (a%m))%m + ((b)%m * (b)%m)%m
        if n % 2 == 0:
            return [c, d]
        else:
            return [d, c + d]
 
def charIN(x= ' '):
    return(sys.stdin.readline().strip().split(x))
 
def arrIN(x = ' '):
    return list(map(int,sys.stdin.readline().strip().split(x)))
 
def ncr(n,r):
    num=den=1
    for i in range(r):
        num = (num*(n-i))%MOD
        den = (den*(i+1))%MOD
 
    return (num*(pow(den,MOD-2,MOD)))%MOD
 
def flush():
    return sys.stdout.flush()
 
'''*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*'''
for _ in range(int(input())):
    n = int(input())
    if n%2:
        print(n//2)
    else:
        print(n//2-1)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=1000046 max_rec=0 
  traced size=2: status=ok lines=1000058 max_rec=0 
  traced size=4: status=ok lines=1000082 max_rec=0 
  traced size=8: status=ok lines=1000130 max_rec=0 
  traced size=16: status=ok lines=1000226 max_rec=0 
  traced size=32: status=ok lines=1000418 max_rec=0 
  traced size=64: status=ok lines=1000802 max_rec=0 
  traced size=128: status=ok lines=1001570 max_rec=0 
  traced size=256: status=ok lines=1003106 max_rec=0 
  traced size=512: status=ok lines=1006178 max_rec=0 
  traced size=1024: status=ok lines=1012322 max_rec=0 
  traced size=2048: status=ok lines=1024610 max_rec=0 
  traced size=4096: status=ok lines=1049186 max_rec=0 
  traced size=8192: status=ok lines=1098338 max_rec=0 
  traced size=16384: status=ok lines=1196642 max_rec=0 
  traced size=32768: status=ok lines=1393250 max_rec=0 
  untraced time (size:seconds): 1:4.11e-02 2:4.03e-02 4:4.07e-02 8:4.05e-02 16:4.03e-02 32:4.02e-02 64:4.06e-02 128:4.11e-02 256:4.16e-02 512:4.26e-02 1024:4.54e-02 2048:5.03e-02


# CASE 10: MISSED_DIFFERENT  (pair 0, task apps/4388, io=stdio)
LLM labeller said: same=0 level=other confidence=high reason: A swaps digits 1/9 via chained string replace; B extracts each digit arithmetically with modulo and adds/subtracts 8 per place.
d_phi=0.000  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(1)|none # none|-|nest0 # -   slope b=-1.1669088310189271e-17 (lines -1.1669088310189271e-17, time None)
Fingerprint B: O(1)|none # none|-|nest0 # -   slope b=-8.913283141067692e-17 (lines -8.913283141067692e-17, time None)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

## Task statement (truncated)
Cat Snuke is learning to write characters.
Today, he practiced writing digits 1 and 9, but he did it the other way around.
You are given a three-digit integer n written by Snuke.
Print the integer obtained by replacing each digit 1 with 9 and each digit 9 with 1 in n.

-----Constraints-----
 - 111 \leq n \leq 999
 - n is an integer consisting of digits 1 and 9.

-----Input-----
Input is given from Standard Input in the following format:
n

-----Output-----
Print the integer obtained by replacing each occurrence of 1 with 9 and each occurrence of 9 with 1 in n.

-----Sample Input-----
119

-----Sample Output-----
991

Replace the 9 in the ones place with 1, the 1 in the tens place with 9 and the 1 in the hundreds place with 9. The answer is 991.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (4 chars):
191

--- size 256 (6 chars):
48896

--- size 32768 (8 chars):
6258688


## Program A
```python
#ABC111A
n = input()
print(n.replace("1","x").replace("9","1").replace("x","9"))
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=2 max_rec=0 
  traced size=2: status=ok lines=2 max_rec=0 
  traced size=4: status=ok lines=2 max_rec=0 
  traced size=8: status=ok lines=2 max_rec=0 
  traced size=16: status=ok lines=2 max_rec=0 
  traced size=32: status=ok lines=2 max_rec=0 
  traced size=64: status=ok lines=2 max_rec=0 
  traced size=128: status=ok lines=2 max_rec=0 
  traced size=256: status=ok lines=2 max_rec=0 
  traced size=512: status=ok lines=2 max_rec=0 
  traced size=1024: status=ok lines=2 max_rec=0 
  traced size=2048: status=ok lines=2 max_rec=0 
  traced size=4096: status=ok lines=2 max_rec=0 
  traced size=8192: status=ok lines=2 max_rec=0 
  traced size=16384: status=ok lines=2 max_rec=0 
  traced size=32768: status=ok lines=2 max_rec=0 
  untraced time (size:seconds): 1:7.46e-06 2:7.18e-06 4:7.18e-06 8:7.37e-06 16:7.07e-06 32:7.20e-06 64:7.13e-06 128:7.14e-06 256:7.20e-06 512:7.28e-06 1024:7.36e-06 2048:7.38e-06 4096:7.29e-06 8192:7.31e-06 16384:7.46e-06 32768:7.28e-06


## Program B
```python
n=int(input())
if (n-n%100)/100==1:
    n+=800
else:
    n-=800

if (n%100-(n%100)%10)/10==1:
    n+=80
else:
    n-=80

if n%10==1:
    n+=8
else:
    n-=8
print(n)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=8 max_rec=0 
  traced size=2: status=ok lines=8 max_rec=0 
  traced size=4: status=ok lines=8 max_rec=0 
  traced size=8: status=ok lines=8 max_rec=0 
  traced size=16: status=ok lines=8 max_rec=0 
  traced size=32: status=ok lines=8 max_rec=0 
  traced size=64: status=ok lines=8 max_rec=0 
  traced size=128: status=ok lines=8 max_rec=0 
  traced size=256: status=ok lines=8 max_rec=0 
  traced size=512: status=ok lines=8 max_rec=0 
  traced size=1024: status=ok lines=8 max_rec=0 
  traced size=2048: status=ok lines=8 max_rec=0 
  traced size=4096: status=ok lines=8 max_rec=0 
  traced size=8192: status=ok lines=8 max_rec=0 
  traced size=16384: status=ok lines=8 max_rec=0 
  traced size=32768: status=ok lines=8 max_rec=0 
  untraced time (size:seconds): 1:8.80e-06 2:8.87e-06 4:8.86e-06 8:8.58e-06 16:8.89e-06 32:8.75e-06 64:8.81e-06 128:8.75e-06 256:8.75e-06 512:8.79e-06 1024:8.85e-06 2048:8.89e-06 4096:8.88e-06 8192:8.66e-06 16384:8.61e-06 32768:8.68e-06


# CASE 13: MISSED_DIFFERENT  (pair 73, task apps/4206, io=stdio)
LLM labeller said: same=0 level=paradigm confidence=high reason: A: greedy with state tracking remainders mod 3 to cut; B: DP over residue classes with max.
d_phi=0.001  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(log n)|none # none|-|nest1 # -   slope b=0.08433028671397882 (lines 0.08433028671397882, time None)
Fingerprint B: O(log n)|none # none|-|nest1 # -   slope b=0.08122964965164266 (lines 0.08122964965164266, time None)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
Polycarp likes numbers that are divisible by 3.

He has a huge number $s$. Polycarp wants to cut from it the maximum number of numbers that are divisible by $3$. To do this, he makes an arbitrary number of vertical cuts between pairs of adjacent digits. As a result, after $m$ such cuts, there will be $m+1$ parts in total. Polycarp analyzes each of the obtained numbers and finds the number of those that are divisible by $3$.

For example, if the original number is $s=3121$, then Polycarp can cut it into three parts with two cuts: $3|1|21$. As a result, he will get two numbers that are divisible by $3$.

Polycarp can make an arbitrary number of vertical cuts, where each cut is made between a pair of adjacent digits. The resulting numbers cannot contain extra leading zeroes (that is, the number can begin with 0 if and only if this number is exactly one character '0'). For example, 007, 01 and 00099 are not valid numbers, but 90, 0 and 10001 are valid.

What is the maximum number of numbers divisible by $3$ that Polycarp can obtain?


-----Input-----

The first line of the input contains a positive integer $s$. The number of digits of the number $s$ is between $1$ and $2\cdot10^5$, inclusive. The first (leftmost) digit is not equal to 0.


-----Output-----

Print the maximum number of numbers divisible by $3$ that Polycarp can get by making vertical cuts in the given number $s$.


-----Examples-----
Input
3121

Output
2

Input
6

Output
1

Input
1000000000000000000000000000000000

Output
33

Input
201920181

Output
4



-----Note-----

In the first example, an example set of optimal cuts on the number is 3|1|21.

In the second example, you do not need to make any cuts. The specified number 6 forms one number that is divisible by $3$.

In the third example, cuts must be made

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (3 chars):
12

--- size 512 (5 chars):
6144

--- size 131072 (8 chars):
1572864


## Program A
```python
s = input()
ost = []
for i in map(int,s):
    ost += [i%3]
now = 0
last = -1
answer = 0
for i in ost:
    if i == 0:
        now = []
        answer += 1
    else:
        if now == 2:
            now = 0
            answer += 1
        elif now == 1:
            if last != i:
                answer += 1
                now = 0
            else:
                now = 2
        else:
            now = 1
            last = i
print(answer)
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=25 max_rec=0 
  traced size=2: status=ok lines=25 max_rec=0 
  traced size=4: status=ok lines=25 max_rec=0 
  traced size=8: status=ok lines=20 max_rec=0 
  traced size=16: status=ok lines=30 max_rec=0 
  traced size=32: status=ok lines=31 max_rec=0 
  traced size=64: status=ok lines=30 max_rec=0 
  traced size=128: status=ok lines=37 max_rec=0 
  traced size=256: status=ok lines=37 max_rec=0 
  traced size=512: status=ok lines=37 max_rec=0 
  traced size=1024: status=ok lines=48 max_rec=0 
  traced size=2048: status=ok lines=48 max_rec=0 
  traced size=4096: status=ok lines=47 max_rec=0 
  traced size=8192: status=ok lines=42 max_rec=0 
  traced size=16384: status=ok lines=48 max_rec=0 
  traced size=32768: status=ok lines=49 max_rec=0 
  traced size=65536: status=ok lines=53 max_rec=0 
  traced size=131072: status=ok lines=64 max_rec=0 
  untraced time (size:seconds): 1:1.07e-05 2:1.07e-05 4:1.10e-05 8:1.07e-05 16:1.13e-05 32:1.15e-05 64:1.12e-05 128:1.19e-05 256:1.20e-05 512:1.22e-05 1024:1.20e-05 2048:1.15e-05 4096:1.17e-05 8192:1.14e-05 16384:1.19e-05 32768:1.21e-05 65536:1.27e-05 131072:1.32e-05


## Program B
```python
res_plain = 0
res_1 = -200000
res_2 = -200000
s = input()
for c in s:
	if c in '147':
		res_plain, res_1, res_2 = res_2, res_plain, res_1
	elif c in '258':
		res_plain, res_1, res_2 = res_1, res_2, res_plain
	res_plain = max(res_1, res_2, res_plain+1)
print(res_plain)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=15 max_rec=0 
  traced size=2: status=ok lines=15 max_rec=0 
  traced size=4: status=ok lines=15 max_rec=0 
  traced size=8: status=ok lines=14 max_rec=0 
  traced size=16: status=ok lines=19 max_rec=0 
  traced size=32: status=ok lines=19 max_rec=0 
  traced size=64: status=ok lines=19 max_rec=0 
  traced size=128: status=ok lines=23 max_rec=0 
  traced size=256: status=ok lines=23 max_rec=0 
  traced size=512: status=ok lines=22 max_rec=0 
  traced size=1024: status=ok lines=30 max_rec=0 
  traced size=2048: status=ok lines=28 max_rec=0 
  traced size=4096: status=ok lines=28 max_rec=0 
  traced size=8192: status=ok lines=27 max_rec=0 
  traced size=16384: status=ok lines=31 max_rec=0 
  traced size=32768: status=ok lines=31 max_rec=0 
  traced size=65536: status=ok lines=32 max_rec=0 
  traced size=131072: status=ok lines=37 max_rec=0 
  untraced time (size:seconds): 1:8.98e-06 2:9.11e-06 4:9.09e-06 8:8.54e-06 16:9.49e-06 32:9.46e-06 64:9.35e-06 128:9.56e-06 256:9.35e-06 512:9.76e-06 1024:1.02e-05 2048:1.02e-05 4096:1.01e-05 8192:9.84e-06 16384:9.93e-06 32768:1.00e-05 65536:1.03e-05 131072:1.11e-05


# CASE 16: MISSED_DIFFERENT  (pair 113, task apps/4452, io=stdio)
LLM labeller said: same=0 level=other confidence=low reason: A extracts nonzero digits via string reversal and zero padding; B extracts digits arithmetically with n%10 and powers of ten.
d_phi=0.000  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest2 # -   slope b=1.004818005551613 (lines 1.004818005551613, time 0.986041336444217)
Fingerprint B: O(n)|none # none|-|nest2 # -   slope b=1.0057784808512862 (lines 1.0057784808512862, time 0.9855657753810438)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
A positive (strictly greater than zero) integer is called round if it is of the form d00...0. In other words, a positive integer is round if all its digits except the leftmost (most significant) are equal to zero. In particular, all numbers from $1$ to $9$ (inclusive) are round.

For example, the following numbers are round: $4000$, $1$, $9$, $800$, $90$. The following numbers are not round: $110$, $707$, $222$, $1001$.

You are given a positive integer $n$ ($1 \le n \le 10^4$). Represent the number $n$ as a sum of round numbers using the minimum number of summands (addends). In other words, you need to represent the given number $n$ as a sum of the least number of terms, each of which is a round number.


-----Input-----

The first line contains an integer $t$ ($1 \le t \le 10^4$) — the number of test cases in the input. Then $t$ test cases follow.

Each test case is a line containing an integer $n$ ($1 \le n \le 10^4$).


-----Output-----

Print $t$ answers to the test cases. Each answer must begin with an integer $k$ — the minimum number of summands. Next, $k$ terms must follow, each of which is a round number, and their sum is $n$. The terms can be printed in any order. If there are several answers, print any of them.


-----Example-----
Input
5
5009
7
9876
10000
10

Output
2
5000 9
1
7 
4
800 70 6 9000 
1
10000 
1
10

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (9 chars):
2
954
18

--- size 512 (3592 chars):
1024
954
954
954
18
18
18
954
18
18
18
954
954
18
18
954
954
18
18
18
18
18
18
954
18
954
954
18
954
18
954
18
18
954
954
18
954
18
18
18
954
18
954
954
18
954
954
954
18
18
18
18
954
18
954
18
18
954
18
954
954
18
954
954
954
18
954
954
18
18
18
954
954
954
18
954
18
18
954
954
18
954
18
954
18
18

--- size 131072 (700168 chars):
200000
18
18
954
954
954
954
954
18
18
954
18
954
18
954
954
18
954
18
18
954
954
18
18
954
954
954
954
954
954
18
18
18
18
954
18
18
954
18
954
954
954
954
18
954
954
18
954
954
954
18
18
954
954
954
18
954
954
954
954
18
954
954
18
18
18
18
18
18
18
954
18
18
954
954
18
954
954
18
18
954
18
954
95

## Program A
```python
for _ in range(int(input())):
    s = input()

    print(len(s.replace('0', '')))

    for i, j in enumerate(s[::-1]):
        if j != '0':
            print(j + '0' * i, end=' ')

    print()
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=26 max_rec=0 
  traced size=2: status=ok lines=48 max_rec=0 
  traced size=4: status=ok lines=95 max_rec=0 
  traced size=8: status=ok lines=198 max_rec=0 
  traced size=16: status=ok lines=392 max_rec=0 
  traced size=32: status=ok lines=774 max_rec=0 
  traced size=64: status=ok lines=1604 max_rec=0 
  traced size=128: status=ok lines=3162 max_rec=0 
  traced size=256: status=ok lines=6389 max_rec=0 
  traced size=512: status=ok lines=12810 max_rec=0 
  traced size=1024: status=ok lines=25583 max_rec=0 
  traced size=2048: status=ok lines=51201 max_rec=0 
  traced size=4096: status=ok lines=102524 max_rec=0 
  traced size=8192: status=ok lines=204879 max_rec=0 
  traced size=16384: status=ok lines=409931 max_rec=0 
  untraced time (size:seconds): 1:1.87e-05 2:2.57e-05 4:4.18e-05 8:7.71e-05 16:1.45e-04 32:2.78e-04 64:5.60e-04 128:1.10e-03 256:2.23e-03 512:4.47e-03 1024:8.89e-03 2048:1.77e-02 4096:3.54e-02 8192:7.06e-02 16384:1.41e-01 32768:2.82e-01 65536:5.79e-01 131072:8.84e-01


## Program B
```python


for _ in range(int(input())):
	s=input()
	print(len(s)-s.count('0'))

	n=int(s)
	pw=1
	while(n):
		if(n%10):
			print(pw*(n%10),end=" ")
		n//=10
		pw*=10
	print()
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=40 max_rec=0 
  traced size=2: status=ok lines=74 max_rec=0 
  traced size=4: status=ok lines=147 max_rec=0 
  traced size=8: status=ok lines=308 max_rec=0 
  traced size=16: status=ok lines=610 max_rec=0 
  traced size=32: status=ok lines=1204 max_rec=0 
  traced size=64: status=ok lines=2502 max_rec=0 
  traced size=128: status=ok lines=4928 max_rec=0 
  traced size=256: status=ok lines=9965 max_rec=0 
  traced size=512: status=ok lines=19984 max_rec=0 
  traced size=1024: status=ok lines=39907 max_rec=0 
  traced size=2048: status=ok lines=79873 max_rec=0 
  traced size=4096: status=ok lines=159950 max_rec=0 
  traced size=8192: status=ok lines=319619 max_rec=0 
  traced size=16384: status=ok lines=639527 max_rec=0 
  untraced time (size:seconds): 1:1.85e-05 2:2.59e-05 4:4.36e-05 8:8.08e-05 16:1.51e-04 32:2.90e-04 64:5.94e-04 128:1.16e-03 256:2.34e-03 512:4.81e-03 1024:9.46e-03 2048:1.89e-02 4096:3.76e-02 8192:7.51e-02 16384:1.50e-01 32768:3.08e-01 65536:6.06e-01 131072:9.20e-01


# CASE 19: MISSED_DIFFERENT  (pair 165, task apps/4151, io=stdio)
LLM labeller said: same=0 level=other confidence=low reason: A uses first/last occurrence intervals with a difference array and multiplies 2 per free boundary; B counts merged-component starts with a sweep and outputs 2^(count-1).
d_phi=0.080  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # dict   slope b=1.001830589711666 (lines 1.001830589711666, time 1.0114539290009212)
Fingerprint B: O(n)|none # none|-|nest1 # dict,set   slope b=0.9745037925660703 (lines 0.9745037925660703, time 1.0327900936366188)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

## Task statement (truncated)
You are given an array $a$ consisting of $n$ integers. Let's denote monotonic renumeration of array $a$ as an array $b$ consisting of $n$ integers such that all of the following conditions are met:

  $b_1 = 0$;  for every pair of indices $i$ and $j$ such that $1 \le i, j \le n$, if $a_i = a_j$, then $b_i = b_j$ (note that if $a_i \ne a_j$, it is still possible that $b_i = b_j$);  for every index $i \in [1, n - 1]$ either $b_i = b_{i + 1}$ or $b_i + 1 = b_{i + 1}$. 

For example, if $a = [1, 2, 1, 2, 3]$, then two possible monotonic renumerations of $a$ are $b = [0, 0, 0, 0, 0]$ and $b = [0, 0, 0, 0, 1]$.

Your task is to calculate the number of different monotonic renumerations of $a$. The answer may be large, so print it modulo $998244353$.


-----Input-----

The first line contains one integer $n$ ($2 \le n \le 2 \cdot 10^5$) — the number of elements in $a$.

The second line contains $n$ integers $a_1, a_2, \dots, a_n$ ($1 \le a_i \le 10^9$).


-----Output-----

Print one integer — the number of different monotonic renumerations of $a$, taken modulo $998244353$.


-----Examples-----
Input
5
1 2 1 2 3

Output
2

Input
2
100 1

Output
2

Input
4
1 3 3 7

Output
4

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (293 chars):
100
23 20 87 49 15 59 70 18 67 47 79 19 7 6 88 40 33 7 37 45 75 16 19 43 6 96 77 79 69 21 54 46 84 67 49 4 97 52 60 45 47 90 33 79 94 4 64 13 56 57 96 33 7 83 17 92 5 18 83 93 87 63 10 33 38 65 85 98 73 47 19 15 92 64 72 18 23 9 33 18 81 35 100 85 70 7 85 35 9 19 44 89 34 48 20 64 70 26 5 95

--- size 32 (9475 chars):
3200
94 44 86 69 86 48 12 67 43 54 25 48 60 47 92 81 79 90 94 14 34 64 6 44 96 91 33 33 13 50 62 62 34 25 87 51 59 51 29 77 92 54 30 42 50 48 71 89 56 63 38 20 52 66 45 95 34 73 27 71 25 62 24 36 42 99 31 64 90 79 52 78 96 68 99 28 81 33 37 72 84 51 88 64 76 12 54 49 50 94 38 66 44 11 25 52 12 37 22
--- size 1024 (302017 chars):
102400
57 89 72 35 97 48 24 63 43 16 80 10 41 46 25 92 91 60 46 90 12 90 69 71 80 21 83 27 10 8 89 15 91 48 60 44 37 14 14 4 75 99 55 45 100 14 68 87 99 67 32 58 71 87 20 59 65 22 54 63 9 88 96 94 21 92 11 59 32 46 52 86 56 53 23 42 41 49 66 62 76 12 97 74 23 47 85 57 83 85 42 65 98 14 5 33 73 46 89

## Program A
```python
from sys import stdin, stdout
from math import *
from heapq import *
from collections import *

def main():
    n=int(stdin.readline())
    a=[int(x) for x in stdin.readline().split()]
    b=[2]*(n+2)
    maxR={}
    minL={}
    for i in range(n):
        x=a[i]
        maxR[x]=i
        minL[x]=minL.get(x,i)
    f=[0]*(n+2)
    for i in range(n):
        x=a[i]
        l=minL[x]
        r=maxR[x]
        if (l<r):
            if (r==l-1):
                b[r]=1
            else:
                f[l+1]=f[l+1]+1
                f[r+1]=f[r+1]-1
    res=1
    for i in range(1,n):
        f[i]=f[i]+f[i-1]
        if (f[i]>0):
            b[i]=1
        res=(res*b[i])%998244353 
    stdout.write(str(res))
    return 0

def __starting_point():
    main()
__starting_point()
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=1700 max_rec=1 
  traced size=2: status=ok lines=3528 max_rec=1 
  traced size=4: status=ok lines=7206 max_rec=1 
  traced size=8: status=ok lines=14415 max_rec=1 
  traced size=16: status=ok lines=28815 max_rec=1 
  traced size=32: status=ok lines=57615 max_rec=1 
  traced size=64: status=ok lines=115215 max_rec=1 
  traced size=128: status=ok lines=230415 max_rec=1 
  traced size=256: status=ok lines=460815 max_rec=1 
  traced size=512: status=ok lines=921615 max_rec=1 
  traced size=1024: status=cap lines=1500001 max_rec=1 
  untraced time (size:seconds): 1:7.39e-05 2:1.21e-04 4:2.40e-04 8:4.70e-04 16:9.18e-04 32:1.80e-03 64:3.62e-03 128:7.20e-03 256:1.43e-02 512:2.92e-02 1024:6.07e-02


## Program B
```python
n=int(input())
a=[int(i) for i in input().split()]
s=list(set(a))
N=len(s)
d={}
l={}
for i in range(N):
	d[s[i]]=0
	l[s[i]]=0
for i in range(n):
	d[a[i]]+=1
ans=0
#print(d)
cting=0
for i in range(n):
	temp=d[a[i]]
	if temp>1 and l[a[i]]==0:
		l[a[i]]=1
		cting+=1
		if cting==1:
			ans+=1
		d[a[i]]-=1
			
	elif l[a[i]]==1:
		d[a[i]]-=1
		if temp-1==0:
			cting-=1
	
	elif cting==0:
		ans+=1
		
print(pow(2,ans-1,998244353))
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=1110 max_rec=0 
  traced size=2: status=ok lines=2156 max_rec=0 
  traced size=4: status=ok lines=4084 max_rec=0 
  traced size=8: status=ok lines=7698 max_rec=0 
  traced size=16: status=ok lines=14898 max_rec=0 
  traced size=32: status=ok lines=29298 max_rec=0 
  traced size=64: status=ok lines=58098 max_rec=0 
  traced size=128: status=ok lines=115698 max_rec=0 
  traced size=256: status=ok lines=230898 max_rec=0 
  traced size=512: status=ok lines=461298 max_rec=0 
  traced size=1024: status=ok lines=922098 max_rec=0 
  untraced time (size:seconds): 1:9.13e-05 2:1.61e-04 4:2.97e-04 8:5.52e-04 16:1.07e-03 32:2.09e-03 64:4.17e-03 128:8.26e-03 256:1.71e-02 512:3.54e-02 1024:7.50e-02
