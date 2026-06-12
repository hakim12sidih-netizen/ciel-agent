// CIEL v1.0 — Hardware monitor (Go)
// Migré depuis Hydra, adapté pour CIEL.
// Fournit des métriques matérielles natives via Go.

package main

import (
	"fmt"
	"runtime"
	"time"
)

type HardwareMetrics struct {
	CPUCount      int     `json:"cpu_count"`
	GoRoutines    int     `json:"go_routines"`
	MemoryAlloc   uint64  `json:"memory_alloc_bytes"`
	MemoryTotal   uint64  `json:"memory_total_bytes"`
	MemoryPercent float64 `json:"memory_percent"`
	Uptime        string  `json:"uptime"`
	Timestamp     int64   `json:"timestamp_ms"`
}

func GetHardwareMetrics() HardwareMetrics {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return HardwareMetrics{
		CPUCount:      runtime.NumCPU(),
		GoRoutines:    runtime.NumGoroutine(),
		MemoryAlloc:   m.Alloc,
		MemoryTotal:   m.TotalAlloc,
		MemoryPercent: float64(m.Alloc) / float64(m.TotalAlloc+1) * 100,
		Uptime:        time.Since(startTime).Round(time.Second).String(),
		Timestamp:     time.Now().UnixMilli(),
	}
}

var startTime time.Time

func main() {
	startTime = time.Now()
	fmt.Println("CIEL Go Hardware Monitor — v1.0")
	fmt.Println("================================")

	metrics := GetHardwareMetrics()
	fmt.Printf("CPU: %d cores\n", metrics.CPUCount)
	fmt.Printf("Goroutines: %d\n", metrics.GoRoutines)
	fmt.Printf("Memory: %d KB allocated\n", metrics.MemoryAlloc/1024)
	fmt.Printf("Uptime: %s\n", metrics.Uptime)
}
