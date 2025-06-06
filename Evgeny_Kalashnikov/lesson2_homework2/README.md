# Amazon Reviews User Board Simulator

This project simulates a user board discussion based on Amazon product reviews. It analyzes product reviews, creates user profiles, and orchestrates discussions about product features and improvements.

## Components

### 1. Data Loading and Management
- `ReviewsLoader` class in `load_reviews.py`
  - Loads Amazon product reviews from CSV file
  - Provides methods to access reviews by product and user
  - Includes functionality to find products with specific review counts
  - Filters unique reviews and manages token limits

### 2. Review Analysis
- `ReviewAnalyzer` class in `userboard_agents.py`
  - Analyzes product reviews to identify key features and issues
  - Generates comprehensive product summaries
  - Identifies top issues and concerns from reviews

### 3. Solution Generation
- `SolutionAnalyzer` class in `userboard_agents.py`
  - Proposes solutions for identified product issues
  - Generates concise, actionable improvement suggestions
  - Focuses on practical and implementable solutions

### 4. User Profile Creation
- `UserPersonaAnalyzer` class in `userboard_agents.py`
  - Analyzes user reviews to create detailed user profiles
  - Identifies user preferences, review styles, and focus areas
  - Creates authentic user representations based on review patterns

### 5. User Simulation
- `User` class in `userboard_agents.py`
  - Simulates user behavior in discussions
  - Responds to questions about product features
  - Reacts to other users' responses
  - Maintains consistent personality based on review history

### 6. Discussion Orchestration
- `userboard.py` main script
  - Selects random product with 50-100 reviews
  - Creates user profiles from product reviewers
  - Generates solutions for identified issues
  - Orchestrates discussions between users
  - Creates formatted summary of the discussion

## Process Flow

1. **Data Selection**
   - Randomly selects a product with 50-100 reviews
   - Retrieves all reviews for the selected product
   - Identifies users who reviewed the product

2. **Analysis Phase**
   - Analyzes product reviews to identify key features and issues
   - Creates user profiles based on review history
   - Generates solutions for identified issues

3. **Discussion Phase**
   - Each user provides initial response to proposed solutions
   - Users can react to other users' responses
   - Reactions form chains of up to 3 responses
   - Discussion continues until natural conclusion

4. **Summary Generation**
   - Creates timestamped summary file
   - Includes product information and analysis
   - Documents user profiles and discussion
   - Formats output for easy reading

## Output Format

The generated summary file includes:
- Product information and review count
- Product summary and analysis
- List of top issues
- User profiles
- Structured discussion with:
  - Initial responses
  - Reaction chains
  - Clear attribution of responses

## Usage

1. Ensure the Amazon reviews CSV file is available
2. Run the main script:
   ```bash
   python userboard.py
   ```
3. Review the generated summary file (format: `summary_YYYYMMDD_HHMMSS.txt`)

## Requirements

- Python 3.x
- pandas
- asyncio
- datetime
- pathlib
- random 