import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterable

# Import common A2A types and components
from A2A.server.task_manager import InMemoryTaskManager
from A2A.types import (
    Task, TaskStatus, TaskState, Message, TextPart, 
    DataPart, Artifact, SendTaskResponse, SendTaskStreamingResponse, TaskStatusUpdateEvent,
    JSONRPCResponse, JSONRPCError
)

# Import the query_agent function from the direct_agent module
from .direct_agent import query_agent

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AppointmentAgentTaskManager(InMemoryTaskManager):
    """
    Task manager per l'Appointment Agent che utilizza OpenRouter invece di Google ADK.
    Gestisce l'esecuzione dei task, l'orchestrazione delle richieste e la conversione 
    dei risultati in formato A2A.
    """
    
    def __init__(self, agent, runner, session_service, app_name, user_id):
        """
        Initializes the AppointmentAgentTaskManager.
        
        Args:
            agent: L'istanza dell'agente (conservato per retrocompatibilità)
            runner: Runner per il modello (conservato per retrocompatibilità)
            session_service: Servizio per la gestione delle sessioni
            app_name: Nome dell'applicazione
            user_id: ID utente default
        """
        self.agent = agent
        self.runner = runner
        self.session_service = session_service
        self.app_name = app_name
        self.user_id = user_id
        
        # Dizionario per memorizzare i task attivi
        self.tasks: Dict[str, Task] = {}
        
    async def process_task(self, task: Task) -> Task:
        """
        Elabora un task inviando la query all'agente direct_agent.
        
        Args:
            task: Il task A2A da processare
            
        Returns:
            Il task aggiornato con lo stato e il risultato
        """
        try:
            # Estrae il messaggio dell'utente dal task
            if not task.history:
                raise ValueError("Task history is empty")
            
            user_message = ""
            for message in task.history:
                if message.role == "user":
                    for part in message.parts:
                        if hasattr(part, "text") and part.text:
                            user_message = part.text
                            break
            
            if not user_message:
                raise ValueError("No user message found in task history")
            
            logger.info(f"QUERY: {user_message}")
            
            # Verifica se esiste una sessione per questo task o ne crea una nuova
            if task.sessionId:
                logger.info(f"Session found with ID: {task.sessionId}")
                session_data = {"session_id": task.sessionId}
            else:
                # Generate a random session ID if none is provided
                import uuid
                session_id = str(uuid.uuid4())
                logger.info(f"Session not found. Creating a new default session with ID: {session_id}")
                task.sessionId = session_id
                session_data = {"session_id": session_id}
            
            # Chiama la funzione query_agent dal direct_agent.py
            result = await query_agent(user_message, session_data)
            
            # Converti il risultato in un messaggio A2A
            agent_response = result.get("agent_response", "")
            
            # Crea un nuovo messaggio per l'agente
            agent_message = Message(
                role="agent",
                parts=[TextPart(type="text", text=agent_response)]
            )
            
            # Crea un nuovo artifact per i dati strutturati
            artifacts = [
                Artifact(
                    parts=[DataPart(type="data", data=result)],
                    index=0
                )
            ]
            
            # Aggiorna il task con il nuovo stato
            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message=agent_message,
                timestamp=None  # Sarà compilato automaticamente
            )
            
            # Aggiorna gli artifacts del task
            task.artifacts = artifacts
            
            # Aggiungi il messaggio dell'agente alla cronologia
            task.history.append(agent_message)
            
            # Registra il risultato per debug
            logger.info(f"RESULT: {result}")
            
            return task
            
        except Exception as e:
            # In caso di errore, restituisci un messaggio di errore
            logger.error(f"Error processing task: {str(e)}", exc_info=True)
            
            # Crea un messaggio di errore
            error_message = Message(
                role="agent",
                parts=[TextPart(type="text", text=f"An error occurred: {str(e)}")]
            )
            
            # Aggiorna lo stato del task
            task.status = TaskStatus(
                state=TaskState.COMPLETED,  # Anche in caso di errore, il task è "completato"
                message=error_message,
                timestamp=None  # Sarà compilato automaticamente
            )
            
            # Aggiungi il messaggio di errore alla cronologia
            task.history.append(error_message)
            
            return task
            
    async def upsert_task(self, request) -> Task:
        """
        Crea o aggiorna un task.
        
        Args:
            request: Richiesta di creazione/aggiornamento task
            
        Returns:
            Il task creato o aggiornato
        """
        # Se non è fornito un ID task, creane uno nuovo
        if not hasattr(request, 'id') or not request.id:
            import uuid
            request.id = str(uuid.uuid4())
            
        # Se non è fornito un ID sessione, creane uno nuovo
        if not hasattr(request, 'sessionId') or not request.sessionId:
            import uuid
            request.sessionId = str(uuid.uuid4())
        
        # Inizializza il task con le informazioni dalla richiesta
        task = Task(
            id=request.id,
            sessionId=request.sessionId,
            status=TaskStatus(
                state=TaskState.PENDING,
                message=None,
                timestamp=None
            ),
            history=request.history if hasattr(request, 'history') and request.history else [],
            artifacts=[],
            metadata=None
        )
        
        # Memorizza il task
        self.tasks[request.id] = task
        
        # Se il task è di tipo "send", elaboralo immediatamente
        if not hasattr(request, 'parent_task_id') or not request.parent_task_id:
            # Aggiorna lo stato del task a IN_PROGRESS
            task.status.state = TaskState.IN_PROGRESS
            
            # Elabora il task in modo asincrono
            asyncio.create_task(self._process_and_update_task(task))
        
        return task
    
    async def _process_and_update_task(self, task: Task) -> None:
        """
        Elabora un task e aggiorna il risultato.
        
        Args:
            task: Il task da elaborare
        """
        # Elabora il task
        updated_task = await self.process_task(task)
        
        # Aggiorna il task memorizzato
        self.tasks[task.id] = updated_task
        
    async def get_task(self, id: str) -> Optional[Task]:
        """
        Ottiene un task dal suo ID.
        
        Args:
            id: ID del task
            
        Returns:
            Il task se trovato, altrimenti None
        """
        return self.tasks.get(id)

    async def on_send_task(self, request) -> SendTaskResponse:
        """
        Gestisce l'invio di un task non streaming.
        
        Args:
            request: La richiesta di invio task
            
        Returns:
            La risposta con i risultati del task
        """
        try:
            # Estrai il messaggio dalla richiesta
            message = request.params.message
            session_id = request.params.sessionId
            task_id = request.params.id
            
            # Crea/aggiorna il task
            task = Task(
                id=task_id,
                sessionId=session_id,
                status=TaskStatus(
                    state=TaskState.IN_PROGRESS,
                    message=None,
                    timestamp=None
                ),
                history=[message],
                artifacts=[]
            )
            
            # Memorizza il task
            self.tasks[task_id] = task
            
            # Processa il task in modo asincrono
            updated_task = await self.process_task(task)
            
            # Restituisci la risposta
            return SendTaskResponse(
                id=request.id,
                result=updated_task
            )
            
        except Exception as e:
            logger.error(f"Error processing send task: {str(e)}", exc_info=True)
            
            # Crea un errore JSON-RPC
            error = JSONRPCError(
                code=-32603,  # Codice per errore interno
                message=f"Error processing send task: {str(e)}"
            )
            
            # Restituisci la risposta con l'errore
            return SendTaskResponse(
                id=request.id,
                error=error
            )
    
    async def on_send_task_subscribe(self, request) -> Union[AsyncIterable[SendTaskStreamingResponse], JSONRPCResponse]:
        """
        Gestisce l'invio di un task streaming.
        
        Args:
            request: La richiesta di invio task streaming
            
        Returns:
            Un generatore asincrono di risposte streaming o una risposta di errore
        """
        try:
            # Estrai il messaggio dalla richiesta
            message = request.params.message
            session_id = request.params.sessionId
            task_id = request.params.id
            
            # Crea/aggiorna il task
            task = Task(
                id=task_id,
                sessionId=session_id,
                status=TaskStatus(
                    state=TaskState.IN_PROGRESS,
                    message=None,
                    timestamp=None
                ),
                history=[message],
                artifacts=[]
            )
            
            # Memorizza il task
            self.tasks[task_id] = task
            
            # In questa implementazione, non supportiamo veramente lo streaming,
            # quindi processiamo il task normalmente e restituiamo un singolo evento
            async def stream_response():
                try:
                    # Processa il task
                    updated_task = await self.process_task(task)
                    
                    # Crea un evento di aggiornamento dello stato del task
                    status_event = TaskStatusUpdateEvent(
                        id=updated_task.id,
                        status=updated_task.status,
                        final=True
                    )
                    
                    # Restituisci una risposta streaming con l'evento di stato
                    yield SendTaskStreamingResponse(
                        id=request.id,
                        result=status_event
                    )
                    
                except Exception as e:
                    logger.error(f"Error in streaming task: {str(e)}", exc_info=True)
                    
                    # Crea un errore JSON-RPC
                    error = JSONRPCError(
                        code=-32603,  # Codice per errore interno
                        message=f"Error in streaming task: {str(e)}"
                    )
                    
                    # Restituisci una risposta con l'errore
                    yield SendTaskStreamingResponse(
                        id=request.id,
                        error=error
                    )
            
            # Restituisci il generatore asincrono
            return stream_response()
            
        except Exception as e:
            logger.error(f"Error setting up streaming task: {str(e)}", exc_info=True)
            
            # Crea un errore JSON-RPC
            error = JSONRPCError(
                code=-32603,  # Codice per errore interno
                message=f"Error setting up streaming task: {str(e)}"
            )
            
            # Restituisci una risposta immediata con l'errore
            return JSONRPCResponse(
                id=request.id,
                error=error
            ) 