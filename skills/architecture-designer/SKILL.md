---
name: architecture-designer
description: "System design patterns with C4 model, ADRs, and NFRs"
version: 1.0.0
author: Alteriom
tags: [architecture, design, c4-model, adr, nfr]
license: MIT
platforms:
  - openclaw
  - claude-code
---


# Architecture Designer

**Purpose**: Design robust, scalable system architectures using proven patterns and decision frameworks.

**Works with**: C4 model, ADRs, NFR analysis, system design tools  
**License**: MIT (original work, inspired by AWS Well-Architected, Google Cloud Architecture Framework, Martin Fowler)

---

## When to Use

Use this skill when you need to:
- Design a new system or major component
- Evaluate architectural tradeoffs
- Document architectural decisions (ADRs)
- Identify non-functional requirements (NFRs)
- Refactor existing architecture
- Communicate system design to stakeholders

**Don't use this for**:
- Simple CRUD applications (start coding, refactor later)
- Proof-of-concept prototypes (focus on learning, not perfection)
- Well-understood patterns with no tradeoffs (just implement)

---

## Prerequisites

### 1. Understand the Problem Domain

**Think Before Coding** (Karpathy Principle #1):
- What problem are we solving?
- Who are the users?
- What are the constraints (cost, time, team size)?
- What's the expected scale (users, data, requests)?

**Questions to answer**:
```
Business Context:
- What's the business goal?
- What's the timeline?
- What's the budget?

Technical Context:
- Current system limitations?
- Integration requirements?
- Team expertise?
- Compliance/security needs?
```

### 2. Gather Requirements

**Non-Functional Requirements (NFRs)**:
- **Performance**: Response time, throughput, latency
- **Scalability**: Expected growth, peak load
- **Availability**: Uptime requirements (99.9%, 99.99%?)
- **Security**: Authentication, authorization, encryption
- **Maintainability**: Team size, code complexity
- **Cost**: Infrastructure, development, operational

**Example NFR Template**:
```markdown
## Non-Functional Requirements

### Performance
- API response time: < 200ms (p95)
- Page load time: < 2s
- Database queries: < 50ms

### Scalability
- Support 10K concurrent users
- Handle 1M requests/day
- Store 100GB data initially, 1TB in year 1

### Availability
- 99.9% uptime (43min downtime/month)
- RPO: 1 hour
- RTO: 4 hours

### Security
- OAuth 2.0 authentication
- End-to-end encryption for sensitive data
- SOC 2 compliance required
```

---

## Core Workflows

### Workflow 1: C4 Model Diagrams

**C4 = Context, Container, Component, Code**

Use C4 to communicate architecture at different zoom levels.

#### Level 1: System Context

Shows the system boundary and external actors.

```
[User] --> [Your System] --> [Email Service]
                 |
                 v
            [Database]
```

**Purpose**: Who uses the system? What does it integrate with?

**Example (text-based)**:
```
User (Customer) --> Web App --> Payment Gateway (Stripe)
                       |
                       v
                  PostgreSQL Database
```

#### Level 2: Container Diagram

Shows applications and data stores within the system.

```
[Web App]     [API Server]     [Background Jobs]
    |              |                  |
    +-------> [PostgreSQL] <----------+
    |              |                  |
    +-------> [Redis Cache] <---------+
```

**Purpose**: What are the deployable units? How do they communicate?

**Example**:
```
Containers:
- Next.js Frontend (Vercel)
- FastAPI Backend (Docker on AWS ECS)
- PostgreSQL (AWS RDS)
- Redis (ElastiCache)
- Worker Jobs (Celery on ECS)

Communication:
- Frontend → Backend: HTTPS/REST
- Backend → Database: PostgreSQL wire protocol
- Backend → Redis: Redis protocol
- Workers → Queue: Redis pub/sub
```

#### Level 3: Component Diagram

Shows components within a container.

```
API Server:
  - Auth Service
  - User Service
  - Order Service
  - Payment Service
  - Notification Service
```

**Purpose**: What are the logical building blocks? How are they organized?

#### Level 4: Code

UML class diagrams, sequence diagrams (optional, often unnecessary).

**Simplicity First** (Karpathy Principle #2): Stop at Level 2-3 for most projects. Code-level diagrams are rarely worth the maintenance burden.

---

### Workflow 2: Architecture Decision Records (ADRs)

**Purpose**: Document *why* decisions were made, not just *what*.

**ADR Template**:
```markdown
# ADR-001: Use PostgreSQL for Primary Database

## Status
Accepted

## Context
We need a database for our e-commerce platform. Requirements:
- ACID transactions (money involved)
- Complex queries (reporting, analytics)
- Strong consistency
- Team has SQL experience

Alternatives considered:
- MongoDB (flexible schema, but weak consistency)
- DynamoDB (scalable, but limited query flexibility)
- MySQL (similar to PostgreSQL, but weaker JSON support)

## Decision
Use PostgreSQL 15 with TimescaleDB extension for time-series data.

## Consequences

### Positive
- Strong ACID guarantees for financial data
- Excellent JSON support (JSONB)
- Team already knows SQL
- Rich ecosystem (pgBouncer, pg_stat_statements)

### Negative
- Horizontal scaling requires sharding (complex)
- Higher learning curve for TimescaleDB
- Cloud costs ~$200/month for production

### Risks
- Database becomes bottleneck at >10K concurrent users
- Mitigation: Add read replicas, implement caching

## Verification
- [x] Can handle expected load (load tested with 5K users)
- [x] Backup/restore tested
- [x] Team trained on PostgreSQL best practices
```

**When to write an ADR**:
- Technology choice (database, framework, cloud provider)
- Architectural pattern (microservices, monolith, serverless)
- Security approach (authentication, authorization)
- Deployment strategy (CI/CD, blue/green, canary)

**When NOT to write an ADR**:
- Obvious choices (use HTTPS, not HTTP)
- Temporary decisions (prototyping tools)
- Low-impact choices (logging library)

---

### Workflow 3: Tradeoff Analysis

**Goal-Driven Execution** (Karpathy Principle #4): Every architecture decision is a tradeoff. Make them explicit.

**Tradeoff Matrix Template**:
```markdown
## Option 1: Monolith (Rails)
| Criterion         | Score | Notes                        |
|-------------------|-------|------------------------------|
| Time to market    | ★★★★★ | Fast development             |
| Scalability       | ★★☆☆☆ | Vertical scaling only        |
| Team expertise    | ★★★★☆ | Team knows Rails             |
| Operational cost  | ★★★★★ | Single server                |
| Deployment ease   | ★★★★★ | Simple deploy                |
| **Total**         | 21/25 | Good for MVP                 |

## Option 2: Microservices (Node.js)
| Criterion         | Score | Notes                        |
|-------------------|-------|------------------------------|
| Time to market    | ★★☆☆☆ | Complex setup                |
| Scalability       | ★★★★★ | Horizontal scaling           |
| Team expertise    | ★★★☆☆ | Learning curve               |
| Operational cost  | ★★☆☆☆ | Multiple services            |
| Deployment ease   | ★★☆☆☆ | K8s required                 |
| **Total**         | 14/25 | Overkill for MVP             |

## Decision: Start with Monolith
- Rationale: Speed to market is #1 priority
- Migration path: Extract microservices later if needed
```

**Weight criteria** by importance:
```markdown
Weighted Scores:
- Time to market (3x weight): Critical
- Scalability (1x): Can defer
- Team expertise (2x): Important

Monolith: 21 → 58 (weighted)
Microservices: 14 → 36 (weighted)
```

---

### Workflow 4: NFR Verification

**Before launch**, verify all NFRs:

```bash
# Performance testing
ab -n 10000 -c 100 https://api.example.com/health
# Target: < 200ms avg response time

# Load testing
artillery run load-test.yml
# Target: Handle 10K concurrent users

# Availability testing
# Monitor uptime over 30 days
curl https://uptimerobot.com/api/...

# Security audit
npm audit
trivy image myapp:latest
# Target: Zero critical vulnerabilities
```

**Success Criteria**:
- [ ] All NFRs met or explicitly deferred
- [ ] Performance tests pass
- [ ] Security scan clean
- [ ] Disaster recovery tested

---

## Common Patterns

### Pattern 1: Layered Architecture

**When**: Standard web applications, team familiar with MVC.

```
┌─────────────────────────┐
│   Presentation Layer    │  (UI, API endpoints)
├─────────────────────────┤
│   Business Logic Layer  │  (Domain services)
├─────────────────────────┤
│   Data Access Layer     │  (Repositories, ORMs)
├─────────────────────────┤
│   Database              │  (PostgreSQL, etc.)
└─────────────────────────┘
```

**Advantages**:
- Simple to understand
- Clear separation of concerns
- Easy to test each layer

**Disadvantages**:
- Can become tightly coupled
- Performance overhead (layer crossing)

---

### Pattern 2: Hexagonal Architecture (Ports & Adapters)

**When**: Need to swap implementations (e.g., testing, multi-tenant).

```
        ┌──────────────┐
        │              │
   ┌────│    Domain    │────┐
   │    │    (Core)    │    │
   │    │              │    │
   │    └──────────────┘    │
   │                        │
[Port]                   [Port]
   │                        │
[Adapter]              [Adapter]
(HTTP API)           (PostgreSQL)
```

**Example**:
```typescript
// Port (interface)
interface UserRepository {
  findById(id: string): Promise<User>
  save(user: User): Promise<void>
}

// Domain (core)
class UserService {
  constructor(private repo: UserRepository) {}
  
  async activateUser(id: string) {
    const user = await this.repo.findById(id)
    user.activate()
    await this.repo.save(user)
  }
}

// Adapter (implementation)
class PostgresUserRepository implements UserRepository {
  async findById(id: string) { /* SQL query */ }
  async save(user: User) { /* SQL insert/update */ }
}

// Swap adapters for testing
class InMemoryUserRepository implements UserRepository {
  async findById(id: string) { /* in-memory lookup */ }
  async save(user: User) { /* store in Map */ }
}
```

**Advantages**:
- Testable (swap adapters)
- Flexible (add new adapters easily)
- Domain-focused

**Disadvantages**:
- More boilerplate
- Overkill for simple apps

---

### Pattern 3: Event-Driven Architecture

**When**: Loose coupling needed, asynchronous processing.

```
[Service A] --event--> [Message Queue] --event--> [Service B]
                            |
                            +---------> [Service C]
```

**Example**:
```
Event: OrderPlaced
- Inventory Service: Decrement stock
- Email Service: Send confirmation
- Analytics Service: Track sale
- Shipping Service: Create shipment
```

**Advantages**:
- Decoupled services
- Scalable (add consumers)
- Resilient (queue buffers)

**Disadvantages**:
- Eventual consistency
- Complex debugging
- Requires infrastructure (RabbitMQ, Kafka)

---

## Common Pitfalls

### Pitfall 1: Over-Engineering

**Why it happens**: Anticipating future needs that never materialize.

**Symptoms**:
- Microservices for a simple CRUD app
- Complex abstractions for 3 database queries
- "We might need to scale to 1M users" (current: 10 users)

**How to avoid**:
- **YAGNI** (You Aren't Gonna Need It)
- Start simple, refactor when pain points emerge
- Measure before optimizing

**Surgical Changes** (Karpathy Principle #3): Build the simplest thing that works. Refactor when requirements change.

---

### Pitfall 2: Analysis Paralysis

**Why it happens**: Endless research, no code written.

**Symptoms**:
- 20 ADRs, zero commits
- Comparing 15 databases for weeks
- Perfect architecture on paper, nothing deployed

**How to avoid**:
- Set decision deadlines (e.g., "Choose database by Friday")
- Build prototypes to test assumptions
- Accept that decisions can change later

**Timebox architecture design**:
- 1-2 days for small projects
- 1-2 weeks for large projects
- After that, start coding

---

### Pitfall 3: Ignoring NFRs

**Why it happens**: Focusing only on features, not quality attributes.

**Symptoms**:
- No performance requirements ("make it fast")
- No availability targets ("should work")
- Security as afterthought

**How to avoid**:
- Write NFRs before designing architecture
- Test NFRs before launch
- Monitor NFRs in production

---

## Verification Checklist

Before considering architecture complete:

**Documentation**:
- [ ] C4 diagrams created (at least Context + Container)
- [ ] Key ADRs written (technology choices, patterns)
- [ ] NFRs documented and prioritized

**Validation**:
- [ ] Architecture reviewed by team
- [ ] Tradeoffs explicit and justified
- [ ] Prototype built (for risky decisions)
- [ ] Load tested (if performance-critical)

**Communication**:
- [ ] Stakeholders understand the design
- [ ] Team can implement the design
- [ ] Documentation accessible (wiki, GitHub, Confluence)

---

## Integration with Other Skills

**Combine with**:
- `requirements-analysis` - Gather NFRs before designing
- `architecture-patterns` - Pick specific patterns (CQRS, Event Sourcing)
- `prd-to-ddd-design` - Map domain model to architecture
- `task-decomposer` - Break architecture into implementation tasks

**Example Workflow**:
```bash
# 1. Gather requirements (requirements-analysis)
# Document NFRs, constraints, stakeholders

# 2. Design architecture (architecture-designer)
# Create C4 diagrams, write ADRs

# 3. Pick patterns (architecture-patterns)
# Choose layered vs hexagonal vs event-driven

# 4. Map domain (prd-to-ddd-design)
# Identify bounded contexts, aggregates

# 5. Break down tasks (task-decomposer)
# Create implementation tasks from architecture
```

---

## References

**Frameworks**:
- AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/
- Google Cloud Architecture Framework: https://cloud.google.com/architecture/framework
- Microsoft Azure Architecture Center: https://learn.microsoft.com/en-us/azure/architecture/

**Books & Articles**:
- Martin Fowler - Software Architecture Guide: https://martinfowler.com/architecture/
- C4 Model: https://c4model.com/
- ADR GitHub: https://adr.github.io/

**Related Skills**:
- `architecture-patterns` - Specific architectural patterns
- `requirements-analysis` - Gathering requirements
- `prd-to-ddd-design` - Domain-Driven Design

---

## Meta: Skill Quality

**Incorporates Karpathy Principles**:
- ✅ Think Before Coding - Understand problem before designing
- ✅ Simplicity First - Start with simplest architecture
- ✅ Surgical Changes - Refactor when needed, not prematurely
- ✅ Goal-Driven - NFRs define success criteria

**Tested With**:
- Real-world projects (e-commerce, SaaS, APIs)
- Teams of 2-50 engineers
- Systems handling 100-10M requests/day

**Last Updated**: April 13, 2026  
**Maintainer**: Alteriom  
**License**: MIT

**Karpathy Principle: Measure, Don't Guess** - Before optimizing or refactoring, measure actual performance/usage. Profile before you fix. Data beats intuition.
