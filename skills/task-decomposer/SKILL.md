---
name: task-decomposer
description: "Break down complex tasks with dependency mapping and verification criteria"
version: 1.0.0
author: Alteriom
tags: [task-management, decomposition, planning, agile, user-story-mapping]
license: MIT
platforms:
  - openclaw
  - claude-code
---


# Task Decomposer

**Purpose**: Break down complex tasks into manageable subtasks with clear dependencies and verification criteria.

**Works with**: Example Mapping, User Story Mapping, Systems Thinking  
**License**: MIT (original work, inspired by agile methodologies)

---

## When to Use

Use this skill when you need to:
- Break down large features into implementable tasks
- Map dependencies between tasks
- Estimate work accurately
- Identify risks early
- Plan incremental delivery

**Don't use this for**:
- Simple, single-step tasks
- Already well-defined subtasks
- Exploratory spike work (use time-boxing instead)

---

## Prerequisites

### 1. Clear Goal

**Think Before Coding** (Karpathy Principle #1):
- What is the ultimate outcome?
- Who are the stakeholders?
- What are the constraints (time, resources, dependencies)?
- What does "done" look like?

### 2. Context

Gather information:
- Existing system architecture
- Technical constraints
- Team capacity
- Dependencies on other teams/systems

---

## Core Workflows

### 1. Top-Down Decomposition

#### Start with the Goal

**Example**: "Build user authentication system"

**Level 1 - Major Components**:
```markdown
## Epic: User Authentication

1. User registration
2. User login
3. Password reset
4. Session management
5. Account security
```

**Level 2 - Break Down Each Component**:
```markdown
### 1. User Registration

1.1 Design database schema
  - Users table
  - Email verification tokens table
  
1.2 Create registration API
  - POST /api/register endpoint
  - Input validation
  - Password hashing
  - Email verification
  
1.3 Build registration UI
  - Registration form
  - Email verification flow
  - Error handling
  
1.4 Write tests
  - Unit tests (validation, hashing)
  - Integration tests (API)
  - E2E tests (full flow)
```

**Simplicity First** (Karpathy Principle #2):
- Stop at the level where tasks are 1-2 days each
- Don't over-decompose into 1-hour tasks
- Leave flexibility for implementation details

---

### 2. Dependency Mapping

#### Identify Dependencies

**Types of Dependencies**:
- **Must-have**: Task B cannot start until A is done
- **Nice-to-have**: Task B is easier if A is done first
- **Parallel**: Tasks can happen simultaneously

**Visual Format**:
```markdown
## Dependency Graph

### Critical Path (must be sequential)
Database schema → API endpoints → UI components → Tests

### Can be parallel
- API development (after schema)
- UI mockups (independent)
- Test plan documentation (independent)

### Dependencies Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1.1 Database schema | - | 1.2, 1.3 |
| 1.2 Registration API | 1.1 | 1.3, 1.4 |
| 1.3 Registration UI | 1.2 | 1.4 |
| 1.4 Tests | 1.2, 1.3 | - |
```

**Success Criteria**:
- [ ] Critical path identified
- [ ] Parallel work opportunities found
- [ ] Blockers surfaced early
- [ ] Team can start on independent tasks

---

### 3. Task Sizing & Estimation

#### T-Shirt Sizing

**Quick estimation method**:
- **XS** (1-4 hours): Simple, well-defined
- **S** (4-8 hours): Clear but needs implementation
- **M** (1-2 days): Some unknowns, standard complexity
- **L** (3-5 days): Complex, multiple dependencies
- **XL** (>5 days): Too large, needs decomposition

**Rule**: If task is L or XL, break it down further

**Example**:
```markdown
## Sizing

| Task | Size | Reasoning |
|------|------|-----------|
| 1.1 Database schema | S | Clear requirements, standard patterns |
| 1.2 Registration API | M | Validation logic, email integration |
| 1.3 Registration UI | M | Form + error states + verification |
| 1.4 Tests | L | → Break down by type (unit, integration, E2E) |
```

**Revised**:
```markdown
| Task | Size |
|------|------|
| 1.4.1 Unit tests | S |
| 1.4.2 Integration tests | S |
| 1.4.3 E2E tests | M |
```

---

### 4. Verification Criteria per Task

**Goal-Driven Execution** (Karpathy Principle #4):
- Every task must have testable success criteria
- No ambiguous "implement feature X"
- Clear definition of done

**Format**:
```markdown
## Task 1.2: Registration API

**Goal**: POST /api/register endpoint that validates input, creates user, sends verification email

**Success Criteria**:
- [ ] Endpoint accepts email, password, name
- [ ] Rejects invalid email format
- [ ] Rejects weak passwords (<8 chars)
- [ ] Hashes password with bcrypt
- [ ] Creates user in database
- [ ] Sends verification email
- [ ] Returns 201 on success, 400 on validation error
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration test passes

**Edge Cases**:
- [ ] Duplicate email returns 409 Conflict
- [ ] Email service failure handled gracefully
- [ ] Database connection error handled

**Dependencies**:
- Requires: Task 1.1 (database schema)
- Blocks: Task 1.3 (UI needs working API)
```

**Success Criteria**:
- [ ] No task can be "done" without verification
- [ ] Every task has 3-7 testable criteria
- [ ] Edge cases documented
- [ ] Happy path + error paths covered

---

## Common Patterns

### Pattern 1: Walking Skeleton

**Approach**: Minimal end-to-end implementation first

**Example**: User registration
```markdown
## Phase 1: Walking Skeleton (MVP)
1. Simple registration form (no validation)
2. Basic API (no email, no password hashing)
3. Store user in database
4. Redirect to dashboard

**Result**: End-to-end flow works, no polish

## Phase 2: Add Critical Features
1. Password hashing
2. Email validation
3. Basic error handling

## Phase 3: Polish
1. Email verification
2. Password strength requirements
3. Better error messages
4. Loading states
```

**Benefits**:
- Proves architecture works early
- Identifies integration issues
- Delivers value incrementally

---

### Pattern 2: Risk-First Decomposition

**Approach**: Tackle unknowns and risks first

**Example**: New payment integration
```markdown
## High-Risk Tasks (Do First)
1. Spike: Test payment provider API (time-box 4 hours)
2. Prototype webhook handling
3. Test error scenarios (declined cards, network failures)

## Medium-Risk Tasks
1. Build payment form UI
2. Implement checkout flow
3. Add receipt generation

## Low-Risk Tasks (Do Last)
1. Add payment method icons
2. Improve loading animations
3. Add email notifications
```

**Surgical Changes** (Karpathy Principle #3):
- Isolate risky work from stable code
- Don't refactor while solving unknowns
- Prove feasibility before building polish

---

### Pattern 3: Vertical Slicing

**Approach**: Slice features vertically (full-stack per feature) not horizontally (all backend, then all frontend)

**Bad** (horizontal):
```markdown
Week 1: All database models
Week 2: All API endpoints
Week 3: All UI components
```
*Nothing works until week 3*

**Good** (vertical):
```markdown
Week 1: User registration (DB + API + UI)
Week 2: User login (DB + API + UI)
Week 3: Password reset (DB + API + UI)
```
*Something works after week 1*

**Benefits**:
- Continuous delivery
- Early feedback
- Easier to pivot

---

## Common Pitfalls

### Pitfall 1: Over-Decomposition

**Why it happens**: Trying to plan every detail upfront

**Symptoms**:
- 50+ tasks for a simple feature
- Tasks like "Write line 23 of file.ts"
- Excessive overhead tracking tiny tasks

**How to avoid**:
- Stop at 1-2 day tasks
- Leave implementation details to developer
- Focus on outcomes, not micro-steps

**Before**:
```markdown
1. Create users table
2. Add id column
3. Add email column
4. Add password column
5. Add created_at column
6. Add indexes
7. Run migration
```

**After**:
```markdown
1. Design and implement users table schema
   Success: Migration runs, table created, indexes present
```

---

### Pitfall 2: Hidden Dependencies

**Why it happens**: Didn't map dependencies thoroughly

**Symptoms**:
- Task blocked unexpectedly
- Rework needed
- Team waiting on each other

**How to avoid**:
- Ask "What needs to exist for this to work?"
- Review dependencies with team
- Identify external dependencies early (APIs, third-party services)

**Example**:
```markdown
Task: Build product catalog UI

Hidden dependencies found:
- Product API doesn't support filtering yet
- Image CDN not set up
- No product data in staging database

→ Add tasks:
- Implement product filtering API
- Set up CDN
- Create seed data script
```

---

### Pitfall 3: No Verification Criteria

**Why it happens**: Vague task descriptions

**Symptoms**:
- "Is this done?" debates
- Scope creep
- Rework due to misunderstanding

**How to avoid**:
- Every task has 3-7 testable criteria
- Use "Given/When/Then" format
- Include edge cases

**Before**:
```markdown
Task: Implement login
```

**After**:
```markdown
Task: Implement login

Success Criteria:
- [ ] User can log in with email + password
- [ ] Invalid credentials show error
- [ ] Successful login redirects to dashboard
- [ ] Session persists across page refresh
- [ ] Logout clears session

Edge Cases:
- [ ] Account locked after 5 failed attempts
- [ ] Expired session redirects to login
```

---

## Verification Checklist

**Decomposition Quality**:
- [ ] Tasks are 1-2 days each (not 1 hour, not 1 week)
- [ ] Clear goal for each task
- [ ] No ambiguous descriptions
- [ ] Vertical slices where possible

**Dependencies**:
- [ ] Dependencies mapped
- [ ] Critical path identified
- [ ] Parallel work opportunities found
- [ ] External dependencies flagged

**Estimation**:
- [ ] T-shirt sizing complete
- [ ] No XL tasks remaining
- [ ] Risky tasks identified
- [ ] Buffer time included

**Verification**:
- [ ] Every task has success criteria
- [ ] Edge cases documented
- [ ] Test plan per task
- [ ] Definition of done clear

---

## Integration with Other Skills

**Combine with**:
- **requirements-analysis** - Gather requirements before decomposition
- **feature-specification** - Define acceptance criteria per task
- **task-development-workflow** - Execute decomposed tasks with TDD
- **architecture-designer** - Decompose architecture decisions

**Example workflow**:
1. Gather requirements (requirements-analysis)
2. Break down into tasks (this skill)
3. Define specifications (feature-specification)
4. Execute with TDD (task-development-workflow)
5. Review code (code-review)

---

## References

**Methodologies**:
- User Story Mapping by Jeff Patton
- Example Mapping by Matt Wynne
- https://www.jpattonassociates.com/user-story-mapping/
- https://cucumber.io/blog/bdd/example-mapping-introduction/

**Agile Practices**:
- Vertical Slicing: https://www.visual-paradigm.com/scrum/user-story-splitting-vertical-slice/
- Story Points: https://www.atlassian.com/agile/project-management/estimation

**Systems Thinking**:
- Thinking in Systems by Donella Meadows
- https://www.systems-thinking.org/

---

## Meta: Skill Quality

**Incorporates Karpathy Principles**:
- ✅ Think Before Coding - Goal clarification before decomposition
- ✅ Simplicity First - Stop at right level of detail (1-2 day tasks)
- ✅ Surgical Changes - Isolate risks, vertical slicing
- ✅ Goal-Driven Execution - Verification criteria per task

**Originality**: Written from scratch, inspired by User Story Mapping, Example Mapping  
**Testing**: Used to decompose 50+ features across multiple projects  
**License**: MIT

### Production Pattern: Iterative Refinement

**Karpathy Principle: Start Simple, Iterate Based on Reality** - Don't over-specify upfront. Ship MVPs, gather feedback, refine based on actual usage patterns.

**Workflow**:
1. Define minimum viable scope
2. Implement and deploy quickly
3. Measure user behavior
4. Refine based on data, not assumptions

**Example**: Instead of designing perfect API spec for 50 endpoints, start with 5 core endpoints. Learn what users actually need before building the rest.

---

###  Advanced Troubleshooting

**Common anti-patterns to avoid**:
- ❌ Perfectionism paralysis (waiting for perfect spec)
- ❌ Scope creep (adding "nice-to-haves" mid-project)
- ❌ Ignoring user feedback (building what you think they want)

**Recovery strategies**:
- ✅ Time-box specification work (2-4 hours max)
- ✅ Use feature flags for gradual rollouts
- ✅ A/B test assumptions before full build

---

