# System Patterns

## Architecture Overview

The system follows a modular pipeline architecture with four main components:

```
Review Scraping → Persona Generation → Group Discussion → Insights Generation
```

Each component is designed to operate independently while maintaining data consistency throughout the pipeline.

## Core Design Patterns

### 1. Pipeline Pattern
The system implements a sequential processing pipeline where each stage:
- Takes input from the previous stage
- Performs specific transformations
- Produces output for the next stage
- Stores intermediate results for audit and debugging

### 2. Factory Pattern (for Persona Generation)
The system dynamically creates different persona types based on review analysis:
- Each persona is created with a unique set of attributes
- Personas are instantiated with appropriate behavioral characteristics
- The factory ensures diversity among generated personas

### 3. Agent-Based Simulation
The group discussion component uses an agent-based approach:
- Each agent (persona) has its own state, knowledge, and behavior rules
- Agents interact with each other based on predefined rules
- The system orchestrates turn-taking and discussion flow
- Agents can respond to each other's messages and build on previous points

### 4. Repository Pattern (for Data Storage)
All intermediate and final outputs are stored in a consistent format:
- JSON for structured data (reviews, personas, discussions)
- Text files for unstructured outputs (summaries, recommendations)
- Timestamped files for audit trail and versioning

## Key Components

### 1. Review Scraper (`scraper.py`)
- Manages web interactions with e-commerce sites
- Handles different HTML structures using site-specific extractors
- Processes and normalizes review data

### 2. Persona Generator (`persona_generator.py`)
- Analyzes review text to identify demographic patterns
- Extracts key needs, preferences, and pain points
- Generates coherent persona profiles with consistent attributes

### 3. Group Discussion Engine (`group_discussion.py`)
- Simulates multi-turn conversations between personas
- Manages conversation flow and turn-taking
- Facilitates information exchange between agents
- Creates realistic discussion dynamics

### 4. Insight Generators
- Discussion Summarizer (`summarizer.py`): Extracts key points from discussions
- Product Improvements Generator (`product_improvements.py`): Generates actionable recommendations

## Error Handling Strategy

1. **Graceful Degradation**: Each component handles failures without crashing the entire pipeline
2. **Robust Logging**: Detailed logging of actions, outcomes, and errors
3. **Fallback Mechanisms**: Alternative strategies when primary approaches fail
4. **Input Validation**: Checking and cleaning inputs at each stage

## Extension Points

The system is designed for extension in the following areas:

1. **New Scrapers**: Add support for additional e-commerce platforms
2. **Product Categories**: Extend to handle different product types
3. **Discussion Types**: Add new discussion formats and questions
4. **Output Formats**: Generate additional types of insights and recommendations 