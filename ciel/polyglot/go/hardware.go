// Hydra Polyglot — Hardware metrics in Go
// Replaces the slow TS implementation in HardwareMetrics.ts.
// Reads /proc/stat (Linux), /proc/meminfo, and computes a deterministic
// physical-entropy value using a logistic map (chaos regime).
//
// Run standalone:  go run polyglot/go/hardware.go
// Output:          JSON line {cpu, memory, entropy, event_loop_ms}
//
// Compiled:        go build -o polyglot/go/hardware polyglot/go/hardware.go

package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type Metrics struct {
	CPU        float64 `json:"cpu"`         // 0.0 to 1.0
	Memory     float64 `json:"memory"`      // 0.0 to 1.0
	Entropy    float64 `json:"entropy"`     // 0.0 to 1.0
	UptimeS    float64 `json:"uptime_s"`
	ProcsAvail int     `json:"procs_avail"`
}

var (
	mu         sync.Mutex
	lastIdle   uint64
	lastTotal  uint64
	chaosState = 0.5
)

func readCPUStat() (idle, total uint64, err error) {
	f, err := os.Open("/proc/stat")
	if err != nil {
		return 0, 0, err
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	if !scanner.Scan() {
		return 0, 0, fmt.Errorf("empty /proc/stat")
	}
	fields := strings.Fields(scanner.Text())
	if len(fields) < 5 || fields[0] != "cpu" {
		return 0, 0, fmt.Errorf("unexpected /proc/stat format")
	}
	for i, v := range fields[1:] {
		n, _ := strconv.ParseUint(v, 10, 64)
		total += n
		if i == 3 { // idle is the 4th field
			idle = n
		}
	}
	return idle, total, nil
}

func getRealCPULoad() float64 {
	idle, total, err := readCPUStat()
	if err != nil {
		return 0
	}
	mu.Lock()
	defer mu.Unlock()
	diffIdle := idle - lastIdle
	diffTotal := total - lastTotal
	lastIdle, lastTotal = idle, total
	if diffTotal == 0 {
		return 0
	}
	return 1.0 - float64(diffIdle)/float64(diffTotal)
}

func getRealMemoryUsage() float64 {
	data, err := os.ReadFile("/proc/meminfo")
	if err != nil {
		return 0
	}
	var total, free, available uint64
	for _, line := range strings.Split(string(data), "\n") {
		fields := strings.Fields(line)
		if len(fields) < 2 {
			continue
		}
		val, _ := strconv.ParseUint(fields[1], 10, 64)
		switch fields[0] {
		case "MemTotal:":
			total = val
		case "MemFree:":
			free = val
		case "MemAvailable:":
			available = val
		}
	}
	if total == 0 {
		return 0
	}
	used := total
	if available > 0 {
		used = total - available
	} else {
		used = total - free
	}
	return float64(used) / float64(total)
}

// Logistic map in chaos regime (r=3.99). Output stays in (0,1) after
// a few iterations. Mix in current CPU load as a perturbation to make it
// physically-coupled (not pseudo-random).
func getPhysicalEntropy(cpuLoad float64) float64 {
	mu.Lock()
	defer mu.Unlock()
	r := 3.99 + (cpuLoad * 0.01)
	memPerturbation := math.Mod(float64(time.Now().UnixNano()), 1000) / 10000
	chaosState = r*chaosState*(1-chaosState) + memPerturbation
	if chaosState > 1.0 {
		chaosState -= 1.0
	}
	if chaosState <= 0.0 {
		chaosState = 0.0001
	}
	return chaosState
}

func snapshot() Metrics {
	cpu := getRealCPULoad()
	mem := getRealMemoryUsage()
	entropy := getPhysicalEntropy(cpu)
	procsAvail := 0
	if n, err := os.ReadFile("/proc/cpuinfo"); err == nil {
		procsAvail = strings.Count(string(n), "processor\t:")
	}
	return Metrics{
		CPU:        cpu,
		Memory:     mem,
		Entropy:    entropy,
		UptimeS:    time.Since(startTime).Seconds(),
		ProcsAvail: procsAvail,
	}
}

var startTime = time.Now()

func main() {
	// If called with --loop, emit one JSON per second on stdout (for bench).
	if len(os.Args) > 1 && os.Args[1] == "--loop" {
		// Prime the CPU counter
		getRealCPULoad()
		for {
			m := snapshot()
			b, _ := json.Marshal(m)
			fmt.Println(string(b))
			time.Sleep(1 * time.Second)
		}
	}
	// One-shot mode
	m := snapshot()
	b, _ := json.Marshal(m)
	fmt.Println(string(b))
}
