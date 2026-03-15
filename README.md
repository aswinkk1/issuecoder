# AutoResolver

AutoResolver is an autonomous AI agent designed to streamline your development workflow by automatically resolving Jira tickets. It acts as a bridge between your issue tracker (Jira) and your version control system (GitHub or Bitbucket), utilizing LLMs to read requirements, implement code changes (with a focus on C++ codebases), write unit tests, validate builds, and open Pull Requests.

## Features

- **Jira Webhook Integration**: Instantly triggers upon issue creation or updates.
- **Context Analyzer**: Pulls complete ticket details (summary, description, comments) from Jira to understand the objective.
- **Configurable LLM Backends**: Supports OpenAI API (`gpt-4`) or your own local LLMs (via Ollama, LM Studio, etc.) for code analysis and generation.
- **Autonomous C++ Code Editor**: Reads repository context and applies intelligent code modifications.
- **Unit Test Generator**: Automatically writes and injects C++ GTest unit tests covering new functions and modified branches.
- **Validation Pipeline**:
  - Automatically runs local commands (e.g., `make test` or linters) to verify changes.
  - Option to perform a post-modification AI semantic review to ensure logic aligns with the ticket requirements.
- **Multi-VCS PR Creator**: Supports automatic committing and Pull Request creation on both GitHub and Bitbucket.

## Architecture

1. **Webhook Receiver** (`app/api/webhooks.py`): FastAPI listener for Jira payloads.
2. **Issue Analyzer** (`app/services/analyzer.py`): Connects to the Jira API to extract the full scope and plans the resolution strategy.
3. **Core Agent Modifier** (`app/core/agent.py` & `app/core/file_editor.py`): Uses LangChain to search the codebase, formulate file patches, and safely edit files.
4. **Validation System** (`app/core/validator.py`): Executes shell validation commands and runs the AI review step.
5. **Unit Test Generator** (`app/core/test_generator.py`): Crafts corresponding GTest syntax for the branches touched by the AI.
6. **Git/PR Creator** (`app/services/git_service.py`): Uses PyGithub and Atlassian Python APIs to commit changes to a new branch and open a PR.

## Setup Instructions

### Prerequisites
- Python 3.10+
- A Jira Cloud account (with API token)
- GitHub Personal Access Token AND/OR Bitbucket App Password
- (Optional) OpenAI API Key, or a Local LLM running (e.g., via Ollama at `http://localhost:11434`)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd AutoResolver
   ```

2. Set up the virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Create a `.env` file in the root directory (copy from `.env.example` if available) and configure your variables:

```env
# LLM Provider Configuration ('openai' or 'local')
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
# LOCAL_LLM_URL=http://localhost:11434/v1
# LOCAL_LLM_MODEL=llama2

# Jira Configuration
JIRA_SERVER_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your_jira_email@example.com
JIRA_API_TOKEN=your_jira_api_token

# VCS Provider ('github' or 'bitbucket')
VCS_PROVIDER=github

# GitHub Configuration
GITHUB_TOKEN=your_github_token

# Bitbucket Configuration
BITBUCKET_URL=https://api.bitbucket.org
BITBUCKET_USER=your_bb_username
BITBUCKET_APP_PASSWORD=your_bb_app_pass
BITBUCKET_WORKSPACE=your_workspace_id
```

## Running the Server Locally

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. Expose your local port using a tool like [Ngrok](https://ngrok.com/):
   ```bash
   ngrok http 8000
   ```

3. Configure Jira Webhooks:
   - Go to Jira Settings > System > Webhooks.
   - Set the URL to `https://<YOUR_NGROK_URL>/webhooks/jira`.
   - Select the events you want to trigger the agent (e.g., `Issue: created`, `Issue: updated`).

4. Create a Jira ticket containing C++ coding instructions, and watch the agent create a PR!

## Modifying Validation Commands

By default, the `Validator` class looks to execute `make test` for C++ verification. If your project uses CMake, CTest, or a custom script, you can adjust the execution commands inside `app/core/validator.py`.
