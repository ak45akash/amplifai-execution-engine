"""
Memory utilities for AmplifAI Execution Engine v1
Provides memory storage and retrieval with future Pinecone integration
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
MEMORY_FILE_PATH = "memory/memory_store.jsonl"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "amplifai-memory")


def ensure_memory_directory():
    """Ensure the memory directory exists"""
    memory_dir = Path("memory")
    memory_dir.mkdir(exist_ok=True)


def is_pinecone_configured() -> bool:
    """Check if Pinecone is configured"""
    return bool(PINECONE_API_KEY and PINECONE_ENV)


def format_memory_entry(
    data: Dict[str, Any],
    memory_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a memory entry with consistent structure
    
    Args:
        data: Memory data to store
        memory_type: Type of memory (campaign, playbook, user, etc.)
        metadata: Additional metadata
        
    Returns:
        Formatted memory entry
    """
    memory_entry = {
        "id": f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{memory_type}",
        "timestamp": datetime.now().isoformat(),
        "memory_type": memory_type,
        "data": data,
        "metadata": metadata or {},
        "version": "1.0"
    }
    
    return memory_entry


def store_to_file(memory_entry: Dict[str, Any]) -> bool:
    """
    Store memory entry to local file
    
    Args:
        memory_entry: Memory entry to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_memory_directory()
        
        with open(MEMORY_FILE_PATH, "a") as f:
            f.write(json.dumps(memory_entry) + "\n")
        
        logger.info(f"Memory entry stored to file: {memory_entry['id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing memory to file: {e}")
        return False


def store_to_pinecone_stub(memory_entry: Dict[str, Any]) -> bool:
    """
    Stub for Pinecone vector storage (for future implementation)
    
    Args:
        memory_entry: Memory entry to store
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not is_pinecone_configured():
            logger.debug("Pinecone not configured, skipping vector storage")
            return False
        
        # Future implementation would:
        # 1. Generate embeddings for the memory data
        # 2. Store vectors in Pinecone with metadata
        # 3. Enable semantic search and retrieval
        
        logger.info(f"Would store to Pinecone: {memory_entry['id']}")
        logger.info(f"Pinecone Index: {PINECONE_INDEX_NAME}")
        logger.info(f"Memory Type: {memory_entry['memory_type']}")
        
        # Placeholder for actual Pinecone integration
        # import pinecone
        # pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        # index = pinecone.Index(PINECONE_INDEX_NAME)
        # 
        # # Generate embeddings (would use OpenAI or similar)
        # embeddings = generate_embeddings(memory_entry['data'])
        # 
        # # Upsert to Pinecone
        # index.upsert(vectors=[(memory_entry['id'], embeddings, memory_entry['metadata'])])
        
        return True
        
    except Exception as e:
        logger.error(f"Error storing memory to Pinecone: {e}")
        return False


def log_to_memory(
    data: Dict[str, Any],
    memory_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Main function to log data to memory storage
    
    Args:
        data: Data to store in memory
        memory_type: Type of memory entry
        metadata: Additional metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_memory_directory()
        
        memory_entry = format_memory_entry(data, memory_type, metadata)
        
        # Store to file
        file_success = store_to_file(memory_entry)
        
        # Try to store to Pinecone if configured
        pinecone_success = store_to_pinecone_stub(memory_entry)
        
        if file_success:
            logger.info(f"Memory logged successfully: {memory_entry['id']}")
            return True
        else:
            logger.error("Failed to store memory to file")
            return False
            
    except Exception as e:
        logger.error(f"Error in log_to_memory: {e}")
        return False


def retrieve_memories(
    memory_type: Optional[str] = None,
    limit: int = 10,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve memories from storage
    
    Args:
        memory_type: Filter by memory type
        limit: Maximum number of memories to return
        search_query: Search query (for future semantic search)
        
    Returns:
        List of memory entries
    """
    try:
        if not os.path.exists(MEMORY_FILE_PATH):
            logger.info("No memory file exists yet")
            return []
        
        memories = []
        
        with open(MEMORY_FILE_PATH, "r") as f:
            for line in f:
                try:
                    memory_entry = json.loads(line.strip())
                    
                    # Filter by memory type if specified
                    if memory_type and memory_entry.get("memory_type") != memory_type:
                        continue
                    
                    # TODO: Implement semantic search when Pinecone is integrated
                    if search_query:
                        logger.debug(f"Search query '{search_query}' not implemented yet")
                    
                    memories.append(memory_entry)
                    
                except json.JSONDecodeError:
                    continue
        
        # Sort by timestamp (most recent first) and limit
        memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return memories[:limit]
        
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        return []


def store_campaign_memory(
    campaign_id: str,
    budget: float,
    audience: List[str],
    creatives: List[str],
    status: str = "launched"
) -> bool:
    """
    Store campaign-specific memory
    
    Args:
        campaign_id: Campaign identifier
        budget: Campaign budget
        audience: Target audience segments
        creatives: Creative asset IDs
        status: Campaign status
        
    Returns:
        True if successful, False otherwise
    """
    campaign_data = {
        "campaign_id": campaign_id,
        "budget": budget,
        "audience": audience,
        "creatives": creatives,
        "status": status,
        "launch_timestamp": datetime.now().isoformat()
    }
    
    metadata = {
        "entity_type": "campaign",
        "entity_id": campaign_id,
        "status": status
    }
    
    return log_to_memory(campaign_data, "campaign", metadata)


def store_playbook_memory(
    playbook_id: str,
    playbook_name: str,
    content: Dict[str, Any],
    version: str = "1.0"
) -> bool:
    """
    Store playbook-specific memory
    
    Args:
        playbook_id: Playbook identifier
        playbook_name: Playbook name
        content: Playbook content
        version: Playbook version
        
    Returns:
        True if successful, False otherwise
    """
    playbook_data = {
        "playbook_id": playbook_id,
        "playbook_name": playbook_name,
        "content": content,
        "version": version,
        "upload_timestamp": datetime.now().isoformat()
    }
    
    metadata = {
        "entity_type": "playbook",
        "entity_id": playbook_id,
        "name": playbook_name,
        "version": version
    }
    
    return log_to_memory(playbook_data, "playbook", metadata)


def store_api_interaction_memory(
    endpoint: str,
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    session_id: Optional[str] = None
) -> bool:
    """
    Store API interaction memory
    
    Args:
        endpoint: API endpoint
        request_data: Request data
        response_data: Response data
        session_id: Session identifier
        
    Returns:
        True if successful, False otherwise
    """
    interaction_data = {
        "endpoint": endpoint,
        "request": request_data,
        "response": response_data,
        "session_id": session_id,
        "interaction_timestamp": datetime.now().isoformat()
    }
    
    metadata = {
        "entity_type": "api_interaction",
        "endpoint": endpoint,
        "session_id": session_id
    }
    
    return log_to_memory(interaction_data, "api_interaction", metadata)


def get_memory_stats() -> Dict[str, Any]:
    """
    Get basic statistics about stored memories
    
    Returns:
        Dictionary with memory statistics
    """
    try:
        if not os.path.exists(MEMORY_FILE_PATH):
            return {
                "total_memories": 0,
                "file_exists": False,
                "pinecone_configured": is_pinecone_configured()
            }
        
        with open(MEMORY_FILE_PATH, "r") as f:
            lines = f.readlines()
        
        total_memories = len(lines)
        
        # Count by memory type
        memory_types = {}
        for line in lines:
            try:
                memory_entry = json.loads(line.strip())
                memory_type = memory_entry.get("memory_type", "unknown")
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
            except json.JSONDecodeError:
                continue
        
        return {
            "total_memories": total_memories,
            "file_exists": True,
            "memory_types": memory_types,
            "file_path": MEMORY_FILE_PATH,
            "pinecone_configured": is_pinecone_configured()
        }
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return {"error": str(e)}


# Example usage and testing
if __name__ == "__main__":
    print("Testing memory utilities...")
    
    # Test basic memory storage
    test_data = {
        "test_key": "test_value",
        "timestamp": datetime.now().isoformat(),
        "message": "This is a test memory entry"
    }
    
    success = log_to_memory(test_data, "test", {"test": True})
    print(f"Basic memory storage test: {'✅ Success' if success else '❌ Failed'}")
    
    # Test campaign memory
    success = store_campaign_memory(
        campaign_id="test_campaign_001",
        budget=1000.0,
        audience=["test_audience"],
        creatives=["test_creative"],
        status="launched"
    )
    print(f"Campaign memory test: {'✅ Success' if success else '❌ Failed'}")
    
    # Test memory retrieval
    memories = retrieve_memories(memory_type="campaign", limit=5)
    print(f"Memory retrieval test: {'✅ Success' if len(memories) > 0 else '❌ Failed'}")
    
    # Test memory stats
    stats = get_memory_stats()
    print(f"Memory stats: {json.dumps(stats, indent=2)}")
    
    print(f"Pinecone configured: {'✅ Yes' if is_pinecone_configured() else '❌ No'}")
    print("Memory utilities testing completed!") 