// Hydra Polyglot — Rust CLI bridge
// Fast deterministic computation: SHA-256 (via stdlib's `Sha256` from ring would
// need internet, so we use a hand-rolled FNV-1a 64-bit + a simple polynomial hash).
// Provides the same `hash` operation as Go, so TypeScript can verify cross-language
// consistency.
//
// Run:  cargo run --manifest-path polyglot/rust/Cargo.toml -- hash "hello world"
//       echo -n "hello world" | cargo run --manifest-path polyglot/rust/Cargo.toml -- hash-stdin

use std::env;
use std::io::{self, Read};

/// FNV-1a 64-bit hash (deterministic, no allocations).
fn fnv1a_64(data: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for &b in data {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

/// Polynomial rolling hash (simple, deterministic).
fn poly_hash(data: &[u8]) -> u64 {
    let mut h: u64 = 0;
    let p: u64 = 1099511628211;  // FNV prime
    for &b in data {
        h = h.wrapping_mul(p).wrapping_add(b as u64);
    }
    h
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: hydra_rust_bridge <hash|hash-stdin> [input]");
        std::process::exit(1);
    }
    let mode = &args[1];
    let input: Vec<u8> = if mode == "hash-stdin" {
        let mut buf = Vec::new();
        io::stdin().read_to_end(&mut buf).expect("read stdin");
        buf
    } else if mode == "hash" {
        if args.len() < 3 {
            eprintln!("hash requires input argument");
            std::process::exit(1);
        }
        args[2].as_bytes().to_vec()
    } else {
        eprintln!("Unknown mode: {}", mode);
        std::process::exit(1);
    };

    let fnv = fnv1a_64(&input);
    let poly = poly_hash(&input);
    println!("fnv1a:{:016x} poly:{:016x} len:{}", fnv, poly, input.len());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fnv1a_known_empty() {
        assert_eq!(fnv1a_64(b""), 0xcbf29ce484222325);
    }

    #[test]
    fn fnv1a_known_hello() {
        // Known FNV-1a 64 of "hello" = 0xa430d84680aabd0b
        assert_eq!(fnv1a_64(b"hello"), 0xa430d84680aabd0b);
    }

    #[test]
    fn fnv1a_deterministic() {
        let a = fnv1a_64(b"hydra");
        let b = fnv1a_64(b"hydra");
        assert_eq!(a, b);
    }

    #[test]
    fn poly_known_empty() {
        assert_eq!(poly_hash(b""), 0);
    }

    #[test]
    fn poly_deterministic() {
        let a = poly_hash(b"rust");
        let b = poly_hash(b"rust");
        assert_eq!(a, b);
    }
}
