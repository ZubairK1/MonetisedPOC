#reference(https://en.wikipedia.org/w/index.php?title=Paillier_cryptosystem)
import secrets
import math

def egcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return abs(a*b) // math.gcd(a, b)

def invmod(a, n):
    t, newt = 0, 1
    r, newr = n, a
    while newr:
        q = r // newr
        t, newt = newt, t - q*newt
        r, newr = newr, r - q*newr
    if r > 1:
        raise ValueError("Error")
    if t < 0:
        t += n
    return t

def _is_probable_prime(n):
    if n in (2, 3):
        return True
    if n % 2 == 0 or n < 2:
        return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in [2, 3, 5, 7, 11, 13, 17]:
        if a % n == 0:
            return True
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def _rand_prime(bits):
    while True:
        p = secrets.randbits(bits) | 1 | (1 << (bits - 1))
        if _is_probable_prime(p):
            return p

class PublicKey:
    def __init__(self, n):
        self.n = n
        self.n2 = n * n
        self.g = n + 1  

class PrivateKey:
    def __init__(self, lam, mu, pub: PublicKey):
        self.lam = lam
        self.mu = mu
        self.pub = pub

def keygen(bits=512):
    p = _rand_prime(bits // 2)
    q = _rand_prime(bits // 2)
    while q == p:
        q = _rand_prime(bits // 2)
    n = p * q
    lam = lcm(p - 1, q - 1)
    pub = PublicKey(n)
    x = pow(pub.g, lam, pub.n2)
    Lx = (x - 1) // n
    mu = invmod(Lx % n, n)
    priv = PrivateKey(lam, mu, pub)
    return pub, priv

def encrypt(pub: PublicKey, m: int):
    if m < 0 or m >= pub.n:
        raise ValueError("Range error")
    r = secrets.randbelow(pub.n)
    while egcd(r, pub.n) != 1:
        r = secrets.randbelow(pub.n)
    return (pow(pub.g, m, pub.n2) * pow(r, pub.n, pub.n2)) % pub.n2

def decrypt(priv: PrivateKey, c: int):
    x = pow(c, priv.lam, priv.pub.n2)
    Lx = (x - 1) // priv.pub.n
    return (Lx * priv.mu) % priv.pub.n

def e_add(pub: PublicKey, c1: int, c2: int):
    return (c1 * c2) % pub.n2

def e_mul_const(pub: PublicKey, c: int, k: int):
    return pow(c, k, pub.n2)
