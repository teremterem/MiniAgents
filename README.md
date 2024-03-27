# MiniAgents

TODO Oleksandr: write proper readme

## Classes

### StreamedPromise

### Node

### PromisePath(relation_name) ?

- Should the same relation type support multiple (more than two) edges ?
- Should those edges be both, directed and undirected ?

The answer to both questions is probably no - I need to more or less closely adapt this graph to the use case of
AgentForum. Each relation type should connect Nodes into a path where it is clear which Node is the source and which
is the target.
