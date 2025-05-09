Orchestrator response structure:

jsonrpc='2.0' 
id= user id
agent = agent that have generated the response
result=Task(
    id= task id 
    sessionId= session id 
    status=TaskStatus(
        state= COMPLETE, INPUT REQUIREDE, ... 
        message=Message(
            role= agent or user, who send this message, 
            parts=[TextPart(
                type='text', 
                text= text response, 
                metadata = eventauly some extra metadata in the part
                )
            ], 
            metadata = eventauly some extra metadata in the message
        ), 
        timestamp = time in which this task is crated 
        artifacts = return of the task 
        history = array of message exchange between user and agent during the task, 
        metadata = eventauly some extra metadata for the Task
    )
) 

