import os
import uuid
import datetime

class ContextualMemory:
    def __init__(self, persist_path):
        self.use_chroma = False
        self.collection = None
        self.memory_store = [] # Fallback list of dicts
        
        try:
            import chromadb
            # Try initializing client to see if it works
            self.client = chromadb.PersistentClient(path=persist_path)
            self.collection = self.client.get_or_create_collection(
                name="conversation_history",
                metadata={"hnsw:space": "cosine"}
            )
            self.use_chroma = True
            print("ContextualMemory: ChromaDB loaded successfully.")
        except Exception as e:
            print(f"ContextualMemory Warning: ChromaDB failed to load ({e}). Using in-memory fallback.")
            self.use_chroma = False

    def add_memory(self, user_id, text, metadata=None):
        """
        Add a conversation snippet to vector memory.
        """
        if metadata is None:
            metadata = {}
        
        metadata['user_id'] = str(user_id)
        metadata['timestamp'] = str(datetime.datetime.now().isoformat())
        
        if self.use_chroma:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())]
            )
        else:
            # Fallback
            self.memory_store.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": metadata
            })

    def retrieve_context(self, user_id, query_text, n_results=3):
        """
        Retrieve relevant past interactions for a specific user.
        """
        if self.use_chroma:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"user_id": str(user_id)}
            )
            
            if not results['documents']:
                return []
                
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            
            context_items = []
            for doc, meta in zip(documents, metadatas):
                context_items.append({
                    "text": doc,
                    "metadata": meta
                })
            return context_items
        else:
            # Fallback: Simple keyword match or recent history
            # For simplicity, just return recent items for this user
            user_items = [item for item in self.memory_store if item['metadata']['user_id'] == str(user_id)]
            # Reverse to get most recent
            recent = user_items[-n_results:]
            return [{"text": i["text"], "metadata": i["metadata"]} for i in recent]

    def delete_user_memory(self, user_id):
        """
        Clear memory for a specific user.
        """
        if self.use_chroma:
            self.collection.delete(
                where={"user_id": str(user_id)}
            )
        else:
            self.memory_store = [item for item in self.memory_store if item['metadata']['user_id'] != str(user_id)]

# Singleton instance will be created in app init
