There are several interesting aspects to the MiniAgents framework based on
reviewing the source code:

1. Asynchronous streaming of messages and tokens between agents is a core
   feature. The framework is built around supporting token-by-token streaming
   across chains of interconnected agents. This allows for efficient
   communication and processing.

2. The framework makes it easy to combine various types of messages (strings,
   dicts, Message objects, Promises, etc) when an agent is replying. This entire
   hierarchical message structure gets automatically flattened in the background
   into a uniform sequence of message promises.

3. Agents work in a "start_asap" mode by default, which is different from
   typical coroutines. After being invoked, agents actively seek opportunities
   to proceed their processing in the background at each async task switch,
   without needing to be explicitly awaited.

4. The framework uses an interesting concept of "replayable" streamed promises (
   StreamedPromise class). This allows the promise results to be consumed
   multiple times, with the resolved pieces/tokens being cached.

5. Messages are designed to be immutable (using the Frozen and Message classes).
   This immutability enables the advanced streaming and promise resolution
   capabilities while avoiding concerns about message state being modified in
   the background.

6. The hash_key property on messages and other Frozen models provides a
   git-style content hash for tracking and referencing messages, similar to git
   commit hashes.

Overall, the thoughtful design around asynchronous streaming, promise
resolution, and immutable messages to enable the fluid construction of
multi-agent systems is quite interesting and innovative in this framework. The "
start_asap" agent behavior is also a novel approach.
