# JavaScript Tests

This directory contains Jest-based unit tests for the ttmp32gme web frontend JavaScript code.

## Running Tests

```bash
# Install dependencies (from project root)
npm install

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Test Files

- `print.test.js` - Tests for utility functions in `src/assets/js/print.js`
  - testCheckBox() - Checkbox state handling
  - notify() - Popover notification system
  - getElementValues() - Form data extraction
  - cssPagedMedia() - CSS page layout manipulation

## Test Framework

- **Jest** - JavaScript testing framework
- **jsdom** - DOM implementation for testing browser code in Node.js

## Coverage

Coverage reports are generated in the `coverage/` directory when running `npm run test:coverage`.
