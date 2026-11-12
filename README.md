# OnePay API 🚀

API en FastAPI para la gestión de membresías, clientes y pagos recurrentes.

El modelo de dominio sigue la separación clásica de una pasarela de pagos:
**Plan → Subscription → Invoice → Transaction**. Los importes se manejan en
enteros (unidad mínima de la moneda, nunca `float`) y las claves foráneas de
las tablas con valor contable usan `ondelete="RESTRICT"` para no perder
historial.

## Stack

- FastAPI 0.116 · SQLModel 0.0.27 · Pydantic 2.11 · SQLAlchemy 2.0
- PostgreSQL 16 (Docker) · Alembic
- PyJWT · passlib/bcrypt

## Estado actual

| Módulo | Estado |
| --- | --- |
| Modelo de datos completo (planes, clientes, suscripciones, facturas, transacciones) | ✅ |
| Migraciones Alembic | ✅ |
| CRUD de clientes (con soft delete y validación de duplicados) | ✅ |
| CRUD de planes | ✅ |
| Login con JWT | 🚧 parcial |
| Suscripciones · Facturación · Transacciones | ⬜ pendiente |
| Integración con proveedores de pago | ⬜ pendiente |

---

## Roadmap

### Fase 0 — Base segura

- [ ] Dependencia `get_current_user` que verifique firma y expiración del JWT
- [ ] Dependencia `require_admin` para las rutas de gestión
- [ ] Configuración centralizada con `pydantic-settings` (fallar al arrancar si falta una variable)
- [ ] Credenciales fuera del repositorio: `alembic.ini` y `migrations/env.py` leyendo la URL desde el entorno
- [ ] Desactivar el log de headers de request y el `echo` de SQL del engine
- [ ] Alembic como única fuente de verdad del esquema (quitar `create_all` del arranque)

### Fase 1 — Identidad coherente

- [ ] Unificar el modelo de identidad: definir si `Customer` se autentica o si `User` es el único con credenciales
- [ ] Roles explícitos en lugar de flags sueltos (`is_admin` / `is_superuser`)
- [ ] Refresh tokens y expiración configurable
- [ ] Rate limiting en `/login`
- [ ] Migrar el hashing a `bcrypt` directo o `argon2` (passlib está sin mantenimiento)

### Fase 2 — Motor de suscripciones y facturación

- [ ] Router de suscripciones con máquina de estados y transiciones válidas explícitas
      (`incomplete → active → past_due → canceled / unpaid`)
- [ ] Cálculo de periodos de facturación desde `interval` e `interval_count`
- [ ] Generación de facturas a partir de la suscripción (nunca creadas a mano)
- [ ] Aplicación de transacciones sobre facturas en una única transacción de base de datos,
      con bloqueo de fila, manteniendo la invariante `amount_due = amount_paid + amount_remaining`
- [ ] Validación de moneda en cascada (plan → suscripción → factura → transacción)
- [ ] Schemas de respuesta (`*Public`) para suscripciones, facturas y transacciones
- [ ] Índice único parcial para permitir dar de alta de nuevo a un cliente eliminado
- [ ] Límites y orden estable en la paginación (`limit` acotado, `ORDER BY id`, total en la respuesta)

### Fase 3 — Comportamiento de pasarela

- [ ] Soporte de `Idempotency-Key` con tabla de claves (endpoint, hash del request, respuesta)
- [ ] Restricción `UNIQUE` sobre `provider_transaction_id`
- [ ] Interfaz abstracta `PaymentProvider` con implementación `MANUAL` y una pasarela real en modo test
- [ ] Endpoint de webhooks con verificación de firma y deduplicación por `event_id`

### Fase 4 — Producción y documentación

- [ ] `Dockerfile` multi-stage y `docker-compose` completo con healthcheck
- [ ] Endpoint `/health`
- [ ] Logging estructurado con `request_id` (en lugar de `print`)
- [ ] Suite de tests real: fixtures de autenticación, factories y cobertura de la máquina
      de estados y de la idempotencia
- [ ] CI con `pytest` y `ruff`
- [ ] Documentar las decisiones de diseño: importes enteros, `RESTRICT` en las FK,
      garantía de exactly-once

### Fuera de alcance por ahora

Dunning y reintentos automáticos, proveedores adicionales a los dos implementados,
y métricas/observabilidad avanzada.


# OnePay-API

🚧 **Work In Progress**: I am intentionally building the core architecture and database models of this API completely from scratch (without AI assistance) to deeply solidify my understanding of FastAPI, SQLModel, and advanced PostgreSQL relationships.
