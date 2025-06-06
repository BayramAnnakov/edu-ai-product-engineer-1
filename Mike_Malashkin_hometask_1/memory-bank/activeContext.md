# Active Context

## Current Focus Areas

### 1. Error Handling & Robustness
Recent work has focused on improving error handling throughout the pipeline, particularly:
- Handling missing or invalid persona generation results
- Ensuring discussions can proceed even if some personas fail to generate
- Proper file path handling for output storage

### 2. Token Usage Optimization
We've implemented strategies to manage token usage more efficiently:
- Limiting the number of reviews processed (configurable, currently set to 100)
- Limiting text length for review analysis (configurable, currently set to 10,000 characters)
- Using targeted model selection based on task complexity

### 3. Universal Product Analysis
Making the system capable of analyzing different product types:
- Added configuration system for different product categories
- Flexible persona generation based on product type
- Adaptable discussion topics and recommendation formats

### 4. OpenAI API Migration (RESOLVED)
**Issue**: Updated from openai<1.0.0 to openai>=1.12.0
**Solution**: 
- Replaced `openai.ChatCompletion.create` with `openai.chat.completions.create` in all files:
  - group_discussion.py
  - summarizer.py  
  - agents/agent.py
  - product_improvements.py
  - persona_generator.py
- Updated syntax to include trailing commas
- Updated requirements.txt to `openai>=1.12.0`

### 5. File Path Issues (RESOLVED)
**Issue**: Discussion summary files had timestamp mismatches between generation and reading
**Solution**: 
- Updated analyze_sober_reviews.py to use glob pattern matching
- Added selection of most recent file when multiple matches found
- Added proper error handling for missing files

### 6. Telegram MCP Integration (NEW)
**Description**: Implemented comprehensive Telegram integration for receiving dialogs and sending messages
**Components**:
- `telegram_mcp_client.py` - Core Telegram Client API wrapper using pyrogram
- `run_telegram_mcp.py` - CLI interface for Telegram operations
- `test_telegram_mcp.py` - Test suite for Telegram functionality

**Available Functions**:
- `getDialogs` - retrieve list of all dialogs (chats, groups, channels)
- `getHistory` - get message history from specific chat
- `search` - search messages by text across chats
- `sendMessage` - send messages to specific chats

**Configuration**: Uses API_ID and API_HASH from environment variables or MCP config

### 7. Automated Bug Report & Improvement Telegram Delivery (NEW)
**Description**: Automatic delivery of generated bug reports and improvement proposals to Telegram
**Components**:
- `telegram_sender.py` - Automated sending of bug reports and improvements
- Modified `run_final_bugreports.py` - Now sends bug reports to @mmalashkin after generation
- Modified `run_final_improvements.py` - Now sends improvement proposals to @mmalashkin after generation
- `test_telegram_integration.py` - Test suite for the integration

**Workflow**:
1. Bug reports are generated via `run_final_bugreports.py`
2. Each bug report is automatically sent as separate Telegram message to @mmalashkin
3. Improvement proposals are generated via `run_final_improvements.py`  
4. Each improvement proposal is automatically sent as separate Telegram message to @mmalashkin
5. Messages are rate-limited (2 second delay between sends)
6. Content is truncated if longer than 4000 characters (Telegram limit)

**Benefits**:
- Real-time notification of new bug reports and improvements
- No manual intervention required
- Each item sent separately for better readability
- Automatic fallback to local storage if Telegram fails

## Known Issues

### 1. ChromeDriver Compatibility
Some users may experience issues with ChromeDriver version mismatches. The system should gracefully handle these and provide clear error messages.

### 2. OpenAI API Rate Limits
During bulk processing, we may hit rate limits. The system should implement retry logic with exponential backoff.

### 3. Persona Generation Failures
Sometimes persona generation fails due to insufficient review data or API issues. The system should continue processing with whatever personas are successfully generated.

### 4. Telegram Rate Limits
When sending multiple messages to Telegram, rate limiting may occur. Current implementation includes 2-second delays between messages.

## Development Guidelines

### Code Style
- No semicolons at end of lines (Python convention)
- Use commas after last element in objects and arrays
- OpenAI API calls should include error handling
- All commit messages in English, under 100 characters

### File Organization
- All output files stored in `output/` directory
- All documentation in `memory-bank/` directory  
- Agent-specific code in `agents/` directory
- Telegram integration files in root directory

### Error Handling Patterns
- Check for None before accessing attributes
- Use try/except blocks with specific error messages
- Provide fallback mechanisms for API failures
- Log errors with context information

### Telegram Integration Guidelines
- Always use async/await for Telegram operations
- Include rate limiting between message sends
- Truncate long content to fit Telegram limits
- Provide clear error messages for failures
- Test with `test_telegram_integration.py` before deployment

## Recent Changes

### Bug Fixes
- Fixed issue with `product_improvements.py` looking for files in the wrong directory
- Added proper handling of None values in `create_agent_from_persona`
- Updated OpenAI client initialization to match library version
- Added checks to avoid processing with empty agent lists

### Enhancements
- Increased review and text limits for more comprehensive analysis
- Added more detailed logging throughout the pipeline
- Improved error messages for troubleshooting
- Added Telegram notifications for real-time bug report delivery
- Enhanced user experience with visual feedback (emojis, formatting)
- Added pyrogram==2.0.106 to requirements.txt for Telegram Client API
- Implemented comprehensive Telegram MCP integration for data extraction

## Current Challenges

### 1. Chrome Driver Compatibility
There are some issues with ChromeDriver initialization, currently showing errors like:
```
Exec format error: '/Users/mike/.wdm/drivers/chromedriver/mac64/136.0.7103.92/chromedriver-mac-arm64/THIRD_PARTY_NOTICES.chromedriver'
```
The code includes fallback mechanisms but this should be investigated further.

### 2. OpenAI API Version Compatibility
The project was originally built for a newer OpenAI library but was adapted to work with version 0.28.1. Future updates should consider:
- Standardizing on a specific library version
- Updating code to be compatible with latest API patterns
- Adding version checking at startup

### 3. Token Limits
Even with current optimizations, some very large review sets can hit token limits. Additional strategies to consider:
- Implementing more aggressive summarization of reviews before persona generation
- Using embeddings for clustering similar reviews
- Adding dynamic batch sizing based on review length

### 4. Telegram Message Limits
- Telegram has a 4096 character limit per message
- Large bug reports or summaries are automatically truncated
- Consider splitting long messages or using file attachments for very long reports

### 5. Telegram MCP Authentication
- Requires valid API_ID and API_HASH from Telegram
- First run requires phone number verification and authentication
- Session files are stored locally for subsequent runs
- Proper error handling for authentication failures

## Next Steps

### Short-term Tasks
1. Fix ChromeDriver compatibility issues
2. Add proper unit tests for critical components
3. Further optimize token usage for very large review sets
4. Test Telegram integration thoroughly
5. Test Telegram MCP integration with real account

### Medium-term Goals
1. Add support for more e-commerce platforms
2. Implement caching to reduce API calls
3. Create a simple web interface for executing the pipeline
4. Add support for multiple Telegram channels (bugs vs features)
5. Integrate Telegram MCP data into the main analysis pipeline

### Long-term Vision
1. Support multiple languages for international product analysis
2. Add sentiment analysis for more targeted persona generation
3. Implement A/B testing for different discussion formats
4. Integration with project management tools (Jira, GitHub Issues) via MCP
5. Use Telegram data as additional source for customer insights and persona generation 