# Hybrid Virtual File System (FSS)

A **custom virtual file system** built from scratch in **C**, exposed via a **FastAPI backend**, and managed through a **Vue.js frontend**.

This project began as a low-level learning experiment and evolved into a realistic backend system that demonstrates **filesystem design**, **memory management**, **API architecture**, and **multi-user isolation**.

---

## 📌 Overview

Hybrid FSS simulates a real-world file system environment where users can create, manage, and store files and directories in a virtual space.  
The core filesystem is implemented in C for performance and low-level control, while modern web technologies provide accessibility and usability.

---

## 🚀 Features

### ✅ Implemented

- Create directories
- Delete directories (recursive)
- Create files
- Delete files
- Read file contents
- Write file contents
- Persistent storage using binary dump file
- Thread-safe access via backend locking
- C filesystem core exposed via shared library
- Multi-user isolated virtual roots

---

## 🧩 Architecture & Design

### Core (C Layer)

- Custom hashmap (`obj_map`) for managing files and directories
- Explicit memory ownership (hashmap does **not** free `void *value`)
- Manual memory management
- Portable shared library support:
  - Linux: `.so`
  - Windows: `.dll`

### Backend (FastAPI)

- REST API interface to filesystem core
- Thread-safe request handling
- Centralized locking mechanism
- User-root isolation

### Frontend (Vue.js)

- Web interface for filesystem operations
- REST-based communication
- Modular UI design

---

## 🛠️ Tech Stack

| Layer     | Technology |
|-----------|------------|
| Core      | C          |
| Backend   | FastAPI    |
| Frontend  | Vue 3      |
| UI        | Vuetify    |
| Client    | Axios      |
| Storage   | Binary Dump |

---

## 🔒 Security Considerations

- Path normalization prevents directory traversal (`../`)
- All user paths are sandboxed to private roots
- Cross-user directory access is restricted
- Input validation at API level
- Controlled memory access in C layer

---

## 🔮 Planned Features

### UI Enhancements

- File explorer interface
- Folder navigation
- File preview & editing
- Empty-directory indicators
- Context menus

### System Improvements

- 🗑️ Soft delete (trash system)
- ✂️ Copy / Cut / Move support
- 👥 Authentication & session management
- 🔐 Role-based permissions
- 📦 Database or object storage backend
- 🧠 AI-powered file search & summarization (optional)

---

## 📂 Project Structure (High-Level)
```
backend/
├── native/                 # C-based filesystem core
│   ├── src/                # Core source files
│   ├── include/            # Header files
│   ├── build/              # Compiled objects / shared library
│   └── Makefile            # Build configuration
│
├── data/                   # Persistent storage
│   ├── user_1.dump          # User filesystem dump
│   ├── user_2.dump
│   └── system.dump
│
├── server.py                 # FastAPI entry point
├── file_system.py        # Wrapping all C functions to make it usable for python.
```
---

## ⚙️ Setup (High-Level)

### Prerequisites

- GCC / Clang
- Python 3.9+
- Node.js 18+
- npm / yarn

### Build Core

```bash
cd native
gcc -shared -fPIC   -Iinclude   src/*.c   -o build/fslib.so

```

### Run Backend

```bash
cd backend
source .venv/bin/activate
fastapi run server.py
```

### If requirements are not installed 

```bash
python -m venv .venv
source .venv/bin/activate
pip install "fastapi[standard]"
python3 -m pip install pymongo
```
---
###🎯 Project Motivation

This project was created to:

- Understand how filesystems work internally

- Practice low-level memory management

- Design scalable backend systems

- Integrate C systems with modern web frameworks

- Learn through incremental system evolution

It is **not tutorial code**, but a real system grown through experimentation, refactoring, and design trade-offs.
---

###📈 Learning Outcomes

Through this project, I gained experience in:

- Data structure design in C

- Manual memory handling

- API design

- Multithreading and synchronization

- Backend–frontend integration

- System-level debugging

---

###🧑‍💻 Author

**Nilabha Samadder**

“I didn’t want this effort to be wasted — I wanted it to live as a real backend system.”
