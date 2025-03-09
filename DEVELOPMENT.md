# Development Guide for Unprompted

This document provides guidance for developers contributing to the Unprompted project.

## Development Environment Setup

### Prerequisites

- Node.js 18+ for frontend development
- Python 3.9+ for backend development
- PostgreSQL database
- Redis instance
- Vercel account (for Blob Storage)

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
pnpm install
```

2. Run the development server:
```bash
pnpm dev
```

3. Run tests:
```bash
pnpm test
```

### Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Download spaCy model:
```bash
python -m spacy download en_core_web_lg
```

3. Set up environment variables in a `.env` file:
```
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://username:password@host:port
BLOB_READ_WRITE_TOKEN=your-vercel-blob-token
```

## Current Development Priorities

### Frontend

1. **Performance Optimization**
   - Improve image loading times
   - Optimize React rendering for smoother gameplay

2. **User Experience**
   - Enhance mobile responsiveness
   - Add animations for correct/incorrect guesses
   - Implement dark mode support

3. **Game Features**
   - Add difficulty levels
   - Implement daily challenges
   - Create user accounts and persisted game history

### Backend

1. **API Enhancements**
   - Create RESTful API endpoints for frontend integration
   - Implement proper error handling and validation
   - Add authentication for admin operations

2. **Database Optimization**
   - Optimize PostgreSQL queries
   - Implement Redis caching for frequently accessed data
   - Create database migration system

3. **Game Management**
   - Develop an admin interface for managing games
   - Implement automated game rotation system
   - Add analytics dashboard for game performance

## Development Workflow

1. **Branching Strategy**
   - `main`: Production-ready code
   - `develop`: Integration branch for features
   - `feature/feature-name`: Individual feature development
   - `bugfix/bug-name`: Bug fix branches

2. **Pull Request Process**
   - Create feature/bugfix branch from `develop`
   - Make changes and write tests
   - Submit PR to `develop` branch
   - Code review and approval
   - Merge to `develop`

3. **Release Process**
   - Final testing in `develop`
   - Create release branch `release/vX.Y.Z`
   - Fix any release-specific issues
   - Merge to `main` with version tag
   - Deploy to production

## Testing Guidelines

### Frontend Tests

- Unit tests for components using React Testing Library
- Integration tests for key user flows
- Accessibility testing with axe-core

### Backend Tests

- Unit tests for utility functions
- Integration tests for database operations
- API endpoint tests using pytest

## Documentation Standards

- Update relevant README files when adding new features
- Document all functions with docstrings
- Keep API documentation current
- Include examples for complex functionality

## Code Style Guidelines

### Frontend

- Follow ESLint configuration
- Use TypeScript for type safety
- Implement component-based architecture
- Follow shadcn/ui patterns for consistency

### Backend

- Follow PEP 8 style guide
- Use type hints for all functions
- Write clear docstrings
- Keep functions focused and small