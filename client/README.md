Orchestrator response structure:

jsonrpc='2.0' 
id='8f682c109dc14a908ebebfab765c63ea' 
result=Task(
    id='d4478c13-303a-4770-970a-f0f807e30d77', 
    sessionId='8dcc32f6-fd84-4cf1-a016-b3ebfecf9c81', 
    status=TaskStatus(
        state=<TaskState.COMPLETED: 'completed'>, 
        message=Message(
            role='agent', 
            parts=[TextPart(
                type='text', 
                text='Agent did not produce a final response.', 
                metadata=None
                )
            ], 
            metadata=None
        ), 
        timestamp=datetime.datetime(2025, 5, 9, 11, 29, 30, 529164) 
        artifacts=[], 
        history=[
            Message(
                role='user', 
                parts=[TextPart(
                    type='text', 
                    text='My sink is broken', 
                    metadata=None
                    )
                ], 
                metadata=None
            ), 
        ], 
        metadata=None
    )
) 
error=None
