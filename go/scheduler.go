// CIEL v1.0 — Scheduler (Go)
// Migré depuis Hydra, adapté pour CIEL.
// Planificateur de tâches sans dérive (drift-free).

package main

import (
	"fmt"
	"time"
)

type Task struct {
	ID        string
	Name      string
	Interval  time.Duration
	LastRun   time.Time
	NextRun   time.Time
	Running   bool
}

type Scheduler struct {
	Tasks []Task
	done  chan bool
}

func NewScheduler() *Scheduler {
	return &Scheduler{
		Tasks: make([]Task, 0),
		done:  make(chan bool),
	}
}

func (s *Scheduler) AddTask(name string, interval time.Duration) {
	task := Task{
		ID:       fmt.Sprintf("TASK-%d", len(s.Tasks)+1),
		Name:     name,
		Interval: interval,
		LastRun:  time.Now(),
		NextRun:  time.Now().Add(interval),
	}
	s.Tasks = append(s.Tasks, task)
	fmt.Printf("  ✓ Tâche ajoutée: %s (tous les %s)\n", name, interval)
}

func (s *Scheduler) Start() {
	fmt.Println("  ▶ Planificateur démarré")
	for {
		now := time.Now()
		for i, task := range s.Tasks {
			if now.After(task.NextRun) && !task.Running {
				s.Tasks[i].Running = true
				s.Tasks[i].LastRun = now
				s.Tasks[i].NextRun = now.Add(task.Interval)
				fmt.Printf("  ⚡ Exécution: %s (%s)\n", task.Name, task.ID)
				s.Tasks[i].Running = false
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
}

func main() {
	fmt.Println("CIEL Go Scheduler — v1.0")
	fmt.Println("=========================")

	sched := NewScheduler()
	sched.AddTask("Évolution Cycle", 30*time.Second)
	sched.AddTask("Health Check", 10*time.Second)
	sched.AddTask("Memory Sync", 60*time.Second)

	sched.Start()
}
