# 🛒 E-Commerce Order & Inventory Service

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-black?logo=jsonwebtokens)

A backend service for product inventory and order checkout, built around two problems every real e-commerce platform has to get right: **preventing overselling under concurrent traffic** and **preventing duplicate orders on retry**.

---

## 📌 The Problem

When multiple customers try to buy the last unit of a product at the same instant, a naive implementation lets both requests read the same stock count, both believe the item is available, and both succeed — potentially causing overselling.

Separately, if a client retries a request (network timeout, a double-clicked "Place Order" button), a naive implementation can create two orders for one purchase.

## ✅ The Solution

| Problem | Fix |
|---|---|
| Two orders both buy the last unit | **Row-level locking** (`SELECT ... FOR UPDATE`) — a product row is locked for the duration of a transaction, so a competing request has to wait until the first transaction commits |
| Duplicate orders on retry | **Idempotency keys** — a unique database constraint ensures the same idempotency key cannot create two orders |
| Two multi-product orders deadlocking each other | **Sorted lock acquisition** — product rows are locked in a consistent order across requests |

---

## 🧱 Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL, SQLAlchemy ORM
- **Auth:** JWT (`python-jose`), bcrypt hashing (`passlib`)
- **Containerization:** Docker, Docker Compose

## 🏗️ Architecture

```text
Client
  │
  ▼
FastAPI
  │
  ├── JWT Authentication
  ├── Product APIs
  └── Order & Inventory Logic
          │
          ▼
      SQLAlchemy
          │
          ▼
      PostgreSQL
          │
          ├── Users
          ├── Products
          ├── Orders
          └── OrderItems

Docker Compose
  ├── FastAPI Container (`order_api`)
  └── PostgreSQL Container (`order_db`)
