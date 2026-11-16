# CASE 0: FALSE_DIFFERENT  (pair 10, task apps/4335, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both check n even and first half equals second half.
d_phi=0.391  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest1 # -   slope b=0.9971362818160899 (lines 0.9971362818160899, time 1.0028020985231476)
Fingerprint B: O(1)|none # none|-|nest0 # -   slope b=-6.339431480201137e-17 (lines -6.339431480201137e-17, time None)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

## Task statement (truncated)
Given are a positive integer N and a string S of length N consisting of lowercase English letters.
Determine whether the string is a concatenation of two copies of some string.
That is, determine whether there is a string T such that S = T + T.

-----Constraints-----
 - 1 \leq N \leq 100
 - S consists of lowercase English letters.
 - |S| = N

-----Input-----
Input is given from Standard Input in the following format:
N
S

-----Output-----
If S is a concatenation of two copies of some string, print Yes; otherwise, print No.

-----Sample Input-----
6
abcabc

-----Sample Output-----
Yes

Let T =  abc, and S = T + T.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (103 chars):
99
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb

--- size 32 (3174 chars):
3168
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
--- size 1024 (101384 chars):
101376
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb

## Program A
```python
n=int(input())
s=input()
cnt = 0

if n%2 == 1:
    print('No')

else :
    for i in range(n//2):
        if s[i] == s[i+n//2]:
            cnt += 1

    if cnt == n//2:
        print('Yes')
    else :
        print('No')
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=5 max_rec=0 
  traced size=2: status=ok lines=304 max_rec=0 
  traced size=4: status=ok lines=601 max_rec=0 
  traced size=8: status=ok lines=1195 max_rec=0 
  traced size=16: status=ok lines=2383 max_rec=0 
  traced size=32: status=ok lines=4759 max_rec=0 
  traced size=64: status=ok lines=9511 max_rec=0 
  traced size=128: status=ok lines=19015 max_rec=0 
  traced size=256: status=ok lines=38023 max_rec=0 
  traced size=512: status=ok lines=76039 max_rec=0 
  traced size=1024: status=ok lines=152071 max_rec=0 
  untraced time (size:seconds): 1:9.13e-06 2:2.50e-05 4:4.30e-05 8:8.59e-05 16:1.66e-04 32:3.28e-04 64:6.50e-04 128:1.31e-03 256:2.62e-03 512:5.26e-03 1024:1.06e-02


## Program B
```python
n = int(input())
s = input()
print('Yes' if n % 2 == 0 and s[:n//2] == s[n//2:] else 'No')
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=3 max_rec=0 
  traced size=2: status=ok lines=3 max_rec=0 
  traced size=4: status=ok lines=3 max_rec=0 
  traced size=8: status=ok lines=3 max_rec=0 
  traced size=16: status=ok lines=3 max_rec=0 
  traced size=32: status=ok lines=3 max_rec=0 
  traced size=64: status=ok lines=3 max_rec=0 
  traced size=128: status=ok lines=3 max_rec=0 
  traced size=256: status=ok lines=3 max_rec=0 
  traced size=512: status=ok lines=3 max_rec=0 
  traced size=1024: status=ok lines=3 max_rec=0 
  untraced time (size:seconds): 1:8.01e-06 2:8.49e-06 4:8.67e-06 8:9.15e-06 16:9.56e-06 32:9.78e-06 64:1.02e-05 128:1.40e-05 256:1.83e-05 512:2.69e-05 1024:4.35e-05


# CASE 3: FALSE_DIFFERENT  (pair 71, task apps/4014, io=stdio)
LLM labeller said: same=1 level=None confidence=low reason: Both greedy by earliest exam deadline assigning preparation days (A day-by-day, B exam-by-exam sorted by deadline).
d_phi=0.431  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest2 # sort   slope b=0.9461828082961858 (lines 0.9461828082961858, time 1.059093936615268)
Fingerprint B: O(n log n)|none # none|-|nest1 # bisect   slope b=1.39438695388536 (lines 0.7859312621494394, time 1.39438695388536)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
Petya studies at university. The current academic year finishes with $n$ special days. Petya needs to pass $m$ exams in those special days. The special days in this problem are numbered from $1$ to $n$.

There are three values about each exam:  $s_i$ — the day, when questions for the $i$-th exam will be published,  $d_i$ — the day of the $i$-th exam ($s_i < d_i$),  $c_i$ — number of days Petya needs to prepare for the $i$-th exam. For the $i$-th exam Petya should prepare in days between $s_i$ and $d_i-1$, inclusive. 

There are three types of activities for Petya in each day: to spend a day doing nothing (taking a rest), to spend a day passing exactly one exam or to spend a day preparing for exactly one exam. So he can't pass/prepare for multiple exams in a day. He can't mix his activities in a day. If he is preparing for the $i$-th exam in day $j$, then $s_i \le j < d_i$.

It is allowed to have breaks in a preparation to an exam and to alternate preparations for different exams in consecutive days. So preparation for an exam is not required to be done in consecutive days.

Find the schedule for Petya to prepare for all exams and pass them, or report that it is impossible.


-----Input-----

The first line contains two integers $n$ and $m$ $(2 \le n \le 100, 1 \le m \le n)$ — the number of days and the number of exams.

Each of the following $m$ lines contains three integers $s_i$, $d_i$, $c_i$ $(1 \le s_i < d_i \le n, 1 \le c_i \le n)$ — the day, when questions for the $i$-th exam will be given, the day of the $i$-th exam, number of days Petya needs to prepare for the $i$-th exam. 

Guaranteed, that all the exams will be in different days. Questions for different exams can be given in the same day. It is possible that, in the day of some exam, the questions for other e

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (57 chars):
100 6
3 43 40
46 86 24
38 78 5
51 91 8
59 99 12
60 100 2

--- size 512 (26117 chars):
100 3072
46 86 24
3 43 40
3 43 40
51 91 8
59 99 12
59 99 12
51 91 8
51 91 8
3 43 40
38 78 5
38 78 5
59 99 12
51 91 8
60 100 2
46 86 24
46 86 24
60 100 2
38 78 5
59 99 12
38 78 5
3 43 40
60 100 2
3 43 40
38 78 5
51 91 8
38 78 5
38 78 5
38 78 5
60 100 2
59 99 12
38 78 5
59 99 12
3 43 40
59 99 12
51 91
--- size 131072 (566886 chars):
100 66666
38 78 5
38 78 5
60 100 2
59 99 12
46 86 24
3 43 40
46 86 24
46 86 24
46 86 24
51 91 8
59 99 12
51 91 8
46 86 24
59 99 12
59 99 12
38 78 5
46 86 24
60 100 2
38 78 5
3 43 40
59 99 12
46 86 24
51 91 8
46 86 24
38 78 5
51 91 8
3 43 40
46 86 24
51 91 8
38 78 5
46 86 24
3 43 40
46 86 24
59 99 12

## Program A
```python
T = input().split(' ')
n = int(T[0])
m = int(T[1])
L = [0] * n
M = []
D = [0] * m
F = [0] * m
for i in range(m):
    S = input().split(' ')
    a = int(S[0])
    b = int(S[1])
    c = int(S[2])
    L[b-1] = m+1
    F[i] = b-1
    M.append((a-1, b-2, i+1))
    D[i] = c
M.sort()
for i in range(n):
    if L[i] == 0:
        G = []
        for j in range(len(M)):
            if M[j][0]<=i:
                G.append((M[j][1], M[j][2]))
        G.sort()
        for k in range(len(G)):
            if D[G[k][1]-1] > 0 and F[G[k][1]-1]>i:
                D[G[k][1]-1]-=1
                L[i] = G[k][1]
                break
b = True
for j in range(len(D)):
    if D[j] > 0:
        b = False
if b:
    for i in range(n-1):
        print(L[i], end=' ')
    print(L[n-1])
else:
    print(-1)
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=2946 max_rec=0 
  traced size=2: status=ok lines=4902 max_rec=0 
  traced size=4: status=ok lines=8386 max_rec=0 
  traced size=8: status=ok lines=13977 max_rec=0 
  traced size=16: status=ok lines=29007 max_rec=0 
  traced size=32: status=ok lines=53854 max_rec=0 
  traced size=64: status=ok lines=110545 max_rec=0 
  traced size=128: status=ok lines=215789 max_rec=0 
  traced size=256: status=ok lines=432826 max_rec=0 
  traced size=512: status=ok lines=868318 max_rec=0 
  traced size=1024: status=cap lines=1500001 max_rec=0 
  untraced time (size:seconds): 1:2.84e-04 2:3.55e-04 4:5.92e-04 8:9.10e-04 16:1.99e-03 32:3.57e-03 64:7.76e-03 128:1.52e-02 256:3.09e-02 512:6.60e-02 1024:1.37e-01 2048:2.92e-01 4096:6.03e-01 8192:1.29e+00


## Program B
```python
import bisect
n,m=list(map(int,input().split()))
a=[]
b=[]
for i in range(m):
    s,d,c=list(map(int,input().split()))
    if c>d-s+1:
        print(-1)
        quit()
    l=bisect.bisect_left(b,d)
    a.insert(l,[s,d,c,i+1])
    b.insert(l,d)
ds=list('0' for i in range(n))
for i in range(m):
    s,d,c,mi=a[i]
    c0=0
    for j in range(s,d):
        if ds[j-1]=='0':
            ds[j-1]=str(mi)
            c0+=1
        if c0>=c:
            break
    if c0<c:
        print(-1)
        quit()
    ds[d-1]=str(m+1)
print(' '.join(ds))
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=915 max_rec=0 
  traced size=2: status=ok lines=512 max_rec=0 
  traced size=4: status=ok lines=584 max_rec=0 
  traced size=8: status=ok lines=1255 max_rec=0 
  traced size=16: status=ok lines=1016 max_rec=0 
  traced size=32: status=ok lines=1592 max_rec=0 
  traced size=64: status=ok lines=2744 max_rec=0 
  traced size=128: status=ok lines=5048 max_rec=0 
  traced size=256: status=ok lines=9656 max_rec=0 
  traced size=512: status=ok lines=18872 max_rec=0 
  traced size=1024: status=ok lines=37304 max_rec=0 
  traced size=2048: status=ok lines=74168 max_rec=0 
  traced size=4096: status=ok lines=147896 max_rec=0 
  traced size=8192: status=ok lines=295352 max_rec=0 
  untraced time (size:seconds): 1:6.75e-05 2:5.74e-05 4:7.85e-05 8:1.46e-04 16:2.07e-04 32:3.80e-04 64:7.40e-04 128:1.55e-03 256:3.31e-03 512:7.62e-03 1024:1.85e-02 2048:5.11e-02 4096:1.55e-01 8192:5.25e-01


# CASE 6: FALSE_DIFFERENT  (pair 118, task apps/4077, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both count subarrays with median m as f(m)-f(m+1) using prefix balance counts and running sum of earlier counts.
d_phi=0.340  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(1)|none # none|-|nest1 # -   slope b=0.03684965275129017 (lines 0.03684965275129017, time None)
Fingerprint B: O(n)|none # none|-|nest1 # -   slope b=0.987221452743458 (lines 0.987221452743458, time 1.016233162853698)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]

## Task statement (truncated)
You are given an integer sequence $a_1, a_2, \dots, a_n$.

Find the number of pairs of indices $(l, r)$ ($1 \le l \le r \le n$) such that the value of median of $a_l, a_{l+1}, \dots, a_r$ is exactly the given number $m$.

The median of a sequence is the value of an element which is in the middle of the sequence after sorting it in non-decreasing order. If the length of the sequence is even, the left of two middle elements is used.

For example, if $a=[4, 2, 7, 5]$ then its median is $4$ since after sorting the sequence, it will look like $[2, 4, 5, 7]$ and the left of two middle elements is equal to $4$. The median of $[7, 1, 2, 9, 6]$ equals $6$ since after sorting, the value $6$ will be in the middle of the sequence.

Write a program to find the number of pairs of indices $(l, r)$ ($1 \le l \le r \le n$) such that the value of median of $a_l, a_{l+1}, \dots, a_r$ is exactly the given number $m$.


-----Input-----

The first line contains integers $n$ and $m$ ($1 \le n,m \le 2\cdot10^5$) — the length of the given sequence and the required value of the median.

The second line contains an integer sequence $a_1, a_2, \dots, a_n$ ($1 \le a_i \le 2\cdot10^5$).


-----Output-----

Print the required number.


-----Examples-----
Input
5 4
1 4 5 60 4

Output
8

Input
3 1
1 1 1

Output
6

Input
15 2
1 2 3 1 2 3 1 2 3 1 2 3 1 2 3

Output
97



-----Note-----

In the first example, the suitable pairs of indices are: $(1, 3)$, $(1, 4)$, $(1, 5)$, $(2, 2)$, $(2, 3)$, $(2, 5)$, $(4, 5)$ and $(5, 5)$.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (10 chars):
3 1
2 1 3

--- size 256 (3305 chars):
768 1
451 639 202 745 496 95 447 89 210 115 294 123 371 679 4 130 428 636 307 196 128 155 204 467 336 280 61 226 101 641 287 122 304 412 110 347 632 31 615 556 329 70 393 596 724 291 175 426 62 60 333 573 660 742 312 284 37 184 82 648 663 274 763 143 131 595 717 670 509 744 249 547 298 67 163 682 56
--- size 65536 (1305762 chars):
196608 1
102255 183693 43458 191335 11974 48786 59558 192054 163494 45089 123923 101149 137245 100476 96187 65688 106398 46967 28925 8557 109147 128385 193162 102755 103046 175940 190416 58190 136614 10631 18137 70550 185922 7688 190754 141874 102305 70419 152655 15976 29040 194805 12012 45488 38781

## Program A
```python
MAXN = 200001

def less_sum(s, m):
    n = len(s)
    a = 0
    b = 0
    res = 0
    last = 0

    count = [0 for i in range(-MAXN, MAXN+1)]

    count[0] = 1
    x = 0
    last = 1

    for i in range(n):
        if s[i] > m:
            b += 1
        else:
            a += 1
        x = a-b
        #print(x)
        #print(count[-2], count[-1], count[0], count[1], count[2])
        if s[i] > m:
            last -= count[x+1]
        else:
            last += count[x]
        #print(x, last)
        res += last
        count[x] += 1
        last += 1
    
    #print(res)

    return res

n, m = map(int, input().split(' '))
s = list(map(int, input().split(' ')))[0:n]

#print(m, s)

print(less_sum(s, m) - less_sum(s, m-1))
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=800087 max_rec=1 
  traced size=2: status=ok lines=800141 max_rec=1 
  traced size=4: status=ok lines=800249 max_rec=1 
  traced size=8: status=ok lines=800465 max_rec=1 
  traced size=16: status=ok lines=800897 max_rec=1 
  traced size=32: status=ok lines=801761 max_rec=1 
  traced size=64: status=ok lines=803489 max_rec=1 
  traced size=128: status=ok lines=806945 max_rec=1 
  traced size=256: status=ok lines=813857 max_rec=1 
  traced size=512: status=ok lines=827681 max_rec=1 
  traced size=1024: status=ok lines=855329 max_rec=1 
  traced size=2048: status=ok lines=910625 max_rec=1 
  traced size=4096: status=ok lines=1021217 max_rec=1 
  traced size=8192: status=ok lines=1242401 max_rec=1 
  traced size=16384: status=cap lines=1500001 max_rec=1 
  untraced time (size:seconds): 1:1.81e-02 2:1.74e-02 4:1.76e-02 8:1.82e-02 16:1.82e-02 32:1.79e-02 64:1.81e-02 128:1.80e-02 256:1.83e-02 512:1.86e-02 1024:1.91e-02 2048:2.06e-02 4096:2.39e-02 8192:3.15e-02 16384:4.49e-02 32768:7.38e-02 65536:1.29e-01


## Program B
```python
n,m = map(int,input().split())
a = [int(x) for x in input().split()]

def gC(m,a):
    s = [0 for x in range(2*n + 1)]
    sum = n
    res = 0
    s[sum] = 1
    ad = 0
    for i in range(n):
        if a[i] < m:
            sum -=1
            ad -=s[sum]
        else:
            ad +=s[sum]
            sum +=1
        res +=ad
        s[sum] +=1
    return res


print(gC(m,a) - gC(m + 1,a))
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=71 max_rec=1 
  traced size=2: status=ok lines=122 max_rec=1 
  traced size=4: status=ok lines=224 max_rec=1 
  traced size=8: status=ok lines=428 max_rec=1 
  traced size=16: status=ok lines=836 max_rec=1 
  traced size=32: status=ok lines=1652 max_rec=1 
  traced size=64: status=ok lines=3284 max_rec=1 
  traced size=128: status=ok lines=6548 max_rec=1 
  traced size=256: status=ok lines=13076 max_rec=1 
  traced size=512: status=ok lines=26132 max_rec=1 
  traced size=1024: status=ok lines=52244 max_rec=1 
  traced size=2048: status=ok lines=104468 max_rec=1 
  traced size=4096: status=ok lines=208916 max_rec=1 
  traced size=8192: status=ok lines=417812 max_rec=1 
  traced size=16384: status=ok lines=835604 max_rec=1 
  traced size=32768: status=cap lines=1500001 max_rec=1 
  untraced time (size:seconds): 1:1.31e-05 2:1.45e-05 4:1.65e-05 8:2.17e-05 16:3.26e-05 32:5.24e-05 64:9.79e-05 128:1.97e-04 256:3.90e-04 512:7.74e-04 1024:1.53e-03 2048:3.04e-03 4096:6.17e-03 8192:1.28e-02 16384:2.59e-02 32768:5.21e-02 65536:1.09e-01


# CASE 9: FALSE_DIFFERENT  (pair 183, task apps/4114, io=stdio)
LLM labeller said: same=1 level=None confidence=high reason: Both brute-force all (X,Y) in 0..100 and verify the height formula against every observation.
d_phi=0.600  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(exp)|none # none|-|nest3 # -   slope b=5.548992535247415 (lines 5.548992535247415, time 0.9393270633178664)
Fingerprint B: O(n)|none # none|-|nest3 # sort   slope b=0.9567618202034913 (lines 0.568793610875861, time 0.9567618202034913)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
In the Ancient Kingdom of Snuke, there was a pyramid to strengthen the authority of Takahashi, the president of AtCoder Inc.

The pyramid had center coordinates (C_X, C_Y) and height H. The altitude of coordinates (X, Y) is max(H - |X - C_X| - |Y - C_Y|, 0).  
Aoki, an explorer, conducted a survey to identify the center coordinates and height of this pyramid. As a result, he obtained the following information:  
 - C_X, C_Y was integers between 0 and 100 (inclusive), and H was an integer not less than 1.  
 - Additionally, he obtained N pieces of information. The i-th of them is: "the altitude of point (x_i, y_i) is h_i."  
This was enough to identify the center coordinates and the height of the pyramid. Find these values with the clues above.  

-----Constraints-----
 - N is an integer between 1 and 100 (inclusive).
 - x_i and y_i are integers between 0 and 100 (inclusive).
 - h_i is an integer between 0 and 10^9 (inclusive).
 - The N coordinates (x_1, y_1), (x_2, y_2), (x_3, y_3), ..., (x_N, y_N) are all different.
 - The center coordinates and the height of the pyramid can be uniquely identified.

-----Input-----
Input is given from Standard Input in the following format:  
N
x_1 y_1 h_1
x_2 y_2 h_2
x_3 y_3 h_3
:
x_N y_N h_N

-----Output-----
Print values C_X, C_Y and H representing the center coordinates and the height of the pyramid in one line, with spaces in between.  

-----Sample Input-----
4
2 3 5
2 1 5
1 2 5
3 2 5

-----Sample Output-----
2 2 6

In this case, the center coordinates and the height can be identified as (2, 2) and 6.

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (42 chars):
5
32 67 0
32 68 1
33 68 0
31 68 0
32 69 0

--- size 512 (20485 chars):
2560
32 68 1
32 67 0
32 67 0
31 68 0
32 69 0
32 69 0
31 68 0
31 68 0
32 67 0
33 68 0
33 68 0
32 69 0
31 68 0
32 68 1
32 68 1
33 68 0
32 69 0
33 68 0
32 67 0
32 67 0
33 68 0
31 68 0
33 68 0
33 68 0
33 68 0
32 69 0
33 68 0
32 69 0
32 67 0
32 69 0
31 68 0
32 67 0
32 68 1
33 68 0
32 67 0
31 68 0
32 67 0
--- size 131072 (533334 chars):
66666
33 68 0
33 68 0
32 69 0
32 68 1
32 67 0
32 68 1
32 68 1
32 68 1
31 68 0
32 69 0
31 68 0
32 68 1
32 69 0
32 69 0
33 68 0
32 68 1
33 68 0
32 67 0
32 69 0
32 68 1
31 68 0
32 68 1
33 68 0
31 68 0
32 67 0
32 68 1
31 68 0
33 68 0
32 68 1
32 67 0
32 68 1
32 69 0
32 69 0
32 68 1
32 68 1
32 68 1
33 68 

## Program A
```python
import math
from math import gcd,pi,sqrt
INF = float("inf")

import sys
sys.setrecursionlimit(10**6)
import itertools
from collections import Counter,deque
def i_input(): return int(input())
def i_map(): return list(map(int, input().split()))
def i_list(): return list(i_map())
def i_row(N): return [i_input() for _ in range(N)]
def i_row_list(N): return [i_list() for _ in range(N)]
def s_input(): return input()
def s_map(): return input().split()
def s_list(): return list(s_map())
def s_row(N): return [s_input for _ in range(N)]
def s_row_str(N): return [s_list() for _ in range(N)]
def s_row_list(N): return [list(s_input()) for _ in range(N)]

def main():
    n = i_input()
    l = [i_list() for i in range(n)]

    L = []

    for i in l:
        if i[2] != 0:
            L.append(i)
    if len(L) == 1:
        print((" ".join(map(str, L[0]))))
        return

    for x in range(101):
        for y in range(101):
            H = L[0][2] + abs(x-L[0][0]) + abs(y-L[0][1])
            flg = True
            for x1, y1, h1 in L[1:]:
                if h1 == 0:
                    pass
                if H != h1 + abs(x-x1) + abs(y-y1):
                    flg = False
                    break
            if flg == True:
                ans = [x,y]
    H = L[0][2] + abs(ans[0]-L[0][0]) + abs(ans[1]-L[0][1])
    print((" ".join(map(str, ans)) +" "+str(H)))


def __starting_point():
    main()

__starting_point()
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=56 max_rec=1 
  traced size=2: status=ok lines=81 max_rec=1 
  traced size=4: status=ok lines=122748 max_rec=1 
  untraced time (size:seconds): 1:2.55e-05 2:3.09e-05 4:4.87e-03 8:1.54e-02 16:1.42e-02 32:3.75e-02 64:7.65e-02 128:1.27e-01 256:2.80e-01 512:5.56e-01 1024:1.09e+00


## Program B
```python
N=int(input())
xyh=[list(map(int,input().split()))for _ in range(N)]
hxy=[[h,x,y]for x,y,h in xyh]
hxy.sort()
for X in range(101):
    for Y in range(101):
        h,x,y=hxy[-1]
        H=h+abs(X-x)+abs(Y-y)
        if all(h==max(H-abs(X-x)-abs(Y-y),0)for h,x,y in hxy):
            print(X,Y,H)
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=60540 max_rec=0 
  traced size=2: status=ok lines=74443 max_rec=0 
  traced size=4: status=ok lines=104665 max_rec=0 
  traced size=8: status=ok lines=144397 max_rec=0 
  traced size=16: status=ok lines=248877 max_rec=0 
  untraced time (size:seconds): 1:1.03e-02 2:1.35e-02 4:2.03e-02 8:2.96e-02 16:5.28e-02 32:7.78e-02 64:1.48e-01 128:2.81e-01 256:5.55e-01 512:1.06e+00


# CASE 12: MISSED_DIFFERENT  (pair 29, task apps/4030, io=stdio)
LLM labeller said: same=0 level=complexity confidence=low reason: A repeatedly peels off non-decreasing subsequences in O(n*colors); B assigns each char to the first color whose last char <= it.
d_phi=0.048  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n log n)|none # none|-|nest2 # -   slope b=1.5173828905191573 (lines 1.5173828905191573, time 1.1207138993135388)
Fingerprint B: O(n log n)|none # none|-|nest2 # -   slope b=1.2753565065801864 (lines 1.2753565065801864, time 1.0721028433535855)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

## Task statement (truncated)
This is a hard version of the problem. The actual problems are different, but the easy version is almost a subtask of the hard version. Note that the constraints and the output format are different.

You are given a string $s$ consisting of $n$ lowercase Latin letters.

You have to color all its characters the minimum number of colors (each character to exactly one color, the same letters can be colored the same or different colors, i.e. you can choose exactly one color for each index in $s$).

After coloring, you can swap any two neighboring characters of the string that are colored different colors. You can perform such an operation arbitrary (possibly, zero) number of times.

The goal is to make the string sorted, i.e. all characters should be in alphabetical order.

Your task is to find the minimum number of colors which you have to color the given string in so that after coloring it can become sorted by some sequence of swaps. Note that you have to restore only coloring, not the sequence of swaps.


-----Input-----

The first line of the input contains one integer $n$ ($1 \le n \le 2 \cdot 10^5$) — the length of $s$.

The second line of the input contains the string $s$ consisting of exactly $n$ lowercase Latin letters.


-----Output-----

In the first line print one integer $res$ ($1 \le res \le n$) — the minimum number of colors in which you have to color the given string so that after coloring it can become sorted by some sequence of swaps.

In the second line print any possible coloring that can be used to sort the string using some sequence of swaps described in the problem statement. The coloring is the array $c$ of length $n$, where $1 \le c_i \le res$ and $c_i$ means the color of the $i$-th character.


-----Examples-----
Input
9
abacbecfd

Output
2
1 1 2 1

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (205 chars):
200
aaaaaaaaaabbbbbccccccccccccccdddddddddeeeeeeefffffffffgggggghhhhhhiiiiiiijjjjjjjjjjkkkkkkllllllllmmmmmmmmnnnnnnoooooooppppppqqqqqqqqqqqrrrrrrsssssssttttttttuuuuuuvvvvvwwwwwxxxyyyyzzzzzzzzzzzcddddjksvw

--- size 32 (6406 chars):
6400
aaaaaaaaaabbbbbccccccccccccccdddddddddeeeeeeefffffffffgggggghhhhhhiiiiiiijjjjjjjjjjkkkkkkllllllllmmmmmmmmnnnnnnoooooooppppppqqqqqqqqqqqrrrrrrsssssssttttttttuuuuuuvvvvvwwwwwxxxyyyyzzzzzzzzzzzcddddjksvwaaaaaaaaaabbbbbccccccccccccccdddddddddeeeeeeefffffffffgggggghhhhhhiiiiiiijjjjjjjjjjkkkkkkllllll
--- size 512 (102408 chars):
102400
aaaaaaaaaabbbbbccccccccccccccdddddddddeeeeeeefffffffffgggggghhhhhhiiiiiiijjjjjjjjjjkkkkkkllllllllmmmmmmmmnnnnnnoooooooppppppqqqqqqqqqqqrrrrrrsssssssttttttttuuuuuuvvvvvwwwwwxxxyyyyzzzzzzzzzzzcddddjksvwaaaaaaaaaabbbbbccccccccccccccdddddddddeeeeeeefffffffffgggggghhhhhhiiiiiiijjjjjjjjjjkkkkkkllll

## Program A
```python
n = int(input())
s = input()
kol = [-1] * n
cur = 1
ind = 0
while ind < n:
    if kol[ind] != -1:
        ind += 1
    else:
        kol[ind] = cur
        best = s[ind]
        for i in range(ind+1, n):
            if kol[i] != -1:
                continue
            else:
                if s[i] >= best:
                    kol[i] = cur
                    best = s[i]
        ind += 1
        cur += 1
print(max(kol))
for i in range(n):
    print(kol[i], end = " ")
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=2036 max_rec=0 
  traced size=2: status=ok lines=5264 max_rec=0 
  traced size=4: status=ok lines=15320 max_rec=0 
  traced size=8: status=ok lines=46116 max_rec=0 
  traced size=16: status=ok lines=136508 max_rec=0 
  traced size=32: status=ok lines=399502 max_rec=0 
  traced size=64: status=ok lines=943502 max_rec=0 
  traced size=128: status=cap lines=1500001 max_rec=0 
  untraced time (size:seconds): 1:2.40e-04 2:5.23e-04 4:1.25e-03 8:3.11e-03 16:7.98e-03 32:2.01e-02 64:4.47e-02 128:9.50e-02 256:1.97e-01 512:4.01e-01


## Program B
```python
from math import *
n = int(input())
s = input()
pre = [0 for i in range(n)]
pre[0] = 1
prev = s[0]
lst = [-1 for i in range(26)]
lst[0] = s[0]
ct = 1
for i in range(1,n):
	for j in range(26):
		if(lst[j] == -1 or lst[j] <= s[i]):
			lst[j] = s[i]
			pre[i] = j+1
			ct = max(ct,j+1)
			break

print(ct)
for i in pre:
	print(i,end = " ")
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=2051 max_rec=0 
  traced size=2: status=ok lines=4799 max_rec=0 
  traced size=4: status=ok lines=12165 max_rec=0 
  traced size=8: status=ok lines=31453 max_rec=0 
  traced size=16: status=ok lines=81867 max_rec=0 
  traced size=32: status=ok lines=199751 max_rec=0 
  traced size=64: status=ok lines=437063 max_rec=0 
  traced size=128: status=ok lines=911687 max_rec=0 
  traced size=256: status=cap lines=1500001 max_rec=0 
  untraced time (size:seconds): 1:2.93e-04 2:6.24e-04 4:1.44e-03 8:3.40e-03 16:8.24e-03 32:1.91e-02 64:4.09e-02 128:8.47e-02 256:1.72e-01 512:3.46e-01


# CASE 15: MISSED_DIFFERENT  (pair 101, task apps/4010, io=stdio)
LLM labeller said: same=0 level=complexity confidence=low reason: A stores first index per value in an array (O(n)); B scans a growing list with `in met[:-1]` (O(n^2)).
d_phi=0.007  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest2 # -   slope b=0.8606294993196341 (lines 0.8606294993196341, time None)
Fingerprint B: O(n)|none # none|-|nest2 # -   slope b=0.895372070591048 (lines 0.895372070591048, time None)
Ladder used: 'nat' (the task test inputs themselves, size = number of tokens); sizes [5, 7, 9, 11, 15, 24, 31, 32, 73, 167]

## Task statement (truncated)
You are given an array $a$ consisting of $n$ integers.

Your task is to determine if $a$ has some subsequence of length at least $3$ that is a palindrome.

Recall that an array $b$ is called a subsequence of the array $a$ if $b$ can be obtained by removing some (possibly, zero) elements from $a$ (not necessarily consecutive) without changing the order of remaining elements. For example, $[2]$, $[1, 2, 1, 3]$ and $[2, 3]$ are subsequences of $[1, 2, 1, 3]$, but $[1, 1, 2]$ and $[4]$ are not.

Also, recall that a palindrome is an array that reads the same backward as forward. In other words, the array $a$ of length $n$ is the palindrome if $a_i = a_{n - i - 1}$ for all $i$ from $1$ to $n$. For example, arrays $[1234]$, $[1, 2, 1]$, $[1, 3, 2, 2, 3, 1]$ and $[10, 100, 10]$ are palindromes, but arrays $[1, 2]$ and $[1, 2, 3, 1]$ are not.

You have to answer $t$ independent test cases.


-----Input-----

The first line of the input contains one integer $t$ ($1 \le t \le 100$) — the number of test cases.

Next $2t$ lines describe test cases. The first line of the test case contains one integer $n$ ($3 \le n \le 5000$) — the length of $a$. The second line of the test case contains $n$ integers $a_1, a_2, \dots, a_n$ ($1 \le a_i \le n$), where $a_i$ is the $i$-th element of $a$.

It is guaranteed that the sum of $n$ over all test cases does not exceed $5000$ ($\sum n \le 5000$).


-----Output-----

For each test case, print the answer — "YES" (without quotes) if $a$ has some subsequence of length at least $3$ that is a palindrome and "NO" otherwise.


-----Example-----
Input
5
3
1 2 1
5
1 2 2 3 2
3
1 1 2
4
1 2 2 1
10
1 1 2 2 3 3 4 4 5 5

Output
YES
YES
NO
YES
NO



-----Note-----

In the first test case of the example, the array $a$ has a subsequence $[1, 2, 1]$ which is a pali

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 5 (10 chars):
1
3
1 1 1

--- size 24 (65 chars):
1
22
2 4 4 5 5 6 10 12 15 15 18 18 19 19 19 19 19 19 19 19 22 22

--- size 167 (401 chars):
13
6
2 2 5 5 6 6
6
2 2 2 2 2 4
11
2 3 11 7 8 6 3 11 6 5 11
14
1 2 1 14 14 7 3 7 7 3 5 1 1 14
6
2 4 6 5 1 1
17
10 12 6 12 15 11 2 14 13 13 8 14 5 7 11 7 2
29
3 4 6 6 14 14 17 17 18 18 22 22 27 27 27 27 27 27 27 27 27 27 27 27 27 27 27 27 27
10
9 1 2 10 7 6 5 4 5 1
11
1 1 1 1 1 1 1 1 1 9 11
15
3 4 6 9

## Program A
```python

t = int(input())

for loop in range(t):

    n = int(input())

    a = list(map(int,input().split()))

    lis = [None] * (n+1)

    ans = "NO"
    for i in range(n):

        if lis[a[i]] == None:
            lis[a[i]] = i
        elif lis[a[i]] + 1 < i:
            ans = "YES"
            break

    print (ans)
```
Trace of A on ladder 'nat':
  traced size=5: status=ok lines=19 max_rec=0 
  traced size=7: status=ok lines=19 max_rec=0 
  traced size=9: status=ok lines=36 max_rec=0 
  traced size=11: status=ok lines=36 max_rec=0 
  traced size=15: status=ok lines=53 max_rec=0 
  traced size=24: status=ok lines=55 max_rec=0 
  traced size=31: status=ok lines=115 max_rec=0 
  traced size=32: status=ok lines=118 max_rec=0 
  traced size=73: status=ok lines=177 max_rec=0 
  traced size=167: status=ok lines=340 max_rec=0 
  untraced time (size:seconds): 5:1.22e-05 7:1.21e-05 9:1.56e-05 11:1.56e-05 15:1.89e-05 24:1.64e-05 31:2.79e-05 32:2.83e-05 73:3.85e-05 167:7.34e-05


## Program B
```python
t = int(input())
for i in range(t):
    n = int(input())
    data = tuple(map(int, input().split()))
    met = []
    for i in data:
        if i in met[:-1]:
            print("YES")
            break
        met.append(i)
    else:
        print("NO")
```
Trace of B on ladder 'nat':
  traced size=5: status=ok lines=16 max_rec=0 
  traced size=7: status=ok lines=16 max_rec=0 
  traced size=9: status=ok lines=30 max_rec=0 
  traced size=11: status=ok lines=30 max_rec=0 
  traced size=15: status=ok lines=44 max_rec=0 
  traced size=24: status=ok lines=52 max_rec=0 
  traced size=31: status=ok lines=104 max_rec=0 
  traced size=32: status=ok lines=107 max_rec=0 
  traced size=73: status=ok lines=163 max_rec=0 
  traced size=167: status=ok lines=307 max_rec=0 
  untraced time (size:seconds): 5:1.30e-05 7:1.25e-05 9:1.50e-05 11:1.59e-05 15:1.87e-05 24:1.84e-05 31:2.78e-05 32:2.81e-05 73:4.03e-05 167:7.41e-05


# CASE 18: MISSED_DIFFERENT  (pair 159, task apps/4284, io=stdio)
LLM labeller said: same=0 level=formula_vs_iteration confidence=high reason: A binary searches on the number of a-turns; B computes the answer with a closed-form division formula.
d_phi=0.043  (>0.3 = fingerprint says 'different'; <0.1 = 'same')
Fingerprint A: O(n)|none # none|-|nest2 # -   slope b=0.9900666470065819 (lines 0.9900666470065819, time 0.6467429970871498)
Fingerprint B: O(n)|none # none|-|nest2 # -   slope b=0.7755643751746957 (lines 0.7755643751746957, time 0.6446159306237803)
Ladder used: 'A' (scaled copies of one test input, size = growth factor); sizes [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]

## Task statement (truncated)
Vova is playing a computer game. There are in total $n$ turns in the game and Vova really wants to play all of them. The initial charge of his laptop battery (i.e. the charge before the start of the game) is $k$.

During each turn Vova can choose what to do:   If the current charge of his laptop battery is strictly greater than $a$, Vova can just play, and then the charge of his laptop battery will decrease by $a$;  if the current charge of his laptop battery is strictly greater than $b$ ($b<a$), Vova can play and charge his laptop, and then the charge of his laptop battery will decrease by $b$;  if the current charge of his laptop battery is less than or equal to $a$ and $b$ at the same time then Vova cannot do anything and loses the game. 

Regardless of Vova's turns the charge of the laptop battery is always decreases.

Vova wants to complete the game (Vova can complete the game if after each of $n$ turns the charge of the laptop battery is strictly greater than $0$). Vova has to play exactly $n$ turns. Among all possible ways to complete the game, Vova wants to choose the one where the number of turns when he just plays (first type turn) is the maximum possible. It is possible that Vova cannot complete the game at all.

Your task is to find out the maximum possible number of turns Vova can just play (make the first type turn) or report that Vova cannot complete the game.

You have to answer $q$ independent queries.


-----Input-----

The first line of the input contains one integer $q$ ($1 \le q \le 10^5$) — the number of queries. Each query is presented by a single line.

The only line of the query contains four integers $k, n, a$ and $b$ ($1 \le k, n \le 10^9, 1 \le b < a \le 10^9$) — the initial charge of Vova's laptop battery, the number of turns in the game and

## Ladder inputs (first 300 chars; smallest, middle, largest)
--- size 1 (236 chars):
10
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
5 1 4 3

--- size 512 (118706 chars):
5120
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
5 1 4 3
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
5 1 4 3
1000000000 500000000 2 1
1000
--- size 131072 (1162490 chars):
50000
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
1000000000 500000000 2 1
5 1 4 3
1000000000 500000000 2 1
1000000000 500000000 2 1
5 1 4 3
5 1

## Program A
```python
q = int(input())
for i in range(q):
	k, n, a, b = list(map(int, input().split()))
	if n * b >= k:
		print(-1)
		continue
	l = 0
	r = min(k // a + 1, n + 1)
	while r - l > 1:
		m = (r + l) // 2
		if ((k - a * m - 1) // b >= n - m) and k - a * m > 0:
			l = m
		else:
			r = m
	print(l)
```
Trace of A on ladder 'A':
  traced size=1: status=ok lines=1120 max_rec=0 
  traced size=2: status=ok lines=2350 max_rec=0 
  traced size=4: status=ok lines=4698 max_rec=0 
  traced size=8: status=ok lines=9394 max_rec=0 
  traced size=16: status=ok lines=17554 max_rec=0 
  traced size=32: status=ok lines=36562 max_rec=0 
  traced size=64: status=ok lines=72338 max_rec=0 
  traced size=128: status=ok lines=141090 max_rec=0 
  traced size=256: status=ok lines=286098 max_rec=0 
  traced size=512: status=ok lines=568498 max_rec=0 
  traced size=1024: status=ok lines=1138338 max_rec=0 
  traced size=2048: status=cap lines=1500001 max_rec=0 
  untraced time (size:seconds): 1:1.40e-04 2:2.78e-04 4:5.45e-04 8:1.09e-03 16:2.04e-03 32:4.22e-03 64:8.33e-03 128:1.63e-02 256:3.28e-02 512:6.54e-02 1024:1.32e-01 2048:2.63e-01 4096:5.25e-01 8192:6.48e-01 16384:6.48e-01 32768:6.41e-01 65536:6.41e-01 131072:6.54e-01


## Program B
```python
#570_C

import math

cases = int(input())

for i in range(0, cases):
    ln = [int(i) for i in input().split(" ")]
    k = ln[0]
    t = ln[1]
    a = ln[2]
    b = ln[3]
    if k / t <= b:
        print(-1)
    else:
        num = b * t
        turns = (k - num) / (a - b)
        if turns % 1 == 0:
            print(min(t, int(turns) - 1))
        else:
            print(min(t, math.floor(turns)))
```
Trace of B on ladder 'A':
  traced size=1: status=ok lines=153 max_rec=0 
  traced size=2: status=ok lines=303 max_rec=0 
  traced size=4: status=ok lines=603 max_rec=0 
  traced size=8: status=ok lines=1203 max_rec=0 
  traced size=16: status=ok lines=2403 max_rec=0 
  traced size=32: status=ok lines=4803 max_rec=0 
  traced size=64: status=ok lines=9603 max_rec=0 
  traced size=128: status=ok lines=19203 max_rec=0 
  traced size=256: status=ok lines=38403 max_rec=0 
  traced size=512: status=ok lines=76803 max_rec=0 
  traced size=1024: status=ok lines=153603 max_rec=0 
  traced size=2048: status=ok lines=307203 max_rec=0 
  traced size=4096: status=ok lines=614403 max_rec=0 
  traced size=8192: status=ok lines=750003 max_rec=0 
  traced size=16384: status=ok lines=750003 max_rec=0 
  traced size=32768: status=ok lines=750003 max_rec=0 
  traced size=65536: status=ok lines=750003 max_rec=0 
  traced size=131072: status=ok lines=750003 max_rec=0 
  untraced time (size:seconds): 1:4.21e-05 2:7.24e-05 4:1.33e-04 8:2.50e-04 16:4.88e-04 32:9.69e-04 64:1.94e-03 128:3.90e-03 256:7.78e-03 512:1.55e-02 1024:3.07e-02 2048:6.14e-02 4096:1.22e-01 8192:1.49e-01 16384:1.49e-01 32768:1.49e-01 65536:1.49e-01 131072:1.50e-01
