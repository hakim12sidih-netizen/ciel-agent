// Hydra Polyglot — Go HTTP server
// Expose health, metrics, and a simple hash endpoint that the TypeScript
// observability/health modules can call for liveness/readiness probing.
//
// Run:  go run polyglot/go/server.go
// Test: curl http://localhost:8732/health
//       curl http://localhost:8732/metrics
//       curl -X POST http://localhost:8732/hash -d "hello world"

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync/atomic"
	"time"
)

var (
	startedAt  = time.Now()
	reqCounter uint64
)

// hashHandler returns the SHA-256 hex of the request body.
func hashHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	sum := sha256.Sum256(body)
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprint(w, hex.EncodeToString(sum[:]))
}

// healthHandler returns a JSON health report.
func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(startedAt).Seconds()
	w.Header().Set("Content-Type", "application/json")
	fmt.Fprintf(w, `{"status":"ok","uptime_s":%.0f,"service":"hydra-go-bridge"}`, uptime)
}

// metricsHandler returns a Prometheus-format text exposition.
func metricsHandler(w http.ResponseWriter, r *http.Request) {
	atomic.AddUint64(&reqCounter, 1)
	w.Header().Set("Content-Type", "text/plain; version=0.0.4")
	fmt.Fprintf(w, "# HELP hydra_go_requests_total Total HTTP requests to Go bridge\n")
	fmt.Fprintf(w, "# TYPE hydra_go_requests_total counter\n")
	fmt.Fprintf(w, "hydra_go_requests_total %d\n", atomic.LoadUint64(&reqCounter))
	fmt.Fprintf(w, "# HELP hydra_go_uptime_seconds Uptime in seconds\n")
	fmt.Fprintf(w, "# TYPE hydra_go_uptime_seconds gauge\n")
	fmt.Fprintf(w, "hydra_go_uptime_seconds %.2f\n", time.Since(startedAt).Seconds())
}

func main() {
	addr := ":8732"
	if v := os.Getenv("HYDRA_GO_ADDR"); v != "" {
		addr = v
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/metrics", metricsHandler)
	mux.HandleFunc("/hash", hashHandler)
	log.Printf("[hydra-go] Listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}
