# Drawi Agent Project Breakdown

## Project Overview
Drawi Agent is a Python-based project that implements a reactive agent system using langgraph. The agent is designed to execute tasks through a structured workflow, utilizing various tools and maintaining state throughout its execution.

### Checkpoint Files
The `.langgraph_checkpoint.*.pckl` files are automatically created by langgraph during the agent's execution. These files serve as state checkpoints that:
- Store the agent's conversation history and state
- Allow the agent to maintain context across multiple steps
- Enable recovery of agent state if needed
- Are automatically managed by the langgraph framework

## Core Components

### 1. Agent Configuration (`configuration.py`)
- Handles the agent's configuration settings
- Defines parameters and settings that control the agent's behavior
- Key focus for customizing agent capabilities and limitations

### 2. Workflow Graph (`graph.py`)
- Implements the agent's decision-making workflow using langgraph
- Defines the flow of operations and decision points
- **Development Focus**: This is a critical file for understanding and modifying agent behavior

### 3. Prompt Management (`prompts.py`)
- Contains templates for agent prompts
- Defines how the agent communicates and processes instructions
- **Development Focus**: Modify this to improve agent understanding and responses

### 4. State Management (`state.py`)
- Handles the agent's internal state
- Tracks progress and maintains context during task execution
- Important for understanding how the agent maintains context

### 5. Tools Implementation (`tools.py`)
- Defines the tools and actions available to the agent
- Implements concrete functionality the agent can use
- **Development Focus**: Add new capabilities here

### 6. Utility Functions (`utils.py`)
- Helper functions and shared utilities
- Common operations used across the project

## Testing Structure

### Unit Tests
- Located in `tests/unit_tests/`
- Tests individual components in isolation
- Focus on configuration testing (`test_configuration.py`)

### Integration Tests
- Located in `tests/integration_tests/`
- Tests complete workflows and component interaction
- Includes graph testing (`test_graph.py`)

## Development Focus Areas

When developing the agent, focus on these key areas:

1. **Tool Development**
   - Add new tools in `tools.py`
   - Implement concrete actions the agent can perform
   - Ensure proper error handling and validation

2. **Workflow Enhancement**
   - Modify `graph.py` to improve decision-making flow
   - Add new states or transitions as needed
   - Optimize the execution path

3. **Prompt Engineering**
   - Refine prompts in `prompts.py`
   - Improve instruction clarity and context handling
   - Add new prompt templates for new capabilities

4. **State Management**
   - Enhance state tracking in `state.py`
   - Add new state variables as needed
   - Improve context preservation

## Getting Started

1. Review the `.env.example` file to set up necessary environment variables
2. Examine the `langgraph.json` for graph configuration
3. Use the Makefile for common development tasks

## UI Component
The project includes a studio UI (see `static/studio_ui.png`) which provides a visual interface for interacting with the agent.

## Best Practices

1. Always add tests for new functionality
2. Keep the graph structure clean and well-documented
3. Maintain consistent error handling
4. Document new tools and capabilities
5. Follow the existing project structure when adding new features

## Development Workflow

1. Start with understanding the graph structure in `graph.py`
2. Implement new tools in `tools.py`
3. Add corresponding prompts in `prompts.py`
4. Update state handling in `state.py` if needed
5. Add tests for new functionality
6. Update configuration as necessary

This breakdown provides a foundation for understanding and developing the Drawi Agent project. Focus on the core components while maintaining the project's structure and testing practices.