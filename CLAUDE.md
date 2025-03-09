# CLAUDE.md - Unprompter Codebase Guidelines

## Commands
- **Frontend (Next.js)**: 
  - `cd frontend && npm run dev`: Start development server with Turbopack
  - `cd frontend && npm run build`: Build production version
  - `cd frontend && npm run lint`: Run ESLint checks
  - `cd frontend && npx tsc --noEmit`: Run TypeScript type checking
  - `cd frontend && next dev --turbopack`: Run dev with Turbopack
- **Backend (Python)**:
  - `cd backend && python -m generate_embeddings`: Generate embeddings
  - `cd backend && python -m load_image`: Load images

## Code Style Guidelines
- **TypeScript**: Strict typing with explicit interfaces for props and state
- **React Components**: Functional components with hooks, explicit typing with React.FC
- **Imports**: Group by external/internal, order alphabetically
- **Naming**: camelCase for variables/functions, PascalCase for components/interfaces
- **Error Handling**: Use try/catch blocks with specific error messages
- **CSS**: Use Tailwind classes with consistent spacing
- **File Structure**: Components in `/components`, hooks in `/hooks`, services in `/services`
- **Component Props**: Pass as explicit objects with TypeScript interfaces