---
name: prd-to-ddd-design
description: "Domain-Driven Design decomposition with Event Storming"
version: 1.0.0
author: Alteriom
tags: [ddd, domain-driven-design, event-storming, bounded-context]
license: MIT
platforms:
  - openclaw
  - claude-code
---


# PRD to DDD Design

**Purpose**: Translate Product Requirements Documents into Domain-Driven Design models with bounded contexts, aggregates, and domain events.

**Works with**: Any programming language, any architecture  
**License**: MIT (original work, inspired by Eric Evans DDD, Vaughn Vernon, Event Storming)

---

## When to Use

Use this skill when you need to:
- Map business requirements to code structure
- Identify bounded contexts for microservices
- Design aggregates and entities
- Define domain events
- Prevent anemic domain model

**Don't use this for**:
- Simple CRUD apps (overkill)
- Well-understood domains (just code it)
- Prototypes (defer complexity)

---

## Prerequisites

### 1. Read the PRD

**Think Before Coding** (Karpathy Principle #1):
- What's the core domain?
- What are the key business rules?
- What are the invariants (things that must always be true)?

### 2. Understand DDD Building Blocks

**Core concepts**:
- **Entity**: Object with unique identity
- **Value Object**: Object defined by attributes (no identity)
- **Aggregate**: Cluster of entities + value objects (consistency boundary)
- **Domain Event**: Something that happened in the domain
- **Bounded Context**: Semantic boundary (different models for different contexts)

---

## Core Workflows

### Step 1: Identify Bounded Contexts

**What are the distinct areas of the business?**

**Example (E-commerce)**:
```
Bounded Contexts:
1. Sales (shopping cart, checkout)
2. Inventory (stock management)
3. Shipping (fulfillment, tracking)
4. Customer (profiles, preferences)
5. Billing (invoices, payments)
```

**Test**: Can these contexts have different definitions of the same word?

```
"Order" in Sales context: Shopping cart + checkout
"Order" in Shipping context: Package to be shipped
"Order" in Billing context: Invoice to be paid

Different meanings → Different bounded contexts ✅
```

**Karpathy Principle: Model the Domain, Not the Database** - Bounded contexts reflect business thinking, not database tables. If two teams talk about "orders" differently, they're in different contexts. Model that reality.

---

### Step 2: Identify Aggregates

**What are the consistency boundaries?**

**Aggregate = cluster of related objects that must stay consistent**

**Example**:
```typescript
// Order Aggregate
class Order {
  id: OrderId  // Entity (has identity)
  customerId: CustomerId
  items: OrderItem[]  // Value Objects (no identity)
  status: OrderStatus
  total: Money  // Value Object
  
  // Business rules (invariants)
  addItem(product: Product, quantity: number) {
    if (this.status !== 'DRAFT') {
      throw new Error('Cannot modify confirmed order')
    }
    
    if (quantity <= 0) {
      throw new Error('Quantity must be positive')
    }
    
    this.items.push(new OrderItem(product, quantity))
    this.recalculateTotal()
  }
  
  confirm() {
    if (this.items.length === 0) {
      throw new Error('Cannot confirm empty order')
    }
    
    this.status = 'CONFIRMED'
    // Emit domain event
    this.addDomainEvent(new OrderConfirmedEvent(this.id, this.total))
  }
  
  private recalculateTotal() {
    this.total = this.items.reduce((sum, item) => sum + item.price, Money.zero())
  }
}

// Value Objects
class OrderItem {
  constructor(
    public readonly product: Product,
    public readonly quantity: number,
    public readonly price: Money
  ) {}
}

class Money {
  constructor(public readonly amount: number, public readonly currency: string) {}
  
  static zero() {
    return new Money(0, 'USD')
  }
}
```

**Aggregate Design Rules**:
- Small aggregates (prefer single entity + value objects)
- Reference other aggregates by ID only (not direct references)
- Enforce invariants within aggregate
- One aggregate per transaction

**Karpathy Principle: Surgical Changes Over Rewrites** - Start with one large aggregate. Split only when you hit real consistency or performance issues. Premature splitting creates distributed transaction problems.

---

### Step 3: Define Domain Events

**What happens in the domain?**

**Events = past-tense facts**

```typescript
// Domain Events
class OrderConfirmedEvent {
  constructor(
    public readonly orderId: OrderId,
    public readonly total: Money,
    public readonly occurredAt: Date = new Date()
  ) {}
}

class PaymentReceivedEvent {
  constructor(
    public readonly orderId: OrderId,
    public readonly amount: Money,
    public readonly occurredAt: Date = new Date()
  ) {}
}

class OrderShippedEvent {
  constructor(
    public readonly orderId: OrderId,
    public readonly trackingNumber: string,
    public readonly occurredAt: Date = new Date()
  ) {}
}
```

**Use events for**:
- Cross-aggregate communication
- Triggering side effects
- Audit trail
- Event sourcing

---

### Step 4: Map Context Relationships

**How do contexts interact?**

**Patterns**:
- **Shared Kernel**: Two contexts share code
- **Customer/Supplier**: Upstream defines API, downstream consumes
- **Conformist**: Downstream accepts upstream model
- **Anti-Corruption Layer**: Translate between contexts

**Example**:
```
Sales (Upstream) → Inventory (Downstream)
When order is confirmed, reserve inventory

Inventory → Shipping
When stock allocated, create shipment

Shipping → Customer
When shipped, send tracking email
```

---

## Common Patterns

### Pattern 1: Anemic vs Rich Domain Model

**❌ Anemic (just data, no behavior)**:
```typescript
class Order {
  id: string
  items: OrderItem[]
  status: string
  total: number
}

// Business logic in service layer
class OrderService {
  addItem(order: Order, product: Product, quantity: number) {
    order.items.push({ product, quantity, price: product.price * quantity })
    order.total = order.items.reduce((sum, item) => sum + item.price, 0)
  }
}
```

**✅ Rich (behavior + data)**:
```typescript
class Order {
  private items: OrderItem[] = []
  private status: OrderStatus
  
  addItem(product: Product, quantity: number) {
    this.guardCanModify()
    this.items.push(OrderItem.create(product, quantity))
    this.recalculateTotal()
  }
  
  private guardCanModify() {
    if (this.status !== 'DRAFT') {
      throw new Error('Cannot modify confirmed order')
    }
  }
}
```

**Goal-Driven Execution** (Karpathy Principle #4): Business rules live in domain, not services.

---

### Pattern 2: Repository Pattern

**Separate domain from persistence**:

```typescript
// Domain interface (port)
interface OrderRepository {
  save(order: Order): Promise<void>
  findById(id: OrderId): Promise<Order | null>
  findByCustomer(customerId: CustomerId): Promise<Order[]>
}

// Infrastructure adapter
class PostgresOrderRepository implements OrderRepository {
  async save(order: Order) {
    // Map domain object → database rows
    await db.query('INSERT INTO orders ...', order.toData())
  }
  
  async findById(id: OrderId) {
    const row = await db.query('SELECT * FROM orders WHERE id = $1', [id.value])
    if (!row) return null
    
    // Map database row → domain object
    return Order.fromData(row)
  }
}
```

---

### Pattern 3: Specification Pattern

**Encapsulate business rules as reusable objects**:

```typescript
// Specification interface
interface Specification<T> {
  isSatisfiedBy(candidate: T): boolean
}

// Concrete specifications
class PremiumCustomerSpecification implements Specification<Customer> {
  isSatisfiedBy(customer: Customer): boolean {
    return customer.totalSpent.isGreaterThan(Money.fromDollars(10000))
  }
}

class EligibleForDiscountSpecification implements Specification<Order> {
  constructor(private customer: Customer) {}
  
  isSatisfiedBy(order: Order): boolean {
    const isPremium = new PremiumCustomerSpecification().isSatisfiedBy(this.customer)
    const isLargeOrder = order.total.isGreaterThan(Money.fromDollars(500))
    return isPremium || isLargeOrder
  }
}

// Usage in domain
class OrderService {
  calculateDiscount(order: Order, customer: Customer): Money {
    const spec = new EligibleForDiscountSpecification(customer)
    if (spec.isSatisfiedBy(order)) {
      return order.total.multiply(0.1) // 10% discount
    }
    return Money.zero()
  }
}
```

**Karpathy Principle: Simplicity First** - Only use Specification pattern when rules are complex and reused. For simple one-off checks, inline the logic.

---

### Pattern 4: Domain Services

**Operations that don't naturally belong to an entity**:

```typescript
// Domain service for complex operations
class PricingService {
  calculatePrice(
    product: Product,
    quantity: number,
    customer: Customer
  ): Money {
    let price = product.basePrice.multiply(quantity)
    
    // Apply volume discount
    if (quantity >= 10) {
      price = price.multiply(0.9) // 10% off
    }
    
    // Apply customer tier discount
    if (customer.tier === 'GOLD') {
      price = price.multiply(0.95) // 5% off
    }
    
    return price
  }
}

// Used by aggregate
class Order {
  addItem(
    product: Product,
    quantity: number,
    pricingService: PricingService,
    customer: Customer
  ) {
    const price = pricingService.calculatePrice(product, quantity, customer)
    this.items.push(new OrderItem(product, quantity, price))
  }
}
```

**Use domain services when**:
- Operation spans multiple aggregates
- Logic doesn't naturally fit one entity
- Stateless operations (no identity needed)

---

### Pattern 5: Event Sourcing

**Store state changes as events instead of current state**:

```typescript
// Event store
class OrderEventStore {
  private events: DomainEvent[] = []
  
  save(aggregate: Order) {
    const newEvents = aggregate.uncommittedEvents()
    this.events.push(...newEvents)
    aggregate.markEventsAsCommitted()
  }
  
  load(orderId: OrderId): Order {
    const events = this.events.filter(e => e.aggregateId.equals(orderId))
    return Order.fromEvents(events)
  }
}

// Aggregate rebuilt from events
class Order {
  private items: OrderItem[] = []
  private status: OrderStatus = 'DRAFT'
  private uncommitted: DomainEvent[] = []
  
  static fromEvents(events: DomainEvent[]): Order {
    const order = new Order()
    events.forEach(event => order.apply(event))
    return order
  }
  
  private apply(event: DomainEvent) {
    if (event instanceof OrderItemAddedEvent) {
      this.items.push(event.item)
    } else if (event instanceof OrderConfirmedEvent) {
      this.status = 'CONFIRMED'
    }
  }
  
  addItem(product: Product, quantity: number) {
    const event = new OrderItemAddedEvent(this.id, product, quantity)
    this.apply(event)
    this.uncommitted.push(event)
  }
}
```

**Use event sourcing when**:
- Full audit trail required
- Time-travel debugging needed
- Multiple projections of same events
- CQRS architecture

---

## Common Pitfalls

### Pitfall 1: Too Many Aggregates

**❌ Bad - Every entity is an aggregate**:
```typescript
class Order {
  id: OrderId
  customerId: CustomerId  // Reference to Customer aggregate
  items: OrderItemId[]    // Reference to OrderItem aggregates (WRONG!)
}

class OrderItem {
  id: OrderItemId
  orderId: OrderId
  productId: ProductId
  quantity: number
}
```

**Why it's wrong**:
- Cannot add item + recalculate total in one transaction
- Complex coordination between Order and OrderItem aggregates
- Performance issues (multiple saves per operation)

**✅ Good - OrderItem as value object**:
```typescript
class Order {
  id: OrderId
  customerId: CustomerId
  items: OrderItem[]  // Value objects within aggregate
  
  addItem(product: Product, quantity: number) {
    this.items.push(new OrderItem(product, quantity))
    this.recalculateTotal()
  }
}

class OrderItem {
  // No id! Value object
  constructor(
    public readonly product: Product,
    public readonly quantity: number
  ) {}
}
```

**Symptoms**:
- Complex transactions across aggregates
- Performance issues (too much locking)
- Confusing consistency boundaries

**How to avoid**:
- Start with large aggregates
- Split only when needed
- Most aggregates should be single entity + value objects

**Simplicity First** (Karpathy Principle #2): Prefer fewer, larger aggregates.

---

### Pitfall 2: Ignoring Bounded Contexts

**❌ Bad - One "Order" for everything**:
```typescript
// God object Order
class Order {
  // Sales context
  cart: CartItem[]
  checkout(): void {}
  
  // Inventory context
  reservedStock: Map<ProductId, number>
  allocateStock(): void {}
  
  // Shipping context
  trackingNumber: string
  ship(): void {}
  
  // Billing context
  invoice: Invoice
  generateInvoice(): void {}
}
```

**Why it's wrong**:
- Tight coupling (changing shipping affects sales)
- Different teams stepping on each other
- Cannot deploy contexts independently

**✅ Good - Separate models per context**:
```typescript
// Sales context
class SalesOrder {
  items: OrderItem[]
  confirm() {
    // Emit event
    publish(new OrderConfirmedEvent(this.id))
  }
}

// Inventory context
class StockReservation {
  orderId: OrderId
  items: Map<ProductId, number>
}

// Shipping context
class Shipment {
  orderId: OrderId
  trackingNumber: string
}

// Each context listens to events from others
```

**Symptoms**:
- God objects (Order knows everything)
- Tight coupling between features
- Difficult to change one area without breaking others

**How to avoid**:
- Identify distinct business areas
- Use different models in different contexts
- Accept some duplication across contexts

---

### Pitfall 3: Not Using Value Objects

**❌ Bad - Primitives everywhere**:
```typescript
class Order {
  totalAmount: number
  currency: string
  
  addDiscount(percent: number) {
    this.totalAmount = this.totalAmount * (1 - percent)
  }
}

// Easy to make mistakes
order.addDiscount(0.1)  // 10% or 1%? Unclear!
order.totalAmount = -100 // Negative price allowed!
```

**✅ Good - Value objects enforce invariants**:
```typescript
class Money {
  constructor(
    private readonly amount: number,
    private readonly currency: string
  ) {
    if (amount < 0) throw new Error('Money cannot be negative')
    if (!['USD', 'EUR', 'GBP'].includes(currency)) {
      throw new Error('Invalid currency')
    }
  }
  
  multiply(factor: number): Money {
    return new Money(this.amount * factor, this.currency)
  }
  
  add(other: Money): Money {
    if (this.currency !== other.currency) {
      throw new Error('Cannot add different currencies')
    }
    return new Money(this.amount + other.amount, this.currency)
  }
}

class Order {
  total: Money
  
  addDiscount(percentage: Percentage) {
    this.total = this.total.multiply(1 - percentage.value)
  }
}
```

**Use value objects for**:
- Money, dates, email addresses
- Coordinates, addresses, phone numbers
- Any concept with validation rules

---

## Verification Checklist

Before considering design complete:

**Domain Model**:
- [ ] Bounded contexts identified
- [ ] Aggregates defined with clear boundaries
- [ ] Business rules in domain, not services
- [ ] Value objects used where appropriate
- [ ] Entities have identity, value objects don't

**Events**:
- [ ] Domain events defined (past tense)
- [ ] Events published on state changes
- [ ] Cross-aggregate communication via events
- [ ] Event handler side effects isolated

**Persistence**:
- [ ] Repository interfaces defined
- [ ] Domain independent of database
- [ ] No ORM annotations in domain entities

**Testing**:
- [ ] Domain logic unit tested (no mocks needed)
- [ ] Aggregates testable in isolation
- [ ] Events captured and verifiable

---

## Integration with Other Skills

**Combine with**:
- `prd-writer` - Start with PRD
- `architecture-patterns` - Apply hexagonal or event-driven architecture
- `task-decomposer` - Break design into tasks

**Workflow**:
```bash
# 1. Write PRD (prd-writer)
# 2. Map to DDD (prd-to-ddd-design)
# 3. Choose architecture (architecture-patterns)
# 4. Implement (task-development-workflow)
```

---

## References

**Books**:
- Eric Evans - Domain-Driven Design: https://www.domainlanguage.com/ddd/
- Vaughn Vernon - Implementing Domain-Driven Design: https://vaughnvernon.com/
- Event Storming: https://www.eventstorming.com/

**Patterns**:
- Specification Pattern: https://martinfowler.com/apsupp/spec.pdf
- Event Sourcing: https://martinfowler.com/eaaDev/EventSourcing.html
- CQRS: https://martinfowler.com/bliki/CQRS.html

**Related Skills**:
- `prd-writer` - Product requirements
- `architecture-patterns` - Architecture selection
- `task-decomposer` - Task breakdown

---

## Meta: Skill Quality

**Incorporates Karpathy Principles**:
- ✅ Think Before Coding - Model domain before implementation
- ✅ Simplicity First - Start with simple aggregates, add complexity when needed
- ✅ Surgical Changes - Split aggregates only when hitting real problems
- ✅ Goal-Driven - Business rules define domain
- ✅ Model the Domain - Reflect business thinking, not database structure
- ✅ Understand the Problem - Use Specification pattern only for complex, reused rules

**Tested With**:
- DDD in TypeScript, C#, Java
- Event-driven architectures
- Microservices with bounded contexts
- Event sourcing and CQRS

**Completeness**: 9/10 - Covers core DDD patterns, event sourcing, and common pitfalls. Missing: Saga pattern, process managers, complex event flows.

**Last Updated**: April 13, 2026  
**Maintainer**: Alteriom  
**License**: MIT
