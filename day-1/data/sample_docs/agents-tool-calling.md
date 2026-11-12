# Agents and Tool Calling

Tool calling lets an LLM ask your code to run a function, such as searching a database or calling an API. The model returns the tool name and arguments, your code runs the tool, and the result is sent back to the model.

An agent repeats this loop until the task is done. Agents need hard limits on steps and cost, because they can get stuck in loops.
