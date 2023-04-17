from Crypto import Random
from Crypto.Math.Numbers import Integer
from Crypto.Math.Primality import (test_probable_prime,
                                   generate_probable_prime, COMPOSITE)
from Crypto.PublicKey.RSA import RsaKey

def generate(bits, randfunc=None, e=65537):
    """Create a new RSA key pair.
    The algorithm closely follows NIST `FIPS 186-4`_ in its
    sections B.3.1 and B.3.3. The modulus is the product of
    two non-strong probable primes.
    Each prime passes a suitable number of Miller-Rabin tests
    with random bases and a single Lucas test.
    Args:
      bits (integer):
        Key length, or size (in bits) of the RSA modulus.
        It must be at least 1024, but **2048 is recommended.**
        The FIPS standard only defines 1024, 2048 and 3072.
      randfunc (callable):
        Function that returns random bytes.
        The default is :func:`Crypto.Random.get_random_bytes`.
      e (integer):
        Public RSA exponent. It must be an odd positive integer.
        It is typically a small number with very few ones in its
        binary representation.
        The FIPS standard requires the public exponent to be
        at least 65537 (the default).
    Returns: an RSA key object (:class:`RsaKey`, with private key).
    .. _FIPS 186-4: http://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf
    """

    if e % 2 == 0 or e < 3:
        raise ValueError("RSA public exponent must be a positive, odd integer larger than 2.")

    if randfunc is None:
        randfunc = Random.get_random_bytes

    d = n = Integer(1)
    e = Integer(e)

    while n.size_in_bits() != bits and d < (1 << (bits // 2)):
        # Generate the prime factors of n: p and q.
        # By construciton, their product is always
        # 2^{bits-1} < p*q < 2^bits.
        size_q = bits // 2
        size_p = bits - size_q

        min_p = min_q = (Integer(1) << (2 * size_q - 1)).sqrt()
        if size_q != size_p:
            min_p = (Integer(1) << (2 * size_p - 1)).sqrt()

        def filter_p(candidate):
            return candidate > min_p and (candidate - 1).gcd(e) == 1

        p = generate_probable_prime(exact_bits=size_p,
                                    randfunc=randfunc,
                                    prime_filter=filter_p)

        min_distance = Integer(1) << (bits // 2 - 100)

        def filter_q(candidate):
            return (candidate > min_q and
                    (candidate - 1).gcd(e) == 1 and
                    abs(candidate - p) > min_distance)

        q = generate_probable_prime(exact_bits=size_q,
                                    randfunc=randfunc,
                                    prime_filter=filter_q)

        n = p * q
        lcm = (p - 1).lcm(q - 1)
        d = e.inverse(lcm)

    if p > q:
        p, q = q, p

    u = p.inverse(q)

    return RsaKey(n=n, e=e, d=d, p=p, q=q, u=u)

pkey = generate(2048, e=17)
nkey = generate(1024, e=17)

print('Your new primary key values are:')
print('  n:', str(pkey.n))
print('  d:', str(pkey.d))
print('')
print('Your new network key values are:')
print('  n:', str(nkey.n))
print('  d:', str(nkey.d))