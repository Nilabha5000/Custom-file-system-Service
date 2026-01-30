# Hybrid Virtual File System (FSS)

A custom **virtual file system** built from scratch in **C**, exposed through a **FastAPI backend**, and operated via a **Vue.js frontend**.

This project started as a learning experiment but evolved into a realistic backend system demonstrating **filesystem design**, **data structures**, **API design**, and **multi-user isolation**.

---

## 🚀 Features

### ✅ Current (Implemented)

- Create directories
- Delete directories (recursive)
- Create files
- Delete files
- Read file contents
- Write file contents
- Persistent storage using a binary dump file
- Thread-safe access via backend locking
- C filesystem core exposed to backend using a shared library

### 🧩 Design Highlights

- Custom hashmap (`obj_map`) for directories and files
- Explicit memory ownership (hashmap does **not** free `void *value`)
- Platform-independent core (Linux `.so`, Windows `.dll`)

---

## 🔮 Future Scope (Planned, Not Implemented Yet):

- File explorer UI (folders & files)
- Navigation (back, open)
- Create / delete files & directories
- File editor dialog
- Visual empty-directory states

Tech:

- Vue 3
- Vuetify
- Axios

---

## 🔒 Security Considerations

- Path normalization prevents directory traversal (`../`)
- User paths are resolved relative to their root
- Direct access to other users' directories is blocked

---

## 🚀 Planned Enhancements

- 🗑️ Trash system (soft delete)
- ✂️ Copy / Cut / Move support
- 👥 Authentication & sessions
- 🔐 Role-based permissions
- 📦 Replace dump file with DB or object storage
- 🧠 AI-powered file search / summarization (optional)

---

## 🎯 Why This Project Exists

This project was built to:

- Understand filesystem internals
- Practice low-level memory management in C
- Learn how real backend systems evolve
- Bridge low-level systems with modern web stacks

It is **not tutorial code**, but a system grown incrementally with conscious design trade-offs.

---

## 🧑‍💻 Author

Built by **Nilabha Samadder**

> "I didn’t want this effort to be wasted — I wanted it to live as a real backend system."

---

## 📜 License

MIT (or choose one)

