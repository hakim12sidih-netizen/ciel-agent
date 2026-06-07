// Hydra Polyglot — Rust episodic vault
// Replaces the TS EpisodicVault.ts for the heavy parts:
//   - JSON file persistence with atomic writes
//   - Cosine similarity search (numerical, fast)
//
// Commands:
//   add <id> <json>          Append an episode
//   similarity <json>        Top-3 episodes by similarity
//   thread                   Get current narrative thread
//   count                    Count episodes
//
// Uses serde + serde_json (no async runtime needed).

use std::env;
use std::fs;
use std::io::{self, Read, Write};
use std::path::PathBuf;

fn vault_dir() -> PathBuf {
    let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home).join(".hydra").join("episodes_rust")
}

fn ensure_vault() -> std::io::Result<()> {
    let d = vault_dir();
    if !d.exists() {
        fs::create_dir_all(&d)?;
    }
    Ok(())
}

fn cmd_add(args: &[String]) -> i32 {
    if args.len() < 2 {
        eprintln!("Usage: add <id> <json>");
        return 1;
    }
    let id = &args[0];
    let json = &args[1];
    if let Err(e) = ensure_vault() {
        eprintln!("vault dir: {}", e);
        return 1;
    }
    let path = vault_dir().join(format!("{}.json", id));
    // Atomic write: write to .tmp, then rename
    let tmp = path.with_extension("json.tmp");
    if let Err(e) = fs::write(&tmp, json) {
        eprintln!("write tmp: {}", e);
        return 1;
    }
    if let Err(e) = fs::rename(&tmp, &path) {
        eprintln!("rename: {}", e);
        return 1;
    }
    println!("OK");
    0
}

fn read_all() -> Vec<(String, serde_json::Value)> {
    let mut out = Vec::new();
    if let Ok(entries) = fs::read_dir(vault_dir()) {
        for e in entries.flatten() {
            let p = e.path();
            if p.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Ok(s) = fs::read_to_string(&p) {
                    if let Ok(v) = serde_json::from_str::<serde_json::Value>(&s) {
                        let id = p.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();
                        out.push((id, v));
                    }
                }
            }
        }
    }
    out
}

/// Cosine similarity between two intensity vectors (numerical feature of qualia).
fn cosine_similarity(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }
    let dot: f64 = a.iter().zip(b).map(|(x, y)| x * y).sum();
    let na: f64 = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let nb: f64 = b.iter().map(|x| x * x).sum::<f64>().sqrt();
    if na == 0.0 || nb == 0.0 { return 0.0; }
    dot / (na * nb)
}

fn extract_intensity(qualia: &serde_json::Value) -> Vec<f64> {
    qualia.as_array()
        .map(|arr| arr.iter().filter_map(|q| q.get("intensity").and_then(|v| v.as_f64())).collect())
        .unwrap_or_default()
}

fn cmd_similarity(args: &[String]) -> i32 {
    if args.is_empty() {
        eprintln!("Usage: similarity <json>");
        return 1;
    }
    let profile: serde_json::Value = match serde_json::from_str(&args[0]) {
        Ok(v) => v,
        Err(e) => { eprintln!("bad json: {}", e); return 1; }
    };
    let profile_vec = extract_intensity(&profile);
    let all = read_all();
    let mut scored: Vec<(String, f64)> = all.iter()
        .map(|(id, ep)| {
            let vec = extract_intensity(ep.get("qualia").unwrap_or(&serde_json::Value::Null));
            (id.clone(), cosine_similarity(&profile_vec, &vec))
        })
        .collect();
    scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    let top3: Vec<serde_json::Value> = scored.iter().take(3).map(|(id, score)| {
        serde_json::json!({"id": id, "score": score})
    }).collect();
    println!("{}", serde_json::to_string(&top3).unwrap());
    0
}

fn cmd_count() -> i32 {
    println!("{}", read_all().len());
    0
}

fn cmd_thread() -> i32 {
    let mut all = read_all();
    all.sort_by(|a, b| {
        let ta = a.1.get("timestamp").and_then(|v| v.as_u64()).unwrap_or(0);
        let tb = b.1.get("timestamp").and_then(|v| v.as_u64()).unwrap_or(0);
        ta.cmp(&tb)
    });
    let last5: Vec<&str> = all.iter().rev().take(5).map(|(id, _)| id.as_str()).collect();
    println!("{}", serde_json::to_string(&last5).unwrap());
    0
}

fn cmd_stdin() -> i32 {
    let mut buf = String::new();
    io::stdin().read_to_string(&mut buf).expect("read stdin");
    let mode = buf.lines().next().unwrap_or("").trim();
    let rest: Vec<String> = buf.lines().skip(1).map(|s| s.to_string()).collect();
    match mode {
        "add" => cmd_add(&rest),
        "similarity" => cmd_similarity(&rest),
        "count" => cmd_count(),
        "thread" => cmd_thread(),
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
        "add" => cmd_add(&args[2..]),
        "similarity" => cmd_similarity(&args[2..]),
        "count" => cmd_count(),
        "thread" => cmd_thread(),
        "stdin" => cmd_stdin(),
        _ => {
            eprintln!("Usage: {} <add|similarity|count|thread|stdin>", args[0]);
            1
        }
    };
    std::process::exit(exit);
}
