// CIEL v1.0 — HTTP Server (Go)
// Migré depuis Hydra, adapté pour CIEL.
// Serveur HTTP pour métriques et health check.

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":    "healthy",
		"service":   "ciel-go",
		"version":   "1.0.0",
		"timestamp": time.Now().UnixMilli(),
	})
}

func metricsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"cpu_cores":     4,
		"memory_mb":     512,
		"uptime_seconds": int(time.Since(startTime).Seconds()),
		"active_tasks":  3,
	})
}

var startTime time.Time

func main() {
	startTime = time.Now()
	fmt.Println("CIEL Go HTTP Server — v1.0")
	fmt.Println("============================")

	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/metrics", metricsHandler)

	port := ":9300"
	fmt.Printf("  ▶ Serveur démarré sur %s\n", port)
	log.Fatal(http.ListenAndServe(port, nil))
}
