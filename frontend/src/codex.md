# Frontend Source

The core source code for the React application.

## Directory Structure (`frontend/src/`)

```
frontend/src/
├── App.css
├── App.test.tsx
├── App.tsx
├── index.css
├── index.tsx
├── react-app-env.d.ts
├── reportWebVitals.ts
├── setupTests.ts
├── components/
├── contexts/
├── hooks/
├── pages/
└── services/
```

*   `App.css`: Global CSS styles specifically for the `App` component.
*   `App.test.tsx`: Basic unit test for the main `App` component.
*   `App.tsx`: The root component of the React application, sets up the main router (`BrowserRouter`) and defines routes.
*   `index.css`: Base CSS styles applied globally.
*   `index.tsx`: The entry point for the React application; renders the `App` component into the DOM.
*   `react-app-env.d.ts`: TypeScript declaration file for Create React App environment variables.
*   `reportWebVitals.ts`: Utility function for measuring and reporting web performance metrics.
*   `setupTests.ts`: Configuration file for Jest tests, typically used to import setup helpers like `@testing-library/jest-dom`.

See subdirectory `codex.md` files for more detailed information about specific components.