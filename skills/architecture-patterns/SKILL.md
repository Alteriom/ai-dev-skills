---
name: architecture-patterns
description: "Common software architecture patterns (Layered, Hexagonal, CQRS, Event Sourcing)"
version: 1.0.0
author: Alteriom
tags: [architecture, patterns, microservices, cqrs, hexagonal]
license: MIT
platforms:
  - openclaw
  - claude-code
---


# Architecture Patterns

**Purpose**: Apply proven architectural patterns to solve common system design challenges.

**Works with**: Any technology stack  
**License**: MIT (original work, inspired by Microsoft Azure patterns, O'Reilly Software Architecture Patterns, Martin Fowler)

---

## When to Use

Use this skill when you need to:
- Select an architectural pattern for a new system
- Understand tradeoffs between patterns
- Refactor an existing architecture
- Solve specific design problems (scalability, maintainability, performance)

**Don't use this for**:
- Simple scripts or utilities (no architecture needed)
- Well-understood domains with obvious patterns
- When custom design is clearly better than standard patterns

---

## Prerequisites

### 1. Understand Your Requirements

**Think Before Coding** (Karpathy Principle #1):
- What's the primary challenge? (scale, complexity, team size, change frequency)
- What are the NFRs? (performance, availability, maintainability)
- What are the constraints? (budget, timeline, team expertise)

**Pattern Selection Criteria**:
```
Scalability needs:
- Current load: ___ requests/second
- Growth rate: ___ % per year
- Peak load: ___ x average

Complexity:
- Number of features: ___ (small < 10, medium < 50, large > 50)
- Team size: ___ developers
- Change frequency: ___ deploys per week

Performance:
- Latency requirements: ___ ms
- Throughput needs: ___ req/s
- Data size: ___ GB/TB
```

---

## Core Workflows

### Pattern 1: Layered Architecture (N-Tier)

**When to use**:
- Standard web applications
- Team familiar with MVC
- Clear separation of UI, business logic, data

**Structure**:
```
┌─────────────────────────┐
│  Presentation Layer     │  UI, API controllers
├─────────────────────────┤
│  Application Layer      │  Use cases, orchestration
├─────────────────────────┤
│  Domain Layer           │  Business logic, entities
├─────────────────────────┤
│  Infrastructure Layer   │  Database, external APIs
└─────────────────────────┘
```

**Example (TypeScript/Express)**:
```typescript
// Presentation Layer
app.post('/users', async (req, res) => {
  const result = await createUserUseCase.execute(req.body)
  res.json(result)
})

// Application Layer
class CreateUserUseCase {
  constructor(private userRepo: UserRepository) {}
  
  async execute(data: CreateUserDTO) {
    const user = User.create(data)  // Domain
    await this.userRepo.save(user)  // Infrastructure
    return user
  }
}

// Domain Layer
class User {
  static create(data: CreateUserDTO) {
    // Validation, business rules
    if (!data.email.includes('@')) throw new Error('Invalid email')
    return new User(data)
  }
}

// Infrastructure Layer
class PostgresUserRepository implements UserRepository {
  async save(user: User) {
    await db.query('INSERT INTO users ...', user)
  }
}
```

**Advantages**:
- ✅ Simple to understand
- ✅ Clear separation of concerns
- ✅ Easy to test each layer
- ✅ Team can work on different layers independently

**Disadvantages**:
- ❌ Can become tightly coupled (layers depend on each other)
- ❌ Performance overhead (crossing layers)
- ❌ Temptation to leak business logic into presentation

**Verification**:
- [ ] Each layer has single responsibility
- [ ] Dependencies flow downward only (no circular deps)
- [ ] Business logic isolated in domain layer
- [ ] Database details hidden from upper layers

---

### Pattern 2: Hexagonal Architecture (Ports & Adapters)

**When to use**:
- Need to swap implementations (testing, multi-cloud)
- Business logic must be technology-agnostic
- Multiple interfaces (REST API, CLI, event-driven)

**Structure**:
```
        ┌──────────────┐
        │   Domain     │
        │   (Core)     │  Business rules, entities
        └──────────────┘
              ↑  ↓
         [Ports (Interfaces)]
              ↑  ↓
    ┌─────────┴──┴─────────┐
[HTTP API]            [PostgreSQL]
[GraphQL]             [Redis]
[CLI]                 [Email Service]
(Adapters)            (Adapters)
```

**Example**:
```typescript
// Port (interface)
interface PaymentGateway {
  charge(amount: number, token: string): Promise<PaymentResult>
}

// Domain (core business logic)
class OrderService {
  constructor(private payment: PaymentGateway) {}
  
  async checkout(order: Order) {
    const total = order.calculateTotal()
    const result = await this.payment.charge(total, order.paymentToken)
    
    if (result.success) {
      order.markAsPaid()
    }
    
    return result
  }
}

// Adapter 1: Stripe
class StripePaymentGateway implements PaymentGateway {
  async charge(amount: number, token: string) {
    const stripeResult = await stripe.charges.create({ amount, source: token })
    return { success: stripeResult.status === 'succeeded' }
  }
}

// Adapter 2: PayPal (easy to swap)
class PayPalPaymentGateway implements PaymentGateway {
  async charge(amount: number, token: string) {
    const paypalResult = await paypal.payment.create({ amount, token })
    return { success: paypalResult.state === 'approved' }
  }
}

// Adapter 3: Test/Mock (for testing)
class MockPaymentGateway implements PaymentGateway {
  async charge(amount: number, token: string) {
    return { success: true }  // Always succeeds in tests
  }
}
```

**Advantages**:
- ✅ Business logic independent of frameworks
- ✅ Easy to test (swap real adapters with mocks)
- ✅ Can add new interfaces without changing core
- ✅ Technology choices deferred until needed

**Disadvantages**:
- ❌ More boilerplate (interfaces everywhere)
- ❌ Overkill for simple applications
- ❌ Requires discipline to maintain boundaries

**Verification**:
- [ ] Domain has zero framework dependencies
- [ ] All external dependencies behind interfaces
- [ ] Can swap adapters without changing domain
- [ ] Tests use mock adapters

---

### Pattern 3: Microservices Architecture

**When to use**:
- Large teams (>20 developers)
- Independently deployable features
- Different scaling needs per service
- Polyglot requirements (different languages/frameworks)

**Structure**:
```
[API Gateway]
     |
     +---> [User Service] --> [User DB]
     +---> [Order Service] --> [Order DB]
     +---> [Payment Service] --> [Payment DB]
     +---> [Notification Service] --> [Message Queue]
```

**Example (Service Boundaries)**:
```
User Service:
- POST /users (register)
- GET /users/:id
- PUT /users/:id
- Authentication

Order Service:
- POST /orders (create)
- GET /orders/:id
- GET /users/:userId/orders
- Calls User Service to validate user

Payment Service:
- POST /payments (charge)
- GET /payments/:id
- Calls Order Service to get order details

Notification Service:
- Listens to events (OrderCreated, PaymentSuccess)
- Sends emails, SMS, push notifications
```

**Communication**:
```typescript
// Synchronous (REST)
const user = await fetch('http://user-service/users/123')

// Asynchronous (Events)
eventBus.publish('OrderCreated', { orderId: '456', userId: '123' })
```

**Advantages**:
- ✅ Independent deployment (update one service without others)
- ✅ Independent scaling (scale hot services only)
- ✅ Technology diversity (Node.js + Python + Go)
- ✅ Team autonomy (own their service)

**Disadvantages**:
- ❌ Operational complexity (many deployments, logs, monitoring)
- ❌ Network latency (service-to-service calls)
- ❌ Data consistency challenges (distributed transactions)
- ❌ Testing complexity (integration tests across services)

**Verification**:
- [ ] Each service has single business capability
- [ ] Services communicate via APIs/events (not shared database)
- [ ] Each service has own database
- [ ] Can deploy services independently
- [ ] Circuit breakers for resilience

**Simplicity First** (Karpathy Principle #2): Start with monolith. Extract microservices only when team size or scaling demands it.

---

### Pattern 4: CQRS (Command Query Responsibility Segregation)

**When to use**:
- Read and write workloads differ significantly
- Complex domain logic on writes, simple reads
- Need to scale reads independently

**Structure**:
```
Commands (Write):
[Create Order] --> [Write Model] --> [Event Store]
[Update Inventory]       |
                         v
                    [Events Published]
                         |
                         v
Queries (Read):     [Read Model]
[Get Orders] <---   (Denormalized, optimized for queries)
[Get Inventory]
```

**Example**:
```typescript
// Command (Write)
class CreateOrderCommand {
  userId: string
  items: OrderItem[]
}

class OrderCommandHandler {
  async handle(command: CreateOrderCommand) {
    // Complex business logic
    const order = Order.create(command)
    
    // Validate inventory
    await this.inventoryService.reserve(command.items)
    
    // Save to write database
    await this.orderRepo.save(order)
    
    // Publish event
    await this.eventBus.publish(new OrderCreatedEvent(order))
  }
}

// Query (Read)
class GetUserOrdersQuery {
  userId: string
}

class OrderQueryHandler {
  async handle(query: GetUserOrdersQuery) {
    // Simple SELECT from denormalized read model
    return await this.readDb.query(`
      SELECT * FROM user_orders_view 
      WHERE user_id = $1
    `, [query.userId])
  }
}

// Event Handler (Sync read model)
class OrderCreatedEventHandler {
  async handle(event: OrderCreatedEvent) {
    // Update read model
    await this.readDb.query(`
      INSERT INTO user_orders_view (user_id, order_id, total, status)
      VALUES ($1, $2, $3, $4)
    `, [event.userId, event.orderId, event.total, event.status])
  }
}
```

**Advantages**:
- ✅ Optimize reads and writes independently
- ✅ Scale read and write databases separately
- ✅ Read models tailored to specific queries
- ✅ Audit trail (event store)

**Disadvantages**:
- ❌ Eventual consistency (read model lags)
- ❌ More complex (two models to maintain)
- ❌ Overkill for simple CRUD

**Verification**:
- [ ] Commands modify state, queries don't
- [ ] Read and write models separated
- [ ] Events published for all state changes
- [ ] Read model eventually consistent

---

### Pattern 5: Event Sourcing

**When to use**:
- Need complete audit trail
- Time-travel queries ("state at time T")
- Complex business logic with many state transitions

**Structure**:
```
Commands --> [Aggregate] --> [Events] --> [Event Store]
                                  |
                                  v
                            [Event Handlers]
                                  |
                                  v
                          [Read Models / Projections]
```

**Example**:
```typescript
// Events (immutable facts)
class OrderCreatedEvent {
  orderId: string
  userId: string
  items: OrderItem[]
  timestamp: Date
}

class OrderPaidEvent {
  orderId: string
  paymentId: string
  amount: number
  timestamp: Date
}

class OrderShippedEvent {
  orderId: string
  trackingNumber: string
  timestamp: Date
}

// Aggregate (rebuilt from events)
class Order {
  id: string
  status: OrderStatus
  items: OrderItem[]
  
  static fromEvents(events: Event[]): Order {
    const order = new Order()
    
    for (const event of events) {
      order.apply(event)
    }
    
    return order
  }
  
  private apply(event: Event) {
    if (event instanceof OrderCreatedEvent) {
      this.id = event.orderId
      this.items = event.items
      this.status = 'CREATED'
    } else if (event instanceof OrderPaidEvent) {
      this.status = 'PAID'
    } else if (event instanceof OrderShippedEvent) {
      this.status = 'SHIPPED'
    }
  }
  
  // Commands produce new events
  ship(trackingNumber: string): OrderShippedEvent {
    if (this.status !== 'PAID') {
      throw new Error('Cannot ship unpaid order')
    }
    
    return new OrderShippedEvent(this.id, trackingNumber, new Date())
  }
}

// Time-travel query
async function getOrderStateAt(orderId: string, timestamp: Date) {
  const events = await eventStore.getEvents(orderId, { until: timestamp })
  return Order.fromEvents(events)
}
```

**Advantages**:
- ✅ Complete audit trail (every change recorded)
- ✅ Time-travel queries
- ✅ Replay events to rebuild state
- ✅ Easy to add new projections later

**Disadvantages**:
- ❌ Complex (steep learning curve)
- ❌ Event schema evolution is hard
- ❌ Performance (replaying many events)
- ❌ Overkill for most applications

**Verification**:
- [ ] All state changes captured as events
- [ ] Events are immutable
- [ ] Aggregates rebuilt from events
- [ ] Event store append-only

---

## Common Pitfalls

### Pitfall 1: Microservices Prematurely

**Why it happens**: "Netflix uses microservices, so should we!"

**Symptoms**:
- 3-person team managing 10 microservices
- More time deploying than coding
- Distributed monolith (all services tightly coupled)

**How to avoid**:
- Start with modular monolith
- Extract microservices only when:
  - Team >20 people
  - Clear service boundaries
  - Independent scaling needed

**Surgical Changes** (Karpathy Principle #3): Refactor monolith → microservices when pain is real, not anticipated.

---

### Pitfall 2: Leaky Abstractions

**Why it happens**: Layers/boundaries not properly enforced.

**Symptoms**:
- SQL queries in presentation layer
- Business logic in controllers
- Domain entities depend on database framework

**How to avoid**:
- Use interfaces/ports to define boundaries
- Code reviews to enforce architecture
- Automated tests to catch violations

---

### Pitfall 3: Over-Abstracting

**Why it happens**: Following patterns dogmatically.

**Symptoms**:
- Repository pattern for 5 database queries
- CQRS for simple CRUD
- Event sourcing for user preferences

**How to avoid**:
- **YAGNI** (You Aren't Gonna Need It)
- Patterns solve specific problems—no problem, no pattern
- Measure pain before adding complexity

---

## Common Patterns

**Decision Tree**:
```
Q: Is this a simple CRUD app?
└─ Yes → Layered Architecture
└─ No → Continue

Q: Do you need to swap implementations often?
└─ Yes → Hexagonal Architecture
└─ No → Continue

Q: Team >20 people? Need independent deployment?
└─ Yes → Microservices
└─ No → Continue

Q: Very different read/write workloads?
└─ Yes → CQRS
└─ No → Continue

Q: Need complete audit trail?
└─ Yes → Event Sourcing
└─ No → Layered or Hexagonal
```

**Goal-Driven Execution** (Karpathy Principle #4): Choose pattern based on concrete problems, not trends.

---

## Verification Checklist

Before committing to a pattern:

**Requirements Match**:
- [ ] Pattern solves actual problem (not hypothetical)
- [ ] Team understands the pattern
- [ ] Tradeoffs documented

**Implementation**:
- [ ] Boundaries clearly defined
- [ ] Dependencies flow correctly
- [ ] Tests verify architecture

**Maintenance**:
- [ ] Pattern enforced by code reviews
- [ ] New developers onboarded to pattern
- [ ] Documentation up to date

---

## Integration with Other Skills

**Combine with**:
- `architecture-designer` - Select pattern during design phase
- `prd-to-ddd-design` - Map domain to architectural pattern
- `task-development-workflow` - Implement pattern incrementally

**Example Workflow**:
```bash
# 1. Design system (architecture-designer)
# Identify NFRs, create C4 diagrams

# 2. Select pattern (architecture-patterns)
# Choose Hexagonal for testability

# 3. Map domain (prd-to-ddd-design)
# Identify aggregates, ports

# 4. Implement (task-development-workflow)
# Build core, add adapters, test
```

---

## References

**Pattern Catalogs**:
- Microsoft Azure Architecture Patterns: https://learn.microsoft.com/en-us/azure/architecture/patterns/
- Martin Fowler - Patterns of Enterprise Application Architecture: https://martinfowler.com/eaaCatalog/
- Sam Newman - Building Microservices: https://samnewman.io/books/building_microservices_2nd_edition/

**Related Skills**:
- `architecture-designer` - System design frameworks
- `prd-to-ddd-design` - Domain modeling
- `task-development-workflow` - Implementation workflow

---

## Meta: Skill Quality

**Incorporates Karpathy Principles**:
- ✅ Think Before Coding - Match pattern to problem
- ✅ Simplicity First - Start simple, add complexity when needed
- ✅ Surgical Changes - Refactor to patterns when pain emerges
- ✅ Goal-Driven - Pattern solves concrete problem

**Tested With**:
- Monoliths → microservices migrations
- CRUD → CQRS transitions
- Event sourcing in finance, healthcare

**Last Updated**: April 13, 2026  
**Maintainer**: Alteriom  
**License**: MIT

**Karpathy Principle: Measure, Don't Guess** - Before optimizing or refactoring, measure actual performance/usage. Profile before you fix. Data beats intuition.
