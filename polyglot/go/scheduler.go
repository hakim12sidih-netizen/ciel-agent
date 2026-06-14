// Hydra Polyglot — Go scheduler
// Lightweight in-process cron: triggers callbacks at given intervals.
// Avoids Node.js setInterval drift + survives long blocking ops.
//
// Commands:
//   add <id> <interval_ms> [max_runs]   Register a job (idempotent)
//   remove <id>                          Unregister
//   list                                 List active job IDs
//   tick <id>                            Manually trigger a job
//   status <id>                          Last run timestamp + count
//
// Runs a single-threaded event loop reading from stdin:
//   stdin: "add" "id" "1000" ""\n → schedules, prints OK
//          "tick" "id"\n → executes, prints "ran <count>"
//   stdout: OK | ran N | {id,interval_ms,last_run_ms,count}
//
// This is the time-accurate core. TS still owns registration of what to do
// (we just trigger via the tick command).

package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type Job struct {
	ID         string `json:"id"`
	IntervalMs int    `json:"interval_ms"`
	MaxRuns    int    `json:"max_runs,omitempty"`
	LastRunMs  int64  `json:"last_run_ms"`
	Count      int    `json:"count"`
	CreatedMs  int64  `json:"created_ms"`
}

type Scheduler struct {
	mu   sync.Mutex
	jobs map[string]*Job
}

func NewScheduler() *Scheduler {
	return &Scheduler{jobs: make(map[string]*Job)}
}

func (s *Scheduler) Add(id string, intervalMs int, maxRuns int) error {
	if intervalMs <= 0 {
		return fmt.Errorf("interval must be > 0")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, exists := s.jobs[id]; exists {
		return fmt.Errorf("job %s already exists", id)
	}
	now := time.Now().UnixMilli()
	s.jobs[id] = &Job{
		ID:         id,
		IntervalMs: intervalMs,
		MaxRuns:    maxRuns,
		CreatedMs:  now,
		LastRunMs:  0,
		Count:      0,
	}
	return nil
}

func (s *Scheduler) Remove(id string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, exists := s.jobs[id]; !exists {
		return false
	}
	delete(s.jobs, id)
	return true
}

func (s *Scheduler) Tick(id string) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	job, ok := s.jobs[id]
	if !ok {
		return 0, fmt.Errorf("job %s not found", id)
	}
	if job.MaxRuns > 0 && job.Count >= job.MaxRuns {
		return job.Count, fmt.Errorf("job %s exhausted (max=%d)", id, job.MaxRuns)
	}
	job.LastRunMs = time.Now().UnixMilli()
	job.Count++
	return job.Count, nil
}

func (s *Scheduler) List() []string {
	s.mu.Lock()
	defer s.mu.Unlock()
	ids := make([]string, 0, len(s.jobs))
	for id := range s.jobs {
		ids = append(ids, id)
	}
	return ids
}

func (s *Scheduler) Status(id string) (*Job, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	job, ok := s.jobs[id]
	if !ok {
		return nil, fmt.Errorf("job %s not found", id)
	}
	return job, nil
}

func (s *Scheduler) Run() {
	reader := bufio.NewReader(os.Stdin)
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) == 0 {
			continue
		}
		cmd := parts[0]
		switch cmd {
		case "add":
			if len(parts) < 3 {
				fmt.Println("ERR usage: add <id> <interval_ms> [max_runs]")
				continue
			}
			interval, _ := strconv.Atoi(parts[2])
			maxRuns := 0
			if len(parts) >= 4 {
				maxRuns, _ = strconv.Atoi(parts[3])
			}
			if err := s.Add(parts[1], interval, maxRuns); err != nil {
				fmt.Println("ERR", err)
			} else {
				fmt.Println("OK")
			}
		case "remove":
			if len(parts) < 2 {
				fmt.Println("ERR usage: remove <id>")
				continue
			}
			if s.Remove(parts[1]) {
				fmt.Println("OK")
			} else {
				fmt.Println("ERR not found")
			}
		case "list":
			ids := s.List()
			b, _ := json.Marshal(ids)
			fmt.Println(string(b))
		case "tick":
			if len(parts) < 2 {
				fmt.Println("ERR usage: tick <id>")
				continue
			}
			n, err := s.Tick(parts[1])
			if err != nil {
				fmt.Println("ERR", err)
			} else {
				fmt.Println("ran", n)
			}
		case "status":
			if len(parts) < 2 {
				fmt.Println("ERR usage: status <id>")
				continue
			}
			j, err := s.Status(parts[1])
			if err != nil {
				fmt.Println("ERR", err)
			} else {
				b, _ := json.Marshal(j)
				fmt.Println(string(b))
			}
		case "quit", "exit":
			return
		default:
			fmt.Println("ERR unknown command:", cmd)
		}
	}
}

func main() {
	NewScheduler().Run()
}
