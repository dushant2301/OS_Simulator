# 🚦 Traffic Intersection Simulator (Deadlock & Starvation)

## 📌 Overview

This project is a **Traffic Intersection Simulator** built to demonstrate important **Operating System concepts** such as:

* Deadlock
* Starvation
* Synchronization
* Resource Allocation

It simulates a **four-way traffic junction** where cars arrive from all directions (North, South, East, West) and attempt to cross the intersection.

---

## 🎯 Objective

The goal of this simulator is to:

* Visualize how **deadlock occurs** in real-world systems
* Demonstrate how **proper scheduling avoids deadlock**
* Ensure **no starvation** using fair allocation techniques
* Provide an **interactive and animated learning experience**

---

## 🧠 Concept Mapping (OS ↔ Real World)

| Traffic System  | OS Concept        |
| --------------- | ----------------- |
| Cars            | Processes         |
| Roads           | Resources         |
| Intersection    | Critical Section  |
| Traffic Signals | Semaphores        |
| Waiting Cars    | Blocked Processes |

---

## ⚙️ Features

### 🚗 Simulation Features

* Real-time car movement from 4 directions
* Smooth animation with realistic motion
* Queue system (FIFO) for each direction

### 🚦 Traffic Control

* Automatic traffic signal system
* Round-robin scheduling for fairness
* Adjustable simulation speed

### 💀 Deadlock Simulation

* Toggle to **enable/disable deadlock**
* Shows cars stuck in circular wait
* Visual indication of deadlock state

### ✅ Deadlock Prevention

* Controlled access to intersection
* Ordered scheduling to avoid circular wait

### ⚖️ Starvation Prevention

* Each direction gets equal opportunity
* No indefinite waiting for any queue

### 🖥️ GUI Features

* Clean and modern UI
* Top-down intersection view
* Real-time statistics panel:

  * Active signal
  * Queue sizes
  * System state

---

## 🏗️ Project Structure

```bash
project/
│── main.py              # Entry point of the simulator
│── car.py               # Car class (movement & behavior)
│── road.py              # Road & queue management
│── signal.py            # Traffic signal logic
│── controller.py        # Deadlock handling & scheduling
│── utils.py             # Helper functions
```

---

## 🔄 How It Works

### 1️⃣ Car Generation

* Cars are generated dynamically for each direction
* Each car joins its respective queue

---

### 2️⃣ Queue Management

* Each road maintains a **FIFO queue**
* Cars wait until signal turns green

---

### 3️⃣ Traffic Signal Logic

* Signals operate in **round-robin scheduling**
* Only one direction is allowed at a time

---

### 4️⃣ Intersection Handling

* Intersection acts as a **critical section**
* Only permitted cars can enter

---

### 5️⃣ Deadlock Scenario

When deadlock is enabled:

* All directions try to enter simultaneously
* Each waits for others → circular wait
* System freezes (deadlock state)

---

### 6️⃣ Deadlock Resolution

* Controlled scheduling avoids circular wait
* Only one direction proceeds at a time

---

### 7️⃣ Starvation Prevention

* Every queue gets turn
* Ensures fairness

---

## 🎮 Controls

| Key/Button      | Action                  |
| --------------- | ----------------------- |
| Start           | Begin simulation        |
| Pause           | Pause simulation        |
| Reset           | Restart system          |
| Toggle Deadlock | Enable/Disable deadlock |
| Speed Control   | Adjust simulation speed |

---

## 🧪 Sample Output (Console)

```text
North cars moving...
East waiting...
South waiting...
West waiting...

Deadlock Enabled!
All cars stuck in intersection.
```

---

## 📊 System States

* 🟢 Normal Mode → Smooth traffic flow
* 🔴 Deadlock Mode → Cars stuck
* 🟡 Recovery Mode → System resolves deadlock

---

## 🧩 Technologies Used

* Python
* Pygame / Tkinter (GUI & animation)
* OOP Concepts
* Basic Synchronization Logic

---

## 🚀 Future Enhancements

* AI-based traffic optimization
* Emergency vehicle priority
* Multi-lane traffic simulation
* Real-world traffic data integration

---

## 📚 Learning Outcomes

* Understanding of **deadlock conditions**
* Implementation of **scheduling algorithms**
* Visualization of OS concepts
* Practical knowledge of synchronization

---

## 🏁 Conclusion

This simulator successfully demonstrates how **deadlock occurs and how it can be prevented** using proper scheduling techniques. It also ensures fairness by preventing starvation, making it a strong real-world example of operating system concepts.

---

## 🙏 Acknowledgement

This project was developed as part of an **Operating Systems practical assignment** to visualize process synchronization and resource management concepts.

---

## ⭐ If you like this project, consider giving it a star!
