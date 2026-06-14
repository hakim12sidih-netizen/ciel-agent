// Hydra Polyglot — Rust math kernel
// Hot-path math primitives used by ReasoningEngine (and other heavy compute).
//
// Commands:
//   bayesian <prior> <lr>     P(H|E) = lr*p / (lr*p + 1 - p)
//   cosine <a.json> <b.json>  Cosine similarity between two numeric vectors
//   confidence <support> <total>  Inductive confidence in [0, 1]
//   entropy <a.json>          Shannon entropy of a probability distribution
//   kl <p.json> <q.json>      KL divergence D(P || Q)
//   softmax <x.json>          Numerically stable softmax
//
// All JSON inputs are arrays of f64.

use std::env;
use std::fs;
use std::io::{self, Read};

fn read_stdin() -> String {
    let mut buf = String::new();
    io::stdin().read_to_string(&mut buf).expect("stdin");
    buf
}

fn parse_vec(s: &str) -> Vec<f64> {
    let v: serde_json::Value = serde_json::from_str(s.trim())
        .expect("not a valid JSON array");
    v.as_array()
        .expect("not an array")
        .iter()
        .map(|x| x.as_f64().expect("not a number"))
        .collect()
}

fn cmd_bayesian(args: &[String]) -> i32 {
    if args.len() < 2 {
        eprintln!("Usage: bayesian <prior> <lr>");
        return 1;
    }
    let prior: f64 = args[0].parse().expect("bad prior");
    let lr: f64 = args[1].parse().expect("bad lr");
    let denom = lr * prior + (1.0 - prior);
    let posterior = if denom == 0.0 { 0.0 } else { (lr * prior) / denom };
    println!("{:.10}", posterior);
    0
}

fn cosine(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() || a.is_empty() { return 0.0; }
    let dot: f64 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let na: f64 = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let nb: f64 = b.iter().map(|x| x * x).sum::<f64>().sqrt();
    if na == 0.0 || nb == 0.0 { return 0.0; }
    dot / (na * nb)
}

fn cmd_cosine(args: &[String]) -> i32 {
    if args.len() < 2 {
        eprintln!("Usage: cosine <a.json> <b.json>");
        return 1;
    }
    let a = parse_vec(&args[0]);
    let b = parse_vec(&args[1]);
    println!("{:.10}", cosine(&a, &b));
    0
}

fn cmd_confidence(args: &[String]) -> i32 {
    if args.len() < 2 {
        eprintln!("Usage: confidence <support_count> <total_count>");
        return 1;
    }
    let support: f64 = args[0].parse().expect("bad support");
    let total: f64 = args[1].parse().expect("bad total");
    if total == 0.0 {
        println!("0");
        return 0;
    }
    let ratio = support / total;
    // Inductive: min(0.95, 0.5 + ratio * 0.45)
    let c = (0.5 + ratio * 0.45).min(0.95);
    println!("{:.10}", c);
    0
}

fn shannon_entropy(p: &[f64]) -> f64 {
    let mut h = 0.0;
    for &pi in p {
        if pi > 0.0 { h -= pi * pi.ln(); }
    }
    h
}

fn cmd_entropy(args: &[String]) -> i32 {
    let p = parse_vec(&args[0]);
    println!("{:.10}", shannon_entropy(&p));
    0
}

fn kl(p: &[f64], q: &[f64]) -> f64 {
    if p.len() != q.len() { return 0.0; }
    let mut d = 0.0;
    for (&pi, &qi) in p.iter().zip(q) {
        if pi > 0.0 {
            if qi <= 0.0 { return f64::INFINITY; }
            d += pi * (pi / qi).ln();
        }
    }
    d
}

fn cmd_kl(args: &[String]) -> i32 {
    if args.len() < 2 {
        eprintln!("Usage: kl <p.json> <q.json>");
        return 1;
    }
    let p = parse_vec(&args[0]);
    let q = parse_vec(&args[1]);
    let d = kl(&p, &q);
    if d.is_infinite() {
        println!("inf");
    } else {
        println!("{:.10}", d);
    }
    0
}

fn softmax(x: &[f64]) -> Vec<f64> {
    if x.is_empty() { return vec![]; }
    let m = x.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let exps: Vec<f64> = x.iter().map(|v| (v - m).exp()).collect();
    let s: f64 = exps.iter().sum();
    exps.iter().map(|e| e / s).collect()
}

fn cmd_softmax(args: &[String]) -> i32 {
    let x = parse_vec(&args[0]);
    let s = softmax(&x);
    println!("{}", serde_json::to_string(&s).unwrap());
    0
}

fn cmd_stdin() -> i32 {
    let buf = read_stdin();
    let mut lines = buf.lines();
    let mode = lines.next().unwrap_or("").trim().to_string();
    let rest: Vec<String> = lines.map(|s| s.to_string()).collect();
    match mode.as_str() {
        "bayesian" => cmd_bayesian(&rest),
        "cosine" => cmd_cosine(&rest),
        "confidence" => cmd_confidence(&rest),
        "entropy" => cmd_entropy(&rest),
        "kl" => cmd_kl(&rest),
        "softmax" => cmd_softmax(&rest),
        _ => {
            eprintln!("Unknown mode: {}", mode);
            1
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        cmd_stdin();
        return;
    }
    let exit = match args[1].as_str() {
        "bayesian" => cmd_bayesian(&args[2..]),
        "cosine" => cmd_cosine(&args[2..]),
        "confidence" => cmd_confidence(&args[2..]),
        "entropy" => cmd_entropy(&args[2..]),
        "kl" => cmd_kl(&args[2..]),
        "softmax" => cmd_softmax(&args[2..]),
        "stdin" => cmd_stdin(),
        _ => {
            eprintln!("Usage: {} <bayesian|cosine|confidence|entropy|kl|softmax|stdin>", args[0]);
            1
        }
    };
    std::process::exit(exit);
}
