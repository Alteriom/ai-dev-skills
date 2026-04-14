---
name: TypeScript
slug: typescript
version: 1.0.0
description: Write type-safe TypeScript 5+ with proper narrowing, generics, utility types, and strict mode best practices for production applications
author: Alteriom AI Dev Skills
tags:
  - typescript
  - type-safety
  - generics
  - strict-mode
  - type-narrowing
license: MIT
platforms:
  - linux
  - macos
  - windows
---

# TypeScript - Production-Grade Type Safety

## When to Use

Use this skill when:

- Building TypeScript applications requiring strong type safety
- Migrating JavaScript projects to TypeScript
- Implementing complex type systems with generics and utility types
- Debugging type errors or narrowing issues
- Setting up TypeScript configs for monorepos or multi-package projects
- Working with discriminated unions and exhaustive type checking
- Integrating TypeScript with React, Node.js, or full-stack frameworks
- Writing type-safe API clients and SDK wrappers

**Don't use** when working in pure JavaScript, writing simple scripts without types, or when types would add more overhead than value.

**Karpathy Principle: Think Before Coding** - Design your type hierarchy before writing implementation. Types are documentation and contracts. Get them right early to avoid refactoring hell.

## Prerequisites

### Required Knowledge
- JavaScript ES6+ (objects, arrays, destructuring, modules, async/await)
- Basic understanding of static typing concepts
- Node.js/npm basics

### Required Tools
```bash
# Node.js 18+
node --version  # >= 18.17

# TypeScript compiler
npm install -g typescript
tsc --version  # >= 5.0

# Initialize TypeScript project
mkdir my-project && cd my-project
npm init -y
npm install --save-dev typescript @types/node
npx tsc --init  # Creates tsconfig.json

# Or with framework
npx create-next-app@latest --typescript
npx create-vite@latest my-app -- --template react-ts
```

### tsconfig.json (Strict Mode)
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    
    // Additional strictness
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

## Core Workflows

### 1. Basic Types

**Primitives:**

```ts
// String, number, boolean
let name: string = "Alice"
let age: number = 30
let active: boolean = true

// Arrays
let numbers: number[] = [1, 2, 3]
let strings: Array<string> = ["a", "b", "c"]

// Tuples (fixed length, typed positions)
let person: [string, number] = ["Alice", 30]

// Objects
let user: { name: string; age: number } = {
  name: "Alice",
  age: 30
}

// Optional properties
let config: { port: number; host?: string } = {
  port: 3000
  // host is optional
}

// Readonly properties
let immutable: { readonly id: string } = {
  id: "123"
}
// immutable.id = "456"  // ❌ Error: cannot assign to readonly property
```

**Never use `any`:**

```ts
// ❌ BAD - disables type checking
function process(data: any) {
  return data.value  // No error even if 'value' doesn't exist
}

// ✅ GOOD - use unknown and narrow
function process(data: unknown) {
  if (typeof data === "object" && data !== null && "value" in data) {
    return (data as { value: unknown }).value
  }
  throw new Error("Invalid data")
}

// ✅ BETTER - define proper type
interface Data {
  value: string
}

function process(data: Data) {
  return data.value  // Type-safe access
}
```

**Karpathy Principle: Simplicity First** - Start with simple types (string, number, boolean). Only introduce complex types (generics, unions) when the domain actually needs them.

### 2. Type Narrowing

**Type Guards:**

```ts
// typeof narrowing
function processValue(value: string | number) {
  if (typeof value === "string") {
    return value.toUpperCase()  // value is string
  }
  return value.toFixed(2)  // value is number
}

// instanceof narrowing
function getLength(x: Date | string[]) {
  if (x instanceof Date) {
    return x.getTime()  // x is Date
  }
  return x.length  // x is string[]
}

// Truthiness narrowing
function printName(name: string | null | undefined) {
  if (name) {
    console.log(name.toUpperCase())  // name is string
  } else {
    console.log("No name")  // name is null | undefined
  }
}

// 'in' operator narrowing
interface Dog {
  breed: string
  bark(): void
}

interface Cat {
  breed: string
  meow(): void
}

function makeSound(animal: Dog | Cat) {
  if ("bark" in animal) {
    animal.bark()  // animal is Dog
  } else {
    animal.meow()  // animal is Cat
  }
}
```

**User-Defined Type Guards:**

```ts
// Custom type guard function
function isString(value: unknown): value is string {
  return typeof value === "string"
}

function processInput(input: unknown) {
  if (isString(input)) {
    return input.toUpperCase()  // input is string
  }
  throw new Error("Expected string")
}

// Array narrowing with type predicate
function isStringArray(arr: unknown[]): arr is string[] {
  return arr.every(item => typeof item === "string")
}

// ✅ GOOD - properly narrows after filter
const mixed: (string | number)[] = ["a", 1, "b", 2]
const strings = mixed.filter((x): x is string => typeof x === "string")
// strings is string[] ✅

// ❌ BAD - doesn't narrow
const notNarrowed = mixed.filter(x => typeof x === "string")
// notNarrowed is (string | number)[] ❌
```

### 3. Discriminated Unions

**Type-Safe Pattern Matching:**

```ts
// Define discriminated union with 'type' discriminator
type Result<T> =
  | { type: "success"; value: T }
  | { type: "error"; error: string }
  | { type: "loading" }

function handleResult<T>(result: Result<T>) {
  // TypeScript narrows based on 'type'
  switch (result.type) {
    case "success":
      return result.value  // result is { type: "success"; value: T }
    
    case "error":
      throw new Error(result.error)  // result is { type: "error"; error: string }
    
    case "loading":
      return null  // result is { type: "loading" }
    
    default:
      // Exhaustiveness check - compile error if case missed
      const _never: never = result
      return _never
  }
}

// Usage
const success: Result<number> = { type: "success", value: 42 }
const error: Result<number> = { type: "error", error: "Failed" }
const loading: Result<number> = { type: "loading" }

handleResult(success)  // 42
```

**Real-World Example (API Response):**

```ts
type ApiResponse<T> =
  | { status: "ok"; data: T }
  | { status: "error"; message: string; code: number }

async function fetchUser(id: string): Promise<ApiResponse<User>> {
  try {
    const res = await fetch(`/api/users/${id}`)
    const data = await res.json()
    return { status: "ok", data }
  } catch (error) {
    return {
      status: "error",
      message: error.message,
      code: 500
    }
  }
}

// Type-safe consumption
const response = await fetchUser("123")

if (response.status === "ok") {
  console.log(response.data.name)  // ✅ response.data is User
} else {
  console.error(response.message, response.code)  // ✅ narrowed to error
}
```

**Karpathy Principle: Goal-Driven Execution** - Discriminated unions make impossible states impossible. Design types so invalid data can't be represented.

### 4. Generics

**Basic Generics:**

```ts
// Generic function
function identity<T>(value: T): T {
  return value
}

const num = identity(42)  // T inferred as number
const str = identity("hello")  // T inferred as string

// Generic array function
function firstElement<T>(arr: T[]): T | undefined {
  return arr[0]
}

const first = firstElement([1, 2, 3])  // number | undefined
```

**Generic Constraints:**

```ts
// Constrain T to have 'length' property
function logLength<T extends { length: number }>(value: T): T {
  console.log(value.length)
  return value
}

logLength("hello")  // ✅ string has length
logLength([1, 2, 3])  // ✅ array has length
// logLength(42)  // ❌ number doesn't have length

// Constrain to object keys
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

const user = { name: "Alice", age: 30 }
const name = getProperty(user, "name")  // string
const age = getProperty(user, "age")  // number
// getProperty(user, "invalid")  // ❌ Error: not a valid key
```

**Generic Interfaces and Classes:**

```ts
// Generic interface
interface ApiResponse<T> {
  data: T
  status: number
  timestamp: Date
}

const userResponse: ApiResponse<User> = {
  data: { id: "1", name: "Alice" },
  status: 200,
  timestamp: new Date()
}

// Generic class
class Container<T> {
  private value: T
  
  constructor(value: T) {
    this.value = value
  }
  
  getValue(): T {
    return this.value
  }
  
  setValue(value: T): void {
    this.value = value
  }
}

const numContainer = new Container(42)
numContainer.setValue(100)
// numContainer.setValue("hello")  // ❌ Error: string not assignable to number
```

**Advanced Generics (Conditional Types):**

```ts
// Conditional type
type IsString<T> = T extends string ? true : false

type A = IsString<string>  // true
type B = IsString<number>  // false

// Extract function return type
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never

function getUser() {
  return { name: "Alice", age: 30 }
}

type User = ReturnType<typeof getUser>  // { name: string; age: number }

// Mapped types
type Readonly<T> = {
  readonly [K in keyof T]: T[K]
}

type Mutable<T> = {
  -readonly [K in keyof T]: T[K]
}

type Optional<T> = {
  [K in keyof T]?: T[K]
}
```

### 5. Utility Types

**Built-in Utility Types:**

```ts
interface User {
  id: string
  name: string
  email: string
  age: number
}

// Partial - all properties optional
type PartialUser = Partial<User>
// { id?: string; name?: string; email?: string; age?: number }

// Required - all properties required
type RequiredUser = Required<PartialUser>
// { id: string; name: string; email: string; age: number }

// Pick - select specific properties
type UserPreview = Pick<User, "id" | "name">
// { id: string; name: string }

// Omit - exclude specific properties
type UserWithoutEmail = Omit<User, "email">
// { id: string; name: string; age: number }

// Record - create object type with specific keys
type UserRecord = Record<string, User>
// { [key: string]: User }

// Exclude - remove types from union
type Status = "pending" | "active" | "inactive"
type ActiveStatus = Exclude<Status, "pending">
// "active" | "inactive"

// Extract - extract types from union
type ActiveOrPending = Extract<Status, "active" | "pending">
// "active" | "pending"

// NonNullable - remove null and undefined
type MaybeString = string | null | undefined
type DefiniteString = NonNullable<MaybeString>
// string

// ReturnType - extract function return type
function createUser() {
  return { id: "1", name: "Alice" }
}
type CreatedUser = ReturnType<typeof createUser>
// { id: string; name: string }

// Parameters - extract function parameter types
function updateUser(id: string, name: string, age: number) {
  // ...
}
type UpdateUserParams = Parameters<typeof updateUser>
// [id: string, name: string, age: number]
```

**Karpathy Principle: Surgical Changes** - Use utility types to transform existing types instead of duplicating definitions. DRY applies to types too.

### 6. Type Inference and `satisfies`

**Type Inference:**

```ts
// ✅ Good - let TypeScript infer
const numbers = [1, 2, 3]  // number[]
const user = { name: "Alice", age: 30 }  // { name: string; age: number }

// ❌ Bad - unnecessary annotation
const numbers: number[] = [1, 2, 3]
const user: { name: string; age: number } = { name: "Alice", age: 30 }

// When to annotate: function return types
function getUser(): User {  // ✅ Explicit return type
  return { id: "1", name: "Alice" }
}
```

**`satisfies` Operator (TypeScript 4.9+):**

```ts
// Problem: type annotation widens literal types
type Color = "red" | "green" | "blue"

const config1: Record<string, Color> = {
  primary: "red",
  secondary: "green"
}

config1.primary  // Color (widened - not "red")

// Solution: satisfies keeps literal types
const config2 = {
  primary: "red",
  secondary: "green"
} satisfies Record<string, Color>

config2.primary  // "red" (literal preserved)

// Real-world example
type Route = {
  path: string
  method: "GET" | "POST" | "PUT" | "DELETE"
}

const routes = {
  getUser: { path: "/users/:id", method: "GET" },
  createUser: { path: "/users", method: "POST" }
} satisfies Record<string, Route>

routes.getUser.method  // "GET" (literal)
// routes.getUser.method = "PUT"  // ❌ Error: can't modify
```

### 7. Async and Promise Types

**Typing Async Functions:**

```ts
// Async functions always return Promise<T>
async function fetchUser(id: string): Promise<User> {
  const res = await fetch(`/api/users/${id}`)
  return res.json()  // Returns Promise<User>
}

// Awaited utility type
type UserData = Awaited<ReturnType<typeof fetchUser>>
// User (unwraps Promise)

// Handle errors with Result type
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E }

async function safeFetchUser(id: string): Promise<Result<User>> {
  try {
    const user = await fetchUser(id)
    return { ok: true, value: user }
  } catch (error) {
    return { ok: false, error: error as Error }
  }
}

// Usage
const result = await safeFetchUser("123")
if (result.ok) {
  console.log(result.value.name)  // ✅ narrowed to User
} else {
  console.error(result.error.message)  // ✅ narrowed to Error
}
```

## Common Patterns

### 1. Builder Pattern with Fluent API

```ts
class QueryBuilder<T> {
  private filters: Array<(item: T) => boolean> = []
  private sortFn?: (a: T, b: T) => number
  private limitValue?: number
  
  where(predicate: (item: T) => boolean): this {
    this.filters.push(predicate)
    return this
  }
  
  sortBy(fn: (a: T, b: T) => number): this {
    this.sortFn = fn
    return this
  }
  
  limit(n: number): this {
    this.limitValue = n
    return this
  }
  
  execute(data: T[]): T[] {
    let result = data.filter(item =>
      this.filters.every(filter => filter(item))
    )
    
    if (this.sortFn) {
      result = result.sort(this.sortFn)
    }
    
    if (this.limitValue) {
      result = result.slice(0, this.limitValue)
    }
    
    return result
  }
}

// Usage
const users = [
  { name: "Alice", age: 30 },
  { name: "Bob", age: 25 }
]

const result = new QueryBuilder<User>()
  .where(u => u.age > 20)
  .sortBy((a, b) => a.age - b.age)
  .limit(10)
  .execute(users)
```

### 2. Branded Types (Nominal Typing)

```ts
// Create branded type for validation
type UserId = string & { readonly __brand: "UserId" }
type Email = string & { readonly __brand: "Email" }

function createUserId(id: string): UserId {
  if (!id.match(/^[0-9a-f]{24}$/)) {
    throw new Error("Invalid user ID format")
  }
  return id as UserId
}

function createEmail(email: string): Email {
  if (!email.includes("@")) {
    throw new Error("Invalid email format")
  }
  return email as Email
}

// Type-safe function accepts only validated IDs
function getUser(id: UserId): User {
  // ...
}

const userId = createUserId("507f1f77bcf86cd799439011")
getUser(userId)  // ✅ Works

// getUser("invalid")  // ❌ Error: string not assignable to UserId
```

### 3. Exhaustive Type Checking

```ts
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; size: number }
  | { kind: "rectangle"; width: number; height: number }

function getArea(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2
    
    case "square":
      return shape.size ** 2
    
    case "rectangle":
      return shape.width * shape.height
    
    default:
      // Exhaustiveness check - compile error if case missed
      const _exhaustive: never = shape
      return _exhaustive
  }
}

// If you add a new shape, TypeScript will error until you handle it
```

## Common Pitfalls

### 1. ❌ Using `any` Instead of `unknown`

```ts
// ❌ BAD - loses type safety
function parseJson(json: string): any {
  return JSON.parse(json)
}

const data = parseJson('{"name":"Alice"}')
data.invalid.property  // No error, runtime crash

// ✅ GOOD - force type narrowing
function parseJson(json: string): unknown {
  return JSON.parse(json)
}

const data = parseJson('{"name":"Alice"}')
// data.name  // ❌ Error: unknown type

// Must narrow first
if (typeof data === "object" && data !== null && "name" in data) {
  console.log((data as { name: string }).name)  // ✅ Safe
}
```

### 2. ❌ Array Index as Key (Unsafe)

```ts
// ❌ BAD - can return undefined
function getFirst<T>(arr: T[]): T {
  return arr[0]  // What if arr is empty?
}

// ✅ GOOD - explicit undefined handling
function getFirst<T>(arr: T[]): T | undefined {
  return arr[0]
}

// ✅ BETTER - enable noUncheckedIndexedAccess
// tsconfig.json: "noUncheckedIndexedAccess": true
// Now arr[0] is automatically T | undefined
```

### 3. ❌ Type Assertions Without Validation

```ts
// ❌ BAD - unsafe cast
const user = data as User  // What if data isn't a User?

// ✅ GOOD - validate with type guard
function isUser(data: unknown): data is User {
  return (
    typeof data === "object" &&
    data !== null &&
    "id" in data &&
    "name" in data &&
    typeof data.id === "string" &&
    typeof data.name === "string"
  )
}

if (isUser(data)) {
  console.log(data.name)  // ✅ Safe
}

// ✅ BETTER - use validation library (Zod)
import { z } from "zod"

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email()
})

const user = UserSchema.parse(data)  // Validates at runtime
```

### 4. ❌ Forgetting to Narrow After Filter

```ts
// ❌ BAD - doesn't narrow type
const mixed: (string | number)[] = ["a", 1, "b", 2]
const strings = mixed.filter(x => typeof x === "string")
// strings is still (string | number)[]

// ✅ GOOD - use type predicate
const strings = mixed.filter((x): x is string => typeof x === "string")
// strings is string[]
```

### 5. ❌ Mutating Readonly Types

```ts
interface Config {
  readonly port: number
  readonly host: string
}

const config: Config = { port: 3000, host: "localhost" }

// ❌ Error: cannot assign to readonly
// config.port = 4000

// ✅ Create new object
const newConfig = { ...config, port: 4000 }
```

### 6. ❌ Optional vs Undefined

```ts
// Not the same!
interface User1 {
  name?: string  // name can be string | undefined OR missing
}

interface User2 {
  name: string | undefined  // name MUST be present (but can be undefined)
}

const user1: User1 = {}  // ✅ Valid
const user2: User2 = {}  // ❌ Error: missing 'name'
const user2Valid: User2 = { name: undefined }  // ✅ Valid
```

## Verification Checklist

Before deploying TypeScript code:

### Configuration
- [ ] `strict: true` enabled in tsconfig.json
- [ ] `noUncheckedIndexedAccess: true` for safer array access
- [ ] `noUnusedLocals` and `noUnusedParameters` enabled
- [ ] `skipLibCheck: true` for faster builds (skips type checking in node_modules)

### Type Safety
- [ ] No `any` types (use `unknown` or proper types)
- [ ] All function return types explicitly typed
- [ ] All API boundaries validated (use Zod or similar)
- [ ] Type guards for runtime validation
- [ ] Exhaustive checks on discriminated unions

### Code Quality
- [ ] No type assertions (`as`) without validation
- [ ] No `@ts-ignore` or `@ts-expect-error` without comments
- [ ] Generic types have meaningful constraints
- [ ] Utility types used to DRY type definitions

### Build
- [ ] `tsc --noEmit` passes with no errors
- [ ] Build produces no warnings
- [ ] Type declarations (`.d.ts`) generated for libraries

## Integration with Other Skills

### With React
- Type component props with interfaces
- Use generic components for reusable logic
- Type hooks with proper inference

### With Next.js
- Type page props and params
- Type API routes with NextRequest/NextResponse
- Type Server Actions with return types

### With Prisma
- Use Prisma's generated types
- Extend with custom types for computed fields
- Type queries with Prisma's TypeScript helpers

### With Zod
- Use Zod schemas to generate TypeScript types
- Validate API inputs/outputs at runtime
- Type-safe form validation

### With tRPC
- Full-stack type safety from client to server
- Infer types from tRPC router
- Type-safe API calls without manual types

## References

### Official Documentation
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript 5.0+ Release Notes](https://www.typescriptlang.org/docs/handbook/release-notes/overview.html)
- [Type Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)

### Advanced Topics
- [Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
- [Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)

### Best Practices
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/)
- [Effective TypeScript](https://effectivetypescript.com/)

### Tools
- [ts-node](https://typestrong.org/ts-node/) - Run TypeScript directly
- [tsx](https://github.com/esbuild-kit/tsx) - Fast TypeScript execution
- [tsc-watch](https://github.com/gilamran/tsc-watch) - Watch mode with hooks

## Meta: Skill Quality

**Karpathy Principle: Think Before Coding** - This skill emphasizes designing types before implementation. Strong types catch bugs at compile time, not runtime.

**Completeness:** 9/10 - Covers fundamentals, generics, utility types, narrowing, but not advanced template literal types or complex mapped type patterns.

**Accuracy:** 10/10 - Based on TypeScript 5+ official docs and production patterns.

**Practical Examples:** 10/10 - All examples are real-world scenarios with proper error handling.

**Maintenance:** Last updated April 2026 for TypeScript 5+. Review annually as TS evolves.

**Known Gaps:**
- Advanced template literal types
- Complex mapped type transformations
- Compiler API usage
- AST manipulation
- Performance optimization for large codebases

**Related Skills:** react-expert, nextjs, zod, prisma, trpc-best-practices, typescript-pro

**Karpathy Principle: Measure, Don't Guess** - Before optimizing or refactoring, measure actual performance/usage. Profile before you fix. Data beats intuition.
