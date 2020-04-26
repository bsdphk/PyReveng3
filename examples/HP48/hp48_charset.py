

# See https://www.hpmuseum.org/cgi-sys/cgiwrap/hpmuseum/articles.cgi?read=1218

rpl_chars = {
    0x1F: "\u2026",       #   Ellipsis

    0x7F: "\u2592",       #   Medium Shade

    0x80: "\u2220",       #   Measured Angle
    0x81: "\u0078\u0305", #   X overbar 
    0x82: "\u2207",       #   Nabla
    0x83: "\u221A",       #   Square Root
    0x84: "\u222B",       #   Integral
    0x85: "\u03A3",       #   Greek Capital Letter Sigma
    0x86: "\u25B6",       #   Black Right-Pointing Triangle
    0x87: "\u03C0",       #   Greek Small Letter Pi
    0x88: "\u2202",       #   Partial Differential
    0x89: "\u2264",       #   Less-Than or Equal To
    0x8A: "\u2265",       #   Greater-Than or Equal To
    0x8B: "\u2260",       #   Not Equal To
    0x8C: "\u03B1",       #   Greek Small Letter Alpha
    0x8D: "\u2192",       #   Rightwards Arrow
    0x8E: "\u2190",       #   Leftwards Arrow
    0x8F: "\u2193",       #   Downwards Arrow

    0x90: "\u2191",       #   Upwards Arrow
    0x91: "\u03B3",       #   Greek Small Letter Gamma
    0x92: "\u03B4",       #   Greek Small Letter Delta
    0x93: "\u03B5",       #   Greek Small Letter Epsilon
    0x94: "\u03B7",       #   Greek Small Letter Eta
    0x95: "\u03B8",       #   Greek Small Letter Theta
    0x96: "\u03BB",       #   Greek Small Letter Lamda
    0x97: "\u03C1",       #   Greek Small Letter Rho
    0x98: "\u03C3",       #   Greek Small Letter Sigma
    0x99: "\u03C4",       #   Greek Small Letter Tau
    0x9A: "\u03C9",       #   Greek Small Letter Omega
    0x9B: "\u0394",       #   Greek Capital Letter Delta
    0x9C: "\u03A0",       #   Greek Capital Letter Pi
    0x9D: "\u03A9",       #   Greek Capital Letter Omega
    0x9E: "\u25A0",       #   Black Square
    0x9F: "\u221E",       #   Infinity
}

if __name__ == "__main__":
    for i, j in sorted(rpl_chars.items()):
        print("0x%02x" % i, j)
